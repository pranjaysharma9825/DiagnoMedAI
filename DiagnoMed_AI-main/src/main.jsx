import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./index.css";

import Navbar from "./components/Navbar"; // Doctor navbar
import PatientNavbar from "./components/PatientNavbar"; // Patient navbar

import Dashboard from "./pages/Dashboard";
import Patients from "./pages/Patients";
import Diagnostics from "./pages/Diagnostics";
import History from "./pages/History";
import NewDiagnosis from "./pages/NewDiagnosis";
import Profile from "./pages/Profile";
import Login from "./pages/Login";
import PatientProfile from "./pages/PatientProfile";
import PatientHome from "./pages/PatientHome";
import SymptomsPage from "./pages/SymptomsPage";
import UploadScansPage from "./pages/UploadScansPage";
import PatientHistoryPage from "./pages/PatientHistoryPage";
import DiagnosisFlow from "./pages/DiagnosisFlow";
import EvaluationDashboard from "./pages/EvaluationDashboard";

// Protected Route
function ProtectedRoute({ children, role }) {
  const authToken = localStorage.getItem("authToken");
  const userRole = localStorage.getItem("role");

  if (!authToken) {
    return <Navigate to="/" replace />;
  }

  if (role && userRole !== role) {
    return <Navigate to="/" replace />;
  }

  return children;
}

// Layout wrapper with correct navbar
function AppLayout() {
  const role = localStorage.getItem("role");

  return (
    <div className="min-h-screen min-w-screen bg-gray-50 flex flex-col">
      {/* Show navbar based on role */}
      {role === "doctor" && <Navbar />}
      {role === "patient" && <PatientNavbar />}

      <Routes>
        {/* Doctor Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute role="doctor">
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/patients"
          element={
            <ProtectedRoute role="doctor">
              <Patients />
            </ProtectedRoute>
          }
        />
        <Route
          path="/diagnostics"
          element={
            <ProtectedRoute role="doctor">
              <Diagnostics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute role="doctor">
              <History />
            </ProtectedRoute>
          }
        />
        <Route
          path="/newdiagnosis"
          element={
            <ProtectedRoute role="doctor">
              <NewDiagnosis />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute role="doctor">
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/evaluation"
          element={
            <ProtectedRoute role="doctor">
              <EvaluationDashboard />
            </ProtectedRoute>
          }
        />

        {/* Patient Routes */}
        <Route
          path="/patient-home"
          element={
            <ProtectedRoute role="patient">
              <PatientHome />
            </ProtectedRoute>
          }
        />
        <Route
          path="/patient-profile"
          element={
            <ProtectedRoute role="patient">
              <PatientProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/symptoms"
          element={
            <ProtectedRoute role="patient">
              <SymptomsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/upload-scans"
          element={
            <ProtectedRoute role="patient">
              <UploadScansPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/patient-history"
          element={
            <ProtectedRoute role="patient">
              <PatientHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/diagnosis-flow"
          element={
            <ProtectedRoute role="patient">
              <DiagnosisFlow />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}

// Root
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Login page */}
        <Route path="/" element={<Login />} />
        {/* All other app routes */}
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);