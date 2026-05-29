import React, { useState } from 'react';
import ImageWithOverlay from './ImageWithOverlay';
import { Eye, HelpCircle, LayoutGrid, CheckCircle } from 'lucide-react';

const ComparisonViewer = ({ result, hoveredDiffId, onSelectDiff }) => {
  const [viewMode, setViewMode] = useState('side-by-side'); // 'side-by-side', 'warped'
  
  if (!result) return null;

  const {
    reference_url,
    annotated_query_url,
    warped_query_url,
    alignment_quality,
    ssim_score,
    color_match,
    ocr_match
  } = result;

  const serverUrl = 'http://localhost:8000';

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 custom-shadow space-y-6">
      {/* Verification Indicators Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="border border-slate-100 bg-slate-50/50 p-4 rounded-xl text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            SIFT Feature Alignment
          </span>
          <span className="text-xl font-bold text-slate-800">{alignment_quality}%</span>
          <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full font-medium inline-block">
            {alignment_quality > 70 ? 'Perfect homography' : 'Moderate skew'}
          </span>
        </div>

        {/* Metric 2 */}
        <div className="border border-slate-100 bg-slate-50/50 p-4 rounded-xl text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            SSIM Layout Match
          </span>
          <span className="text-xl font-bold text-slate-800">{ssim_score}%</span>
          <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full font-medium inline-block">
            {ssim_score > 85 ? 'Aligned structures' : 'Structural change'}
          </span>
        </div>

        {/* Metric 3 */}
        <div className="border border-slate-100 bg-slate-50/50 p-4 rounded-xl text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            CIE LAB Color Shade
          </span>
          <span className="text-xl font-bold text-slate-800">{color_match}%</span>
          <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full font-medium inline-block">
            {color_match > 90 ? 'Color matched' : 'Tint mismatch'}
          </span>
        </div>

        {/* Metric 4 */}
        <div className="border border-slate-100 bg-slate-50/50 p-4 rounded-xl text-center space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
            OCR Printed Text
          </span>
          <span className="text-xl font-bold text-slate-800">{ocr_match}%</span>
          <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full font-medium inline-block">
            {ocr_match > 95 ? 'Text verified' : 'Text mismatch'}
          </span>
        </div>
      </div>

      {/* View Switcher Controls */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <h3 className="font-bold text-slate-800 text-lg flex items-center gap-2">
          <LayoutGrid className="h-5 w-5 text-pharmacy-600" /> Image Inspection Panel
        </h3>
        <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
          <button
            onClick={() => setViewMode('side-by-side')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              viewMode === 'side-by-side'
                ? 'bg-white text-pharmacy-800 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Side-by-Side Comparison
          </button>
          <button
            onClick={() => setViewMode('warped')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              viewMode === 'warped'
                ? 'bg-white text-pharmacy-800 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Aligned Query Warped
          </button>
        </div>
      </div>

      {/* Image Panel Rendering */}
      {viewMode === 'side-by-side' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Authentic Standard View */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
              <span>Authentic Standard</span>
              <span className="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md">
                <CheckCircle className="h-3 w-3" /> Approved Reference
              </span>
            </div>
            <div className="border border-slate-200 rounded-xl overflow-hidden aspect-[4/3] bg-slate-50 flex items-center justify-center p-4 relative">
              <ImageWithOverlay
                src={`${serverUrl}${reference_url}`}
                explanations={result.explanations}
                onSelectDiff={onSelectDiff}
                hoveredId={hoveredDiffId}
              />
            </div>
          </div>

          {/* Inspected Carton Annotated View */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
              <span>Inspected Carton Analysis</span>
              <span className="flex items-center gap-1 text-red-600 bg-red-50 px-2 py-0.5 rounded-md">
                <Eye className="h-3 w-3" /> Anomalies Highlighted
              </span>
            </div>
            <div className="border border-slate-200 rounded-xl overflow-hidden aspect-[4/3] bg-slate-50 relative flex items-center justify-center p-4">
              <ImageWithOverlay
                src={`${serverUrl}${annotated_query_url}`}
                explanations={result.explanations}
                onSelectDiff={onSelectDiff}
                hoveredId={hoveredDiffId}
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
            <span>Aligned Query (Warped Homography Perspective)</span>
            <span className="text-slate-500">Perspective corrected automatically</span>
          </div>
          <div className="border border-slate-200 rounded-xl overflow-hidden aspect-[16/9] bg-slate-50 flex items-center justify-center p-4">
            <img
              src={`${serverUrl}${warped_query_url}`}
              alt="Warped Query Carton"
              className="object-contain max-h-full max-w-full"
            />
          </div>
        </div>
      )}

      {/* Legend Block */}
      <div className="bg-slate-50 border border-slate-150 p-4 rounded-xl flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center gap-1 font-semibold text-slate-600">
          <HelpCircle className="h-4 w-4 text-slate-400" />
          Color indicators for anomalies:
        </span>
        <div className="flex items-center gap-6 font-semibold">
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 bg-red-500 rounded-full border border-white custom-shadow"></span>
            Critical Mismatch
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 bg-amber-500 rounded-full border border-white custom-shadow"></span>
            Suspicious Variance
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 bg-yellow-400 rounded-full border border-white custom-shadow"></span>
            Minor Alteration
          </span>
        </div>
      </div>
    </div>
  );
};

export default ComparisonViewer;
