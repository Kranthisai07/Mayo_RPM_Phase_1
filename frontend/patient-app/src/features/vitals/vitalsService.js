import API from "../../api/apiClient";

export const submitVitals = async (weightValue, spo2Value) => {
  const response = await API.post("/vitals/", {
    weight_value: Number(weightValue),
    spo2_value: Number(spo2Value),
  });
  return response.data;
};

export const getMyHistory = async () => {
  const response = await API.get("/patient/history");
  return response.data;
};
