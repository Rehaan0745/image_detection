import React, { useRef, useEffect, useState } from 'react';

// Explanations format expected: [{id, box: [x,y,w,h], text, severity, category}]
const ImageWithOverlay = ({ src, explanations = [], onSelectDiff, hoveredId }) => {
  const imgRef = useRef(null);
  const containerRef = useRef(null);
  const [naturalSize, setNaturalSize] = useState({ w: 0, h: 0 });
  const [imgRect, setImgRect] = useState(null);
  const [containerRect, setContainerRect] = useState(null);

  useEffect(() => {
    const img = imgRef.current;
    const container = containerRef.current;
    if (!img || !container) return;

    const handleLoad = () => {
      setNaturalSize({ w: img.naturalWidth, h: img.naturalHeight });
      // compute rects
      setTimeout(() => {
        const iRect = img.getBoundingClientRect();
        const cRect = container.getBoundingClientRect();
        setImgRect(iRect);
        setContainerRect(cRect);
      }, 50);
    };

    handleLoad();
    window.addEventListener('resize', handleLoad);
    return () => window.removeEventListener('resize', handleLoad);
  }, [src]);

  const severityColor = (sev) => {
    const s = (sev || '').toLowerCase();
    if (s === 'critical') return { border: 'rgba(220,38,38,0.9)', bg: 'rgba(254,226,226,0.3)' };
    if (s === 'suspicious') return { border: 'rgba(245,158,11,0.9)', bg: 'rgba(255,247,237,0.35)' };
    return { border: 'rgba(234,179,8,0.9)', bg: 'rgba(255,250,231,0.35)' };
  };

  const computeStyle = (box) => {
    if (!imgRect || !containerRect || naturalSize.w === 0) return { display: 'none' };
    const scaleX = imgRect.width / naturalSize.w;
    const scaleY = imgRect.height / naturalSize.h;
    const offsetLeft = imgRect.left - containerRect.left;
    const offsetTop = imgRect.top - containerRect.top;

    const left = offsetLeft + box[0] * scaleX;
    const top = offsetTop + box[1] * scaleY;
    const width = Math.max(24, box[2] * scaleX);
    const height = Math.max(24, box[3] * scaleY);

    return {
      position: 'absolute',
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      height: `${height}px`,
      borderRadius: '9999px',
      transform: 'translate(0,0)',
      boxSizing: 'border-box',
      pointerEvents: 'auto',
      transition: 'transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease'
    };
  };

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <img ref={imgRef} src={src} alt="comparison" className="object-contain max-h-full max-w-full block mx-auto" />

      {explanations.map((item) => {
        if (!item.box || item.box.length < 4) return null;
        const box = item.box;
        const style = computeStyle(box);
        const colors = severityColor(item.severity);
        const isActive = hoveredId && item.id === hoveredId;

        return (
          <div
            key={item.id}
            onMouseEnter={() => onSelectDiff && onSelectDiff(item.id)}
            onMouseLeave={() => onSelectDiff && onSelectDiff(null)}
            onClick={() => onSelectDiff && onSelectDiff(item.id)}
            style={{
              ...style,
              border: `3px solid ${colors.border}`,
              background: isActive ? colors.bg : 'rgba(0,0,0,0.0)',
              boxShadow: isActive ? `0 0 0 2px ${colors.border}` : 'none',
              cursor: 'pointer'
            }}
          >
            <div style={{ position: 'absolute', left: 6, top: 6, zIndex: 30 }}>
              <span style={{
                fontSize: 11,
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: 8,
                background: colors.border,
                color: 'white',
                textTransform: 'uppercase'
              }}>{item.severity ? item.severity[0] : '!'}</span>
            </div>
            {(isActive && item.text) && (
              <div style={{
                position: 'absolute',
                left: '100%',
                top: 0,
                minWidth: 160,
                maxWidth: 260,
                marginLeft: 10,
                padding: 10,
                background: 'rgba(15,23,42,0.95)',
                color: 'white',
                fontSize: 12,
                lineHeight: 1.4,
                borderRadius: 12,
                boxShadow: '0 16px 40px rgba(15,23,42,0.18)',
                zIndex: 40
              }}>
                <strong style={{ display: 'block', marginBottom: 4, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#F8FAFC' }}>{item.category || 'Difference'}</strong>
                <span>{item.text}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ImageWithOverlay;
