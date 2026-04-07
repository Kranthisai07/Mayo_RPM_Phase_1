import axios from "axios";
import { getToken } from "../auth/tokenStorage";

const API = axios.create({
  baseURL: "http://192.168.0.71:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

API.interceptors.request.use(async (config) => {

  const token = await getToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;

});

export default API;