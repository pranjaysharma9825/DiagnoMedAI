import React from "react";

const historyData = [
  { date: "2025-08-01", activity: "Aarav Sharma diagnosed with Hypertension" },
  { date: "2025-08-02", activity: "Saanvi Patel scheduled for blood test" },
  { date: "2025-08-03", activity: "Rohan Singh completed ECG" },
  { date: "2025-08-04", activity: "Ananya Gupta follow-up consultation" },
  { date: "2025-08-05", activity: "Kabir Mehta ultrasound results reviewed" },
  { date: "2025-08-06", activity: "Isha Verma scheduled for allergy test" },
  { date: "2025-08-07", activity: "Vivaan Reddy migraine treatment updated" },
  { date: "2025-08-08", activity: "Diya Nair thyroid report reviewed" },
];

export default function History() {
  return (
    <div className="p-6 min-w-screen bg-gray-50 dark:bg-gradient-to-br dark:from-background-gradient1 dark:via-background-gradient2 dark:to-background-gradient3">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-text-light">History</h2>

      <ul className="mt-6 space-y-4">
        {historyData.map((h, i) => (
          <li
            key={i}
            className="bg-white dark:bg-panel-dark shadow p-4 rounded-lg border-l-4 border-blue-600 dark:border-accent-pink"
          >
            <p className="text-sm text-gray-500 dark:text-text-blue">{h.date}</p>
            <p className="font-medium text-gray-900 dark:text-text-light">{h.activity}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
