import API from "../../api/apiClient";

export const getMyAlerts = async () => {
  const response = await API.get("/patient/alerts");
  return response.data;
};

export const getNurseAlerts = async () => {
  const response = await API.get("/nurse/alerts");
  return response.data;
};

export const getAdminAlerts = async () => {
  const response = await API.get("/admin/alerts");
  return response.data;
};

export const acknowledgeAlert = async (alertId) => {
  const response = await API.put(`/alerts/${alertId}/acknowledge`);
  return response.data;
};

export const resolveAlert = async (alertId) => {
  const response = await API.put(`/alerts/${alertId}/resolve`);
  return response.data;
};
