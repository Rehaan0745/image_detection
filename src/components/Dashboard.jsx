import React, { useState, useEffect } from 'react';
import { adminService, inspectService } from '../services/api';
import { Upload, ShieldAlert, Sparkles, Image as ImageIcon, CheckCircle, RefreshCw } from 'lucide-react';

const Dashboard = ({ onInspectionComplete }) => {
  const [medicines, setMedicines] = useState([]);
  const [selectedMedId, setSelectedMedId] = useState('');
  const [publicMedName, setPublicMedName] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);

  useEffect(() => {
    // Load medicines to help admins; public can still type medicine name
    const loadMedicines = async () => {
      try {
        const res = await adminService.getMedicines();
        setMedicines(res.data);
        if (res.data.length > 0) {
          setSelectedMedId(res.data[0].id);
        }
      } catch (err) {
        // ignore; public flow can still work via name
      }
    };
    loadMedicines();
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleInspect = async (e) => {
    e.preventDefault();
    if (!selectedFile || (!selectedMedId && !publicMedName.trim())) {
      setError('Please enter a medicine name or select a medicine and upload an image.');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      let res;
      if (selectedMedId) {
        res = await inspectService.compareCarton(selectedMedId, selectedFile);
      } else {
        res = await inspectService.compareCartonByName(publicMedName.trim(), selectedFile);
      }
      onInspectionComplete(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Verification request failed. Check backend console.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Container */}
      <div className="bg-white rounded-2xl border border-slate-200 custom-shadow p-8 space-y-8">
        <div className="border-b border-slate-100 pb-5">
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-pharmacy-600" /> Package Inspection System
          </h2>
          <p className="text-slate-500 text-xs mt-1 leading-relaxed">
            Upload an image of the carton containing all details to verify its authenticity against cached reference templates. The system will align coordinates, extract text, and check coloration details offline.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="text-red-700 text-xs font-semibold">{error}</div>
          </div>
        )}

        <form onSubmit={handleInspect} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Public medicine name input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Medicine Name
              </label>
              <input
                type="text"
                placeholder="Type medicine name (public) or choose from library"
                value={publicMedName}
                onChange={(e) => setPublicMedName(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-pharmacy-500 text-slate-700 bg-slate-50"
              />
            </div>

          </div>

          {/* Drag & Drop File Zone */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Upload Inspection Image
            </label>
            
            <div
              className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center min-h-[220px] ${
                dragActive ? 'border-pharmacy-500 bg-pharmacy-50/50' : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('inspect-file-input').click()}
            >
              <input
                type="file"
                id="inspect-file-input"
                className="hidden"
                accept="image/*"
                onChange={handleFileChange}
              />
              
              {previewUrl ? (
                <div className="space-y-4 w-full max-w-[200px]">
                  <div className="aspect-[4/3] rounded-lg overflow-hidden border border-slate-200 bg-white flex items-center justify-center p-2">
                    <img src={previewUrl} alt="Inspection Preview" className="object-contain max-h-full max-w-full" />
                  </div>
                  <p className="text-[10px] text-slate-400 truncate">{selectedFile.name}</p>
                  <span className="text-[10px] font-semibold text-pharmacy-600 bg-pharmacy-50 px-2 py-0.5 rounded">
                    Click or drag new to replace
                  </span>
                </div>
              ) : (
                <>
                  <Upload className="h-10 w-10 text-slate-400 mb-3 stroke-1" />
                  <p className="font-semibold text-slate-600 text-sm">Drag and drop your carton image here</p>
                  <p className="text-slate-400 text-xs mt-1">or click to browse local files (Supports JPG, PNG, WEBP)</p>
                </>
              )}
            </div>
          </div>

          {/* Compare Button */}
          <button
            type="submit"
            disabled={loading || !selectedFile || !publicMedName.trim()}
            className="w-full flex items-center justify-center gap-2 bg-pharmacy-600 hover:bg-pharmacy-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-sm disabled:bg-slate-200"
          >
            {loading ? (
              <>
                <RefreshCw className="h-5 w-5 animate-spin" /> Performing Automated Inspection...
              </>
            ) : (
              <>
                <CheckCircle className="h-5 w-5" /> Run Anti-Counterfeit Verification
              </>
            )}
          </button>
        </form>
      </div>

      {/* Modern Scanning Overlay Spinner */}
      {loading && (
        <div className="fixed inset-0 bg-slate-900/10 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-2xl flex flex-col items-center gap-4 text-center max-w-sm">
            <div className="relative flex items-center justify-center h-16 w-16">
              {/* Outer spin */}
              <div className="absolute inset-0 rounded-full border-4 border-slate-100 border-t-pharmacy-600 animate-spin"></div>
              <ImageIcon className="h-6 w-6 text-pharmacy-600" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-lg">Aligning & Verification</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Applying homography transformation to align query carton features, matching visual structures, and performing OCR text verification...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
