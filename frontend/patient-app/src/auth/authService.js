import API from "../api/apiClient";
import { saveToken, removeToken } from "./tokenStorage";

export const registerUser = async (name, age, email, password) => {

  const response = await API.post("/auth/register", {
    name,
    age:Number(age),
    email,
    password
  });

  return response.data;
};

export const loginUser = async (email, password) => {

  const response = await API.post("/auth/login", {
    email,
    password
  });

  const token = response.data.access_token;

  await saveToken(token);

  return response.data;
};

export const logoutUser = async () => {
  await removeToken();
};