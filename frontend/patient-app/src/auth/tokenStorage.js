import AsyncStorage from "@react-native-async-storage/async-storage";

const SESSION_KEY = "auth_session";

export const saveSession = async (session) => {
  await AsyncStorage.setItem(SESSION_KEY, JSON.stringify(session));
};

export const getSession = async () => {
  const raw = await AsyncStorage.getItem(SESSION_KEY);
  return raw ? JSON.parse(raw) : null;
};

export const getToken = async () => {
  const session = await getSession();
  return session ? session.token : null;
};

export const clearSession = async () => {
  await AsyncStorage.removeItem(SESSION_KEY);
};
