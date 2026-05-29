import axios from 'axios';

// Use environment variable or default to relative path (handled by Vite proxy)
const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export const adminService = {
  getMedicines: () => apiClient.get('/admin/medicines'),
  // Create medicine with optional carton photo upload
  createMedicine: (name, dosage, manufacturer, file) => {
    const formData = new FormData();
    formData.append('name', name);
    if (dosage) formData.append('dosage', dosage);
    if (manufacturer) formData.append('manufacturer', manufacturer);
    if (file) formData.append('file', file);
    return apiClient.post('/admin/medicines', formData);
  },
  // Uploads reference image; viewName is optional and defaults to 'full'
  uploadReferenceView: (medicineId, file, viewName = 'full') => {
    const formData = new FormData();
    formData.append('view_name', viewName);
    formData.append('file', file);
    return apiClient.post(`/admin/medicines/${medicineId}/views`, formData);
  },
  deleteMedicine: (medicineId) => apiClient.delete(`/admin/medicines/${medicineId}`),
  deleteView: (viewId) => apiClient.delete(`/admin/views/${viewId}`),
  login: (email, password) => {
    const data = new URLSearchParams();
    data.append('email', email);
    data.append('password', password);
    return apiClient.post('/admin/login', data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  logout: () => apiClient.post('/admin/logout'),
  checkSession: () => apiClient.get('/admin/session'),
};

export const inspectService = {
  // Compare by medicine id and file
  compareCarton: (medicineId, file) => {
    const formData = new FormData();
    formData.append('medicine_id', medicineId);
    formData.append('file', file);
    return apiClient.post('/inspect/compare', formData);
  },
  // Compare by medicine name and file (public flow)
  compareCartonByName: (medicineName, file) => {
    const formData = new FormData();
    formData.append('medicine_name', medicineName);
    formData.append('file', file);
    return apiClient.post('/inspect/compare', formData);
  },
};

export default apiClient;
