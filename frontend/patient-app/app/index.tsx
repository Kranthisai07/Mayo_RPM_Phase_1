import { useEffect, useState } from "react";
import { Redirect } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { getToken } from "../src/auth/tokenStorage";

export default function Index() {

  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {

    const checkToken = async () => {

      try {

        const storedToken = await getToken();

        setToken(storedToken);

      } catch (err) {

        console.log("Token error", err);

      } finally {

        setLoading(false);

      }

    };

    checkToken();

  }, []);

  if (loading) {

    return (
      <View
        style={{
          flex: 1,
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (token) {
    return <Redirect href="/(tabs)/vitals" />;
  }

  return <Redirect href="/(auth)/login" />;
}