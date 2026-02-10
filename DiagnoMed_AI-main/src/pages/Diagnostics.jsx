import React from "react";

const reports = [
  { id: "DX001", patient: "Aarav Sharma", type: "ECG", status: "Completed", date: "2025-08-01" },
  { id: "DX002", patient: "Saanvi Patel", type: "Blood Test", status: "Pending", date: "2025-08-02" },
  { id: "DX003", patient: "Rohan Singh", type: "ECG", status: "In Review", date: "2025-08-03" },
  { id: "DX004", patient: "Ananya Gupta", type: "Allergy Test", status: "Completed", date: "2025-08-04" },
  { id: "DX005", patient: "Kabir Mehta", type: "Ultrasound", status: "Pending", date: "2025-08-05" },
  { id: "DX006", patient: "Isha Verma", type: "Allergy Test", status: "In Review", date: "2025-08-06" },
  { id: "DX007", patient: "Vivaan Reddy", type: "Migraine Check", status: "Completed", date: "2025-08-07" },
  { id: "DX008", patient: "Diya Nair", type: "Thyroid Test", status: "Pending", date: "2025-08-08" },
];

export default function Diagnostics() {
  const statusClasses = {
    Completed: "bg-blue-600 text-white dark:bg-blue-500",
    Pending: "bg-red-600 text-white dark:bg-red-500",
    "In Review": "bg-pink-600 text-white dark:bg-pink-500",
  };

  return (
    <div className="p-6 min-w-screen bg-gray-50 dark:bg-gradient-to-br dark:from-background-gradient1 dark:via-background-gradient2 dark:to-background-gradient3">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-text-light">Diagnostics</h2>

      <div className="mt-6 space-y-4">
        {reports.map((r) => (
          <div
            key={r.id}
            className="bg-white dark:bg-panel-dark shadow p-4 rounded-lg flex justify-between items-center border-l-4 border-blue-600 dark:border-accent-pink"
          >
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-text-light">
                {r.type} - {r.patient}
              </h2>
              <p className="text-sm text-gray-500 dark:text-text-blue">
                Report ID: {r.id} | Date: {r.date}
              </p>
            </div>
            <span
              className={`px-3 py-1 text-sm rounded-full ${statusClasses[r.status]}`}
            >
              {r.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
