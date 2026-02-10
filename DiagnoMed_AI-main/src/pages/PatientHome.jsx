import React from "react";
import { FileText, Upload, History, Users } from "lucide-react";
import { Link } from "react-router-dom";

export default function PatientHome() {
  const userName = "John"; // Replace with dynamic user data if available

  // Example quick stats
  const stats = [
    { id: 1, label: "Total Scans Uploaded", value: 5, color: "bg-blue-100", icon: <Upload className="w-6 h-6 text-blue-600" /> },
    { id: 2, label: "Past Diagnoses", value: 8, color: "bg-green-100", icon: <History className="w-6 h-6 text-green-600" /> },
    { id: 3, label: "Ongoing Conditions", value: 2, color: "bg-yellow-100", icon: <FileText className="w-6 h-6 text-yellow-600" /> },
  ];

  // Category cards
  const categories = [
    { id: 1, label: "Symptom Analysis", icon: <FileText className="w-6 h-6" />, to: "/symptoms", color: "border-blue-400 hover:bg-blue-50" },
    { id: 2, label: "Image Analysis", icon: <Upload className="w-6 h-6" />, to: "/upload-scans", color: "border-green-400 hover:bg-green-50" },
    { id: 3, label: "View Treatment History", icon: <History className="w-6 h-6" />, to: "/patient-history", color: "border-purple-400 hover:bg-purple-50" },
  ];

  return (
    <div className="py-12 px-4 md:px-10">
      {/* Welcome User */}
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-blue-600">Welcome, {userName}!</h1>
        <p className="text-gray-700 mt-2 text-lg">
          Manage your health with our AI-powered assistance. Choose an option below to continue:
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 max-w-5xl mx-auto">
        {stats.map((stat) => (
          <div key={stat.id} className={`flex items-center gap-4 p-6 rounded-xl shadow ${stat.color}`}>
            {stat.icon}
            <div>
              <p className="text-gray-800 font-medium">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Category Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {categories.map((cat) => (
          <Link
            key={cat.id}
            to={cat.to}
            className={`flex items-center gap-3 px-8 py-6 bg-white shadow rounded-xl border ${cat.color} transition`}
          >
            {cat.icon}
            <span className="text-lg font-medium !text-black">{cat.label}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}