import { useEffect, useState } from "react";
import { Redirect } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { getSession } from "../src/auth/tokenStorage";
import { getHomeRouteForRole } from "../src/auth/roleRoutes";

export default function Index() {

  const [session, setSession] = useState<{ role: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {

    const checkSession = async () => {

      try {

        const storedSession = await getSession();

        setSession(storedSession);

      } catch (err) {

        console.log("Session error", err);

      } finally {

        setLoading(false);

      }

    };

    checkSession();

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

  if (session) {
    return <Redirect href={getHomeRouteForRole(session.role) as any} />;
  }

  return <Redirect href="/(auth)/login" />;
}
