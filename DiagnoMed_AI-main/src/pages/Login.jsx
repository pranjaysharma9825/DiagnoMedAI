import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [role, setRole] = useState("doctor"); // default role
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // ✅ Doctor login
    if (role === "doctor" && form.username === "Admin" && form.password === "Adm$n@1234") {
      localStorage.setItem("authToken", "doctor-token");
      localStorage.setItem("role", "doctor");
      navigate("/dashboard");
    }
    // ✅ Patient login
    else if (role === "patient" && form.username === "Patient" && form.password === "Pat$ent@1234") {
      localStorage.setItem("authToken", "patient-token");
      localStorage.setItem("role", "patient");
      navigate("/patient-home");
    } else {
      setError("Invalid credentials. Please try again.");
    }
  };

  return (
    <div className="min-h-screen min-w-screen flex items-center justify-center bg-gradient-to-br !from-blue-200 to-gray-400">
      <div className="bg-white dark:bg-panel-dark shadow-lg rounded-2xl w-full max-w-md p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-blue-600 dark:text-accent-pink">
            DiagnoMed AI
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            AI-Powered Medical Diagnostics
          </p>
        </div>

        {/* Role Buttons */}
        <div className="flex justify-center gap-4 mb-4">
          <button
            type="button"
            onClick={() => setRole("doctor")}
            className={`px-4 py-2 rounded-lg font-medium ${
              role === "doctor"
                ? "!bg-blue-600 text-white"
                : "!bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Doctor Login
          </button>
          <button
            type="button"
            onClick={() => setRole("patient")}
            className={`px-4 py-2 rounded-lg font-medium ${
              role === "patient"
                ? "!bg-blue-600 text-white"
                : "!bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Patient Login
          </button>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={form.username}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border rounded-lg dark:bg-gray-200 dark:border-gray-600 dark:text-black focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={form.password}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border rounded-lg dark:bg-gray-200 dark:border-gray-600 dark:text-black focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="w-full !bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium"
          >
            Login as {role === "doctor" ? "Doctor" : "Patient"}
          </button>
        </form>

        {error && <p className="text-red-500 text-sm mt-3">{error}</p>}

        {/* Demo Info — show based on role */}
        {role === "doctor" ? (
          <div className="text-sm text-gray-500 dark:text-gray-400 mt-4 space-y-1">
            <p><strong>Doctor Demo:</strong></p>
            <p>Username: <code>Admin</code></p>
            <p>Password: <code>Adm$n@1234</code></p>
          </div>
        ) : (
          <div className="text-sm text-gray-500 dark:text-gray-400 mt-4 space-y-1">
            <p><strong>Patient Demo:</strong></p>
            <p>Username: <code>Patient</code></p>
            <p>Password: <code>Pat$ent@1234</code></p>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
          Secure medical diagnostics for healthcare professionals & patients
        </footer>
      </div>
    </div>
  );
}