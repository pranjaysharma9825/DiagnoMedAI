import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { User, LogOut, Home, Activity, History } from "lucide-react";

export default function PatientNavbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("role");
    navigate("/");
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="bg-white shadow-md px-6 py-3 flex justify-between items-center">
      {/* Logo */}
      <h1 className="text-2xl font-bold text-blue-600 cursor-pointer">
        DiagnoMed AI
      </h1>

      {/* Navigation Buttons */}
      <nav className="flex items-center space-x-4">
        {/* Home */}
        <Link
          to="/patient-home"
          className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${isActive("/patient-home")
              ? "text-blue-700"
              : "text-gray-700 hover:text-blue-600"
            }`}
        >
          <Home className="w-5 h-5" /> Home
        </Link>

        {/* Diagnosis */}
        <Link
          to="/symptoms"
          className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${isActive("/symptoms") || isActive("/diagnosis-flow")
              ? "text-blue-700"
              : "text-gray-700 hover:text-blue-600"
            }`}
        >
          <Activity className="w-5 h-5" /> Diagnosis
        </Link>

        {/* History */}
        <Link
          to="/patient-history"
          className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${isActive("/patient-history")
              ? "text-blue-700"
              : "text-gray-700 hover:text-blue-600"
            }`}
        >
          <History className="w-5 h-5" /> History
        </Link>

        {/* Profile */}
        <Link
          to="/patient-profile"
          className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${isActive("/patient-profile")
              ? "text-blue-700"
              : "text-gray-700 hover:text-blue-600"
            }`}
        >
          <User className="w-5 h-5" /> Profile
        </Link>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 rounded-md text-gray-700 hover:bg-red-100 hover:text-red-600 transition-colors"
        >
          <LogOut className="w-5 h-5" /> Logout
        </button>
      </nav>
    </header>
  );
}
