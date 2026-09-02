const BASE_URL = "http://127.0.0.1:8000";

// -----------------------------
// Register Patient
// -----------------------------
export async function registerPatient(name, age, email) {

  const response = await fetch(`${BASE_URL}/patient/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: name,
      age: Number(age),
      email: email
    })
  });

  const data = await response.json();

  if (!response.ok) {
    console.log("Backend error:", data);
    throw new Error("Registration failed");
  }

  return data;
}


// -----------------------------
// Submit Vitals
// -----------------------------
export async function submitVitals(patientId, weight, spo2) {

  const response = await fetch(`${BASE_URL}/vitals/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      patient_id: Number(patientId),
      weight_value: Number(weight),
      spo2_value: Number(spo2)
    })
  });

  const data = await response.json();

  if (!response.ok) {
    console.log("Vitals error:", data);
    throw new Error("Vitals submission failed");
  }

  return data;
}