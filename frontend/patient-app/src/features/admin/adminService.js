import API from "../../api/apiClient";

export const getAdminDashboard = async () => {
  const response = await API.get("/admin/dashboard");
  return response.data;
};

export const listNurses = async () => {
  const response = await API.get("/admin/nurses");
  return response.data;
};

export const createNurse = async (name, age, email, password) => {
  const response = await API.post("/admin/nurses", {
    name,
    age: age ? Number(age) : null,
    email,
    password,
  });
  return response.data;
};

export const deactivateNurse = async (nurseId) => {
  const response = await API.delete(`/admin/nurses/${nurseId}`);
  return response.data;
};

export const listPatients = async () => {
  const response = await API.get("/admin/patients");
  return response.data;
};

export const createPatient = async (name, age, email, password) => {
  const response = await API.post("/admin/patients", {
    name,
    age: age ? Number(age) : null,
    email,
    password,
  });
  return response.data;
};

export const deactivatePatient = async (patientId) => {
  const response = await API.delete(`/admin/patients/${patientId}`);
  return response.data;
};

export const listAssignments = async () => {
  const response = await API.get("/admin/assignments");
  return response.data;
};

export const assignPatientToNurse = async (patientId, nurseId) => {
  const response = await API.patch(`/admin/patients/${patientId}/assign-nurse`, {
    nurse_id: nurseId,
  });
  return response.data;
};
