import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import ComparisonViewer from './components/ComparisonViewer';
import ResultPanel from './components/ResultPanel';
import AdminPanel from './components/AdminPanel';
import { ShieldCheck, Plus, RefreshCw, FolderLock, Play } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('inspect'); // 'inspect', 'admin'
  const [inspectionResult, setInspectionResult] = useState(null);
  const [hoveredDiffId, setHoveredDiffId] = useState(null);

  const handleInspectionComplete = (result) => {
    setInspectionResult(result);
  };

  const handleResetInspection = () => {
    setInspectionResult(null);
    setHoveredDiffId(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Header bar */}
      <header className="sticky top-0 bg-white/95 backdrop-blur border-b border-slate-200 z-40 px-6 py-4 custom-shadow">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Logo brand */}
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-pharmacy-600 flex items-center justify-center text-white custom-shadow">
              <ShieldCheck className="h-6 w-6 stroke-[2]" />
            </div>
            <div>
              <h1 className="font-extrabold text-slate-800 tracking-tight leading-none text-lg">PharmaInspect AI</h1>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-1 block">
                Offline Anti-Counterfeit Platform
              </span>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center bg-slate-100 p-1.5 rounded-xl border border-slate-200">
            <button
              onClick={() => {
                setActiveTab('inspect');
                handleResetInspection();
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'inspect'
                  ? 'bg-white text-pharmacy-800 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Play className="h-3.5 w-3.5" /> Inspection Dashboard
            </button>
            <button
              onClick={() => setActiveTab('admin')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'admin'
                  ? 'bg-white text-pharmacy-800 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <FolderLock className="h-3.5 w-3.5" /> Reference Library
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace content */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-6 py-8">
        {activeTab === 'inspect' ? (
          !inspectionResult ? (
            <Dashboard onInspectionComplete={handleInspectionComplete} />
          ) : (
            <div className="space-y-6">
              {/* Back to dashboard utility bar */}
              <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200 custom-shadow">
                <div>
                  <h3 className="font-bold text-slate-800 text-sm">Inspection Completed Successfully</h3>
                  <p className="text-[11px] text-slate-400">Review aligned packaging comparison report below.</p>
                </div>
                <button
                  onClick={handleResetInspection}
                  className="flex items-center gap-2 border border-slate-200 hover:border-slate-300 text-slate-600 hover:text-slate-800 font-semibold px-4 py-2 rounded-xl text-xs transition-colors bg-white hover:bg-slate-50"
                >
                  <RefreshCw className="h-3.5 w-3.5" /> Run Another Inspection
                </button>
              </div>

              {/* View Results layout split */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                  <ComparisonViewer result={inspectionResult} hoveredDiffId={hoveredDiffId} onSelectDiff={setHoveredDiffId} />
                </div>
                <div className="lg:col-span-1">
                  <ResultPanel result={inspectionResult} onHoverDiff={setHoveredDiffId} />
                </div>
              </div>
            </div>
          )
        ) : (
          <AdminPanel />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 px-6 text-center text-xs text-slate-400">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 font-medium">
          <span>PharmaInspect AI Anti-Counterfeit Packaging Verifier • Offline Mode</span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-full font-semibold border border-emerald-100">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span> Local Host API Active
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
