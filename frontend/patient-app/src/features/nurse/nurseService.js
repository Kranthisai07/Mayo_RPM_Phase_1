import API from "../../api/apiClient";

export const getNurseDashboard = async () => {
  const response = await API.get("/nurse/dashboard");
  return response.data;
};

export const updateNurseStatus = async (isAvailable) => {
  const response = await API.patch("/nurse/status", {
    is_available: isAvailable,
  });
  return response.data;
};

export const getAssignedPatients = async () => {
  const response = await API.get("/nurse/patients");
  return response.data;
};

export const getAssignedPatientDetail = async (patientId) => {
  const response = await API.get(`/nurse/patients/${patientId}`);
  return response.data;
};

export const getPatientWeightAIStatus = async (patientId) => {
  const response = await API.get(`/vitals/weight-ai/${patientId}`);
  return response.data;
};
