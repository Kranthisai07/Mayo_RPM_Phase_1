import { View, Text, StyleSheet } from "react-native";

export default function History() {

  return (
    <View style={styles.container}>

      <Text>Vitals History will appear here</Text>

    </View>
  );
}

const styles = StyleSheet.create({

  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center"
  }

});