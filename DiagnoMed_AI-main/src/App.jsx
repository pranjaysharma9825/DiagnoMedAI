import React from "react";
import Navbar from "./components/Navbar";
import Card from "./components/Card";
import RecentPatients from "./components/RecentPatients";
import PatientChart from "./components/PatientChart";
import DiagnosisDistribution from "./components/DiagnosisDistribution";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col min-w-screen">
      <Navbar />

      {/* Main Content */}
      <main className="p-6 w-full space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
          <Card title="Total Patients" value="1,248" color="text-gray-900" />
          <Card title="Pending Diagnoses" value="32" color="text-red-500" />
          <Card title="Completed Reports" value="846" color="text-green-600" />
          <Card title="Activity" value="+12%" color="text-blue-600" />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
          <PatientChart />
          <DiagnosisDistribution />
        </div>
        
        {/* Recent Patients Section */}
        <RecentPatients />
      </main>
    </div>
  );
}

