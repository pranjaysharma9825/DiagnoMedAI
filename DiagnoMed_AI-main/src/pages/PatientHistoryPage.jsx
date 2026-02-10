import React, { useState, useEffect } from "react";
import { History, Activity, FileText, Image, AlertCircle } from "lucide-react";

const BACKEND_URL = import.meta.env.VITE_API_URL;

export default function PatientHistoryPage() {
  const [latestAnalysis, setLatestAnalysis] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // Check for latest analysis from localStorage (just submitted)
    const lastAnalysis = localStorage.getItem("lastAnalysis");
    if (lastAnalysis) {
      try {
        setLatestAnalysis(JSON.parse(lastAnalysis));
        localStorage.removeItem("lastAnalysis"); // Clear after reading
      } catch (e) {
        console.error("Failed to parse lastAnalysis", e);
      }
    }

    // Fetch all cases from backend
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/doctor/cases`);
      if (res.ok) {
        const data = await res.json();
        setCases(data);
      }
    } catch (err) {
      console.error("Failed to fetch cases:", err);
      setError("Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  const parseDdxCandidates = (ddxJson) => {
    if (!ddxJson) return [];
    try {
      return JSON.parse(ddxJson);
    } catch {
      return [];
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      {/* Latest Analysis Result (if just submitted) */}
      {latestAnalysis && (
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 shadow-lg rounded-xl p-6">
          <h1 className="flex items-center gap-2 text-2xl font-bold !text-green-700 mb-4">
            <AlertCircle className="w-6 h-6" />
            Latest Analysis Result
          </h1>

          <div className="grid md:grid-cols-2 gap-6">
            {/* DDX Results */}
            <div className="bg-white rounded-lg p-4 shadow">
              <h2 className="font-semibold text-lg !text-blue-600 mb-3 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Symptom-Based Diagnosis
              </h2>
              {latestAnalysis.ddx_candidates && latestAnalysis.ddx_candidates.length > 0 ? (
                <ul className="space-y-2">
                  {latestAnalysis.ddx_candidates.slice(0, 5).map((c, i) => (
                    <li key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="font-medium !text-gray-800">{c.name}</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                        {Math.round((c.base_probability || 0) * 100)}%
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="!text-gray-500">No DDx candidates identified</p>
              )}
            </div>

            {/* X-Ray Results */}
            <div className="bg-white rounded-lg p-4 shadow">
              <h2 className="font-semibold text-lg !text-blue-600 mb-3 flex items-center gap-2">
                <Image className="w-5 h-5" />
                X-Ray Analysis
              </h2>
              {latestAnalysis.cnn_output && latestAnalysis.cnn_output !== "Model unavailable" ? (
                <div>
                  <p className="text-lg font-medium !text-gray-800">
                    {latestAnalysis.cnn_output}
                  </p>
                  {latestAnalysis.cnn_confidence && (
                    <p className="!text-gray-600">
                      Confidence: {Math.round(latestAnalysis.cnn_confidence * 100)}%
                    </p>
                  )}
                  {latestAnalysis.image_url && (
                    <img
                      src={`${BACKEND_URL}${latestAnalysis.image_url}`}
                      alt="X-ray"
                      className="mt-3 rounded-lg max-h-48 object-contain"
                    />
                  )}
                </div>
              ) : (
                <p className="!text-gray-500">No X-ray analysis available</p>
              )}
            </div>
          </div>

          {/* Analysis Summary */}
          {latestAnalysis.analysis_output && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="!text-blue-800 font-medium">{latestAnalysis.analysis_output}</p>
            </div>
          )}
        </div>
      )}

      {/* Past Diagnoses */}
      <div className="bg-white shadow rounded-xl p-6">
        <h1 className="flex items-center gap-2 text-2xl font-bold !text-blue-600 mb-4">
          <History className="w-6 h-6" />
          Diagnosis History
        </h1>

        {loading ? (
          <p className="!text-gray-500">Loading...</p>
        ) : error ? (
          <p className="!text-red-500">{error}</p>
        ) : cases.length === 0 ? (
          <p className="!text-gray-500">No previous diagnoses found</p>
        ) : (
          <ul className="space-y-3">
            {cases.map((item) => (
              <li
                key={item.id}
                className="p-4 border border-gray-200 rounded-lg bg-gray-50 hover:bg-gray-100 transition"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium !text-gray-800">
                      Case ID: {item.id?.slice(0, 8)}...
                    </p>
                    <p className="!text-gray-600 text-sm mt-1">
                      Symptoms: {item.symptoms?.slice(0, 100)}...
                    </p>
                    {item.analysis_output && (
                      <p className="!text-blue-600 mt-2 font-medium">
                        {item.analysis_output}
                      </p>
                    )}
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${item.status === 'analyzed'
                      ? '!bg-green-100 !text-green-700'
                      : '!bg-yellow-100 !text-yellow-700'
                    }`}>
                    {item.status || 'pending'}
                  </span>
                </div>
                <p className="text-sm !text-gray-400 mt-2">
                  {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
