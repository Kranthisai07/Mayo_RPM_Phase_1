import API from "../api/apiClient";
import { saveSession, clearSession } from "./tokenStorage";

export const registerUser = async (name, age, email, password) => {

  const response = await API.post("/auth/register", {
    name,
    age: Number(age),
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

  const { access_token, role, user_id, name, email: userEmail } = response.data;

  await saveSession({
    token: access_token,
    role,
    userId: user_id,
    name,
    email: userEmail,
  });

  return response.data;
};

export const logoutUser = async () => {
  await clearSession();
};
