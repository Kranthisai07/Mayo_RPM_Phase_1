import axios from "axios";
import { getToken } from "../auth/tokenStorage";

const API = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL || "http://10.0.0.139:8000",
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
