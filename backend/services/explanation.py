import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("explanation_engine")

def get_zone_description(box, img_width, img_height):
    """
    Translates pixel bounding box coordinates into natural language layout zones.
    Format of box: [x, y, w, h]
    """
    x, y, w, h = box
    center_x = x + w / 2.0
    center_y = y + h / 2.0
    
    # Define vertical partition
    if center_y < img_height * 0.25:
        vertical = "upper"
    elif center_y > img_height * 0.75:
        vertical = "lower"
    else:
        vertical = "central"
        
    # Define horizontal partition
    if center_x < img_width * 0.33:
        horizontal = "left"
    elif center_x > img_width * 0.66:
        horizontal = "right"
    else:
        horizontal = "middle"
        
    # Simplify layout names
    if vertical == "central" and horizontal == "middle":
        return "center area"
    elif vertical == "upper" and horizontal == "middle":
        return "upper-center panel"
    elif vertical == "lower" and horizontal == "middle":
        return "lower-center panel"
    else:
        return f"{vertical}-{horizontal} panel"

def generate_semantic_explanations(visual_diffs, ocr_diffs, img_width, img_height):
    """
    Aggregates visual, color, structural, and OCR differences
    and returns a structured list of semantic explanations.
    """
    explanations = []
    
    # 1. Process OCR Differences (often high priority as text carries specific meaning)
    for ocr in ocr_diffs:
        zone = get_zone_description(ocr["box"], img_width, img_height)
        sev = ocr["severity"]
        
        if ocr["type"] == "text_mismatch":
            text_desc = f"Manufacturing/regulatory detail mismatch in the {zone}: " \
                        f"Expected '{ocr['ref_text']}', but query packaging shows '{ocr['query_text']}'."
            explanations.append({
                "category": "OCR & Typography",
                "severity": sev,
                "text": text_desc,
                "box": ocr["box"]
            })
            
        elif ocr["type"] == "missing_text":
            text_desc = f"Mandatory security or regulatory text '{ocr['ref_text']}' is missing in the {zone}."
            explanations.append({
                "category": "OCR & Typography",
                "severity": sev,
                "text": text_desc,
                "box": ocr["box"]
            })
            
        elif ocr["type"] == "unexpected_text":
            text_desc = f"Unapproved text '{ocr['query_text']}' is printed in the {zone}."
            explanations.append({
                "category": "OCR & Typography",
                "severity": sev,
                "text": text_desc,
                "box": ocr["box"]
            })
            
        elif ocr["type"] == "font_size_mismatch":
            text_desc = f"Typography alignment/font size inconsistency: Text '{ocr['ref_text']}' in the {zone} appears altered in size."
            explanations.append({
                "category": "OCR & Typography",
                "severity": sev,
                "text": text_desc,
                "box": ocr["box"]
            })
            
        elif ocr["type"] == "text_spacing_mismatch":
            text_desc = f"Text spacing/kerning deviation: Characters in '{ocr['ref_text']}' ({zone}) show spacing changes compared to authentic packaging."
            explanations.append({
                "category": "OCR & Typography",
                "severity": sev,
                "text": text_desc,
                "box": ocr["box"]
            })

    # 2. Process Visual & Color Differences
    # Avoid overlapping visual diff boxes that are already explained by OCR
    for diff in visual_diffs:
        box = diff["box"]
        zone = get_zone_description(box, img_width, img_height)
        sev = diff["severity"]
        
        # Check if this box overlaps significantly with any already explained OCR box
        overlapping = False
        for ocr in ocr_diffs:
            # Simple bounding box overlap check
            ox, oy, ow, oh = ocr["box"]
            dx, dy, dw, dh = box
            
            x_overlap = max(0, min(ox + ow, dx + dw) - max(ox, dx))
            y_overlap = max(0, min(oy + oh, dy + dh) - max(oy, dy))
            if (x_overlap * y_overlap) > 0.4 * (dw * dh):
                overlapping = True
                break
                
        if overlapping:
            # We already explained this discrepancy via OCR text mismatch
            continue
            
        if diff["type"] == "color":
            color_desc = f"Color deviation in the {zone}: Packaging color hue or saturation differs " \
                         f"from the authentic standard (Delta E = {diff['mean_delta_e']:.1f})."
            explanations.append({
                "category": "Color & Print Quality",
                "severity": sev,
                "text": color_desc,
                "box": box
            })
        elif diff["type"] == "structural":
            struct_desc = f"Visual layout discrepancy in the {zone}: Branding logo, regulatory symbol, " \
                          f"or structural panel boundary appears missing or shifted."
            explanations.append({
                "category": "Structure & Layout",
                "severity": sev,
                "text": struct_desc,
                "box": box
            })
        else:  # mixed
            desc = f"Layout and coloration differences in the {zone}: Altered logo alignment, print quality, " \
                   f"or graphic seals detected."
            explanations.append({
                "category": "Structure & Layout",
                "severity": sev,
                "text": desc,
                "box": box
            })
            
    # Sort explanations by severity: critical first, then suspicious, then minor
    severity_order = {"critical": 0, "suspicious": 1, "minor": 2}
    explanations.sort(key=lambda x: severity_order.get(x["severity"], 3))
    
    return explanations
