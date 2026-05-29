import React, { useState, useEffect } from 'react';
import { adminService } from '../services/api';
import { Trash2, Plus, FileText, CheckCircle, AlertCircle, Image as ImageIcon, LogOut } from 'lucide-react';
import AdminLogin from './AdminLogin';

const AdminPanel = () => {
  const [medicines, setMedicines] = useState([]);
  const [newMedName, setNewMedName] = useState('');
  const [newMedDosage, setNewMedDosage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [newMedManufacturer, setNewMedManufacturer] = useState('');
  
  // Selection state for upload
  const [selectedFile, setSelectedFile] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await adminService.getMedicines();
      setMedicines(res.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch reference dataset from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      await loadData();
      try {
        const res = await adminService.checkSession();
        setIsAdmin(Boolean(res?.data?.is_admin));
      } catch (e) {
        setIsAdmin(false);
      }
    };
    init();
  }, []);

  const handleLoginSuccess = () => {
    console.log('Login successful callback triggered');
    setError(null);
    setSuccess(null);
    setIsAdmin(true);
    loadData();
  };

  const adminLogout = async () => {
    try {
      setError(null);
      setSuccess(null);
      await adminService.logout();
      setIsAdmin(false);
      setSuccess('Logged out successfully');
    } catch (e) {
      console.error('Logout error:', e);
    }
  };

  const handleAddMedicine = async (e) => {
    e.preventDefault();
    if (!newMedName.trim()) {
      setError('Please enter the medicine name.');
      return;
    }
    if (!selectedFile) {
      setError('Please upload the medicine carton image.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await adminService.createMedicine(newMedName.trim(), newMedDosage.trim(), newMedManufacturer.trim(), selectedFile);
      const medName = newMedName;
      setNewMedName('');
      setNewMedDosage('');
      setNewMedManufacturer('');
      setSelectedFile(null);
      const fileInput = document.getElementById('medicine-photo-input');
      if (fileInput) fileInput.value = '';
      setSuccess(`Medicine "${medName}" created successfully!`);
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create medicine.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMedicine = async (id, name) => {
    if (!confirm(`Are you sure you want to delete "${name}" and all its reference images?`)) return;
    try {
      setLoading(true);
      await adminService.deleteMedicine(id);
      setSuccess(`Medicine "${name}" deleted.`);
      loadData();
    } catch (err) {
      setError('Failed to delete medicine.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleDeleteView = async (viewId, viewName) => {
    if (!confirm(`Are you sure you want to delete this ${viewName} reference image?`)) return;
    try {
      setLoading(true);
      await adminService.deleteView(viewId);
      setSuccess('Reference carton image deleted.');
      loadData();
    } catch (err) {
      setError('Failed to delete carton image.');
    } finally {
      setLoading(false);
    }
  };

  // Show login screen if not authenticated
  if (!isAdmin) {
    return <AdminLogin onLoginSuccess={handleLoginSuccess} />;
  }

  // Show admin panel if authenticated
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header and Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 custom-shadow">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <ImageIcon className="h-6 w-6 text-pharmacy-600" />
              Authentic Reference Dataset Manager
            </h2>
            <p className="text-slate-500 mt-1 text-sm">
              Maintain approved authentic pharmaceutical carton templates, version views, and barcodes internally.
            </p>
          </div>
          <button
            onClick={adminLogout}
            className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-semibold transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="text-red-700 text-sm font-medium">{error}</div>
        </div>
      )}

      {success && (
        <div className="bg-emerald-50 border-l-4 border-emerald-500 p-4 rounded-lg flex items-start gap-3">
          <CheckCircle className="h-5 w-5 text-emerald-500 flex-shrink-0 mt-0.5" />
          <div className="text-emerald-700 text-sm font-medium">{success}</div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Management Tools */}
        <div className="space-y-8 lg:col-span-1">
          {/* Add Product Form */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 custom-shadow">
            <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Plus className="h-5 w-5 text-pharmacy-600" /> Add Medicine
            </h3>
            <form onSubmit={handleAddMedicine} className="space-y-4">
              <div className="grid grid-cols-1 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Paracetamol"
                    value={newMedName}
                    onChange={(e) => setNewMedName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-pharmacy-500 text-slate-700 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Manufacturer</label>
                  <input
                    type="text"
                    placeholder="e.g. Acme Pharma"
                    value={newMedManufacturer}
                    onChange={(e) => setNewMedManufacturer(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-pharmacy-500 text-slate-700 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Dosage</label>
                  <input
                    type="text"
                    placeholder="e.g. 500mg"
                    value={newMedDosage}
                    onChange={(e) => setNewMedDosage(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-pharmacy-500 text-slate-700 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Medicine Carton Photo</label>
                  <input
                    type="file"
                    id="medicine-photo-input"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 cursor-pointer"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-pharmacy-600 hover:bg-pharmacy-700 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors text-sm disabled:bg-slate-300"
              >
                <Plus className="h-4 w-4" />
                Create Medicine
              </button>
            </form>
          </div>

        </div>

        {/* Right Column: Reference Dataset Grid */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 custom-shadow min-h-[400px]">
            <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
              <FileText className="h-5 w-5 text-pharmacy-600" /> Reference Image Library ({medicines.length} Medicines)
            </h3>
            
            {medicines.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                <ImageIcon className="h-16 w-16 mb-4 stroke-1 text-slate-300" />
                <p className="font-semibold text-slate-500">No medicines in database.</p>
                <p className="text-xs text-slate-400 mt-1">Use the panel on the left to add a product directory.</p>
              </div>
            ) : (
              <div className="space-y-8">
                {medicines.map((med) => (
                  <div key={med.id} className="border border-slate-150 rounded-xl p-5 hover:border-slate-300 transition-colors bg-slate-50/50">
                    <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-4">
                      <div>
                        <h4 className="font-bold text-slate-800 text-lg">{med.name}{med.dosage ? ` ${med.dosage}` : ''}</h4>
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                          Created on {med.created_at.split('T')[0]}
                        </span>
                      </div>
                      <button
                        onClick={() => handleDeleteMedicine(med.id, med.name)}
                        className="text-red-500 hover:bg-red-50 p-2 rounded-lg transition-colors border border-transparent hover:border-red-100"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    {med.views.length === 0 ? (
                      <p className="text-xs text-slate-400 italic py-4">No carton reference images available for this medicine.</p>
                    ) : (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {med.views.map((view) => (
                          <div key={view.id} className="bg-white rounded-lg border border-slate-200 p-2 relative group hover:border-slate-300 transition-shadow hover:shadow-sm">
                            <div className="aspect-video bg-slate-100 rounded-md overflow-hidden flex items-center justify-center">
                              <img
                                src={`http://localhost:8000${view.image_path}`}
                                alt={`${med.name} ${view.view_name}`}
                                className="object-contain h-full w-full"
                              />
                            </div>
                            <div className="mt-2 flex items-center justify-between">
                              <span className="text-xs font-semibold text-slate-600 capitalize bg-slate-100 px-2 py-0.5 rounded">
                                {view.view_name}
                              </span>
                              <button
                                onClick={() => handleDeleteView(view.id, view.view_name)}
                                className="text-red-500 hover:text-red-700 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
