import React from 'react';
import { ShieldAlert, ShieldCheck, Download, AlertTriangle, FileCheck } from 'lucide-react';

const ResultPanel = ({ result, onHoverDiff }) => {
  if (!result) return null;

  const {
    authenticity_score,
    risk_level,
    explanations,
    pdf_report_url
  } = result;

  const serverUrl = 'http://localhost:8000';

  const riskConfigs = {
    low: {
      bgColor: 'bg-emerald-50',
      textColor: 'text-emerald-800',
      borderColor: 'border-emerald-200',
      icon: <ShieldCheck className="h-10 w-10 text-emerald-600" />,
      label: 'Low Risk (Authentic Packaging)',
      tag: 'Approved',
      tagColor: 'bg-emerald-100 text-emerald-800'
    },
    medium: {
      bgColor: 'bg-amber-50',
      textColor: 'text-amber-800',
      borderColor: 'border-amber-200',
      icon: <AlertTriangle className="h-10 w-10 text-amber-600" />,
      label: 'Medium Risk (Suspicious Packaging)',
      tag: 'Needs Review',
      tagColor: 'bg-amber-100 text-amber-800'
    },
    high: {
      bgColor: 'bg-red-50',
      textColor: 'text-red-800',
      borderColor: 'border-red-200',
      icon: <ShieldAlert className="h-10 w-10 text-red-600" />,
      label: 'High Risk (Potential Counterfeit)',
      tag: 'Rejected',
      tagColor: 'bg-red-100 text-red-800'
    }
  };

  const currentRisk = riskConfigs[risk_level.lower()] || riskConfigs.low;

  return (
    <div className="space-y-6">
      {/* Risk Summary Card */}
      <div className={`p-6 rounded-2xl border ${currentRisk.borderColor} ${currentRisk.bgColor} custom-shadow flex items-start gap-4`}>
        <div className="flex-shrink-0">{currentRisk.icon}</div>
        <div className="flex-grow space-y-1">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-lg text-slate-800">{currentRisk.label}</h3>
            <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wide ${currentRisk.tagColor}`}>
              {currentRisk.tag}
            </span>
          </div>
          <p className="text-slate-600 text-sm">
            Analysis score indicates visual match confidence. Download PDF report for full regulatory documentation.
          </p>
        </div>
      </div>

      {/* Authenticity Score Circle & Actions */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 custom-shadow flex items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          {/* Big Score circle */}
          <div className="relative h-20 w-20 flex items-center justify-center rounded-full bg-slate-50 border-4 border-slate-100">
            <span className="text-xl font-black text-slate-800">{authenticity_score}%</span>
            <span className="absolute text-[8px] font-bold text-slate-400 bottom-2 uppercase tracking-wide">MATCH</span>
          </div>
          <div>
            <h4 className="font-bold text-slate-800">Authenticity Score</h4>
            <p className="text-xs text-slate-500 mt-0.5">Calculated using structural shape mapping and print verification.</p>
          </div>
        </div>

        {pdf_report_url && (
          <a
            href={`${serverUrl}${pdf_report_url}`}
            download
            className="flex items-center gap-2 bg-pharmacy-600 hover:bg-pharmacy-700 text-white font-semibold py-2.5 px-4 rounded-xl transition-all shadow-sm text-sm"
          >
            <Download className="h-4 w-4" /> Download PDF Report
          </a>
        )}
      </div>

      {/* Semantic Difference Log */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 custom-shadow space-y-4">
        <h4 className="font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
          <FileCheck className="h-5 w-5 text-pharmacy-600" /> Explanation Log ({explanations.length} Anomalies)
        </h4>

        {explanations.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">
            No packaging variances detected. The package template matches the reference database perfectly.
          </div>
        ) : (
          <div className="space-y-3">
            {explanations.map((item, idx) => {
              const sevColors = {
                critical: 'bg-red-50 text-red-700 border-red-200',
                suspicious: 'bg-amber-50 text-amber-700 border-amber-200',
                minor: 'bg-yellow-50 text-yellow-700 border-yellow-200'
              };
              
              const sevLabelColors = {
                critical: 'bg-red-500 text-white',
                suspicious: 'bg-amber-500 text-white',
                minor: 'bg-yellow-400 text-slate-800'
              };

              const sev = item.severity.toLowerCase();

              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border ${sevColors[sev] || 'border-slate-200'} transition-all cursor-pointer flex gap-3 items-start hover:shadow-sm`}
                  onMouseEnter={() => onHoverDiff(item.id)}
                  onMouseLeave={() => onHoverDiff(null)}
                >
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${sevLabelColors[sev]} mt-0.5`}>
                    {sev}
                  </span>
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block">
                      {item.category}
                    </span>
                    <p className="text-slate-700 font-semibold text-sm leading-relaxed">{item.text}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

// Helper for lowercase conversion
String.prototype.lower = function() {
  return this.toLowerCase();
}

export default ResultPanel;
