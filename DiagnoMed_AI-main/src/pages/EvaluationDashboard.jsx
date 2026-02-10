import React, { useState, useEffect } from "react";
import {
    BarChart3,
    LineChart,
    FileBarChart,
    RefreshCw,
    Download,
    CheckCircle,
    AlertCircle,
    TrendingUp,
    Activity
} from "lucide-react";

const BACKEND_URL = import.meta.env.VITE_API_URL;

export default function EvaluationDashboard() {
    const [paretoData, setParetoData] = useState(null);
    const [likertData, setLikertData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState("pareto");

    const fetchParetoResults = async () => {
        try {
            const res = await fetch(`${BACKEND_URL}/api/evaluation/pareto/results`);
            const data = await res.json();
            if (!data.message) {
                setParetoData(data);
            }
        } catch (e) {
            console.log("No Pareto data yet");
        }
    };

    const fetchLikertResults = async () => {
        try {
            const res = await fetch(`${BACKEND_URL}/api/evaluation/likert/results`);
            const data = await res.json();
            if (!data.message) {
                setLikertData(data);
            }
        } catch (e) {
            console.log("No Likert data yet");
        }
    };

    useEffect(() => {
        fetchParetoResults();
        fetchLikertResults();
    }, []);

    const generateParetoEvaluation = async (nCases = 100) => {
        setLoading(true);
        setError("");
        try {
            const res = await fetch(`${BACKEND_URL}/api/evaluation/pareto/generate?n_cases=${nCases}`, {
                method: "POST"
            });
            const data = await res.json();
            if (res.ok) {
                setParetoData(data.results);
            } else {
                setError(data.detail || "Failed to generate evaluation");
            }
        } catch (e) {
            setError("Error: " + e.message);
        } finally {
            setLoading(false);
        }
    };

    const generateLikertEvaluation = async (nResponses = 50) => {
        setLoading(true);
        setError("");
        try {
            const res = await fetch(`${BACKEND_URL}/api/evaluation/likert/generate?n_responses=${nResponses}`, {
                method: "POST"
            });
            const data = await res.json();
            if (res.ok) {
                setLikertData(data.results);
            } else {
                setError(data.detail || "Failed to generate survey");
            }
        } catch (e) {
            setError("Error: " + e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto p-6">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold !text-blue-600 flex items-center gap-3">
                    <FileBarChart className="w-8 h-8" />
                    Research Evaluation Dashboard
                </h1>
                <p className="!text-gray-600 mt-2">
                    Generate Pareto efficiency metrics and Likert survey results for paper analysis
                </p>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
                <button
                    onClick={() => setActiveTab("pareto")}
                    className={`px-4 py-2 rounded-lg font-medium transition ${activeTab === "pareto" ? "!bg-blue-600 !text-white" : "!bg-gray-200 !text-gray-700"}`}
                >
                    <BarChart3 className="w-4 h-4 inline mr-2" />
                    Pareto Analysis
                </button>
                <button
                    onClick={() => setActiveTab("likert")}
                    className={`px-4 py-2 rounded-lg font-medium transition ${activeTab === "likert" ? "!bg-blue-600 !text-white" : "!bg-gray-200 !text-gray-700"}`}
                >
                    <LineChart className="w-4 h-4 inline mr-2" />
                    Likert Survey
                </button>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
                    {error}
                </div>
            )}

            {/* Pareto Tab */}
            {activeTab === "pareto" && (
                <div className="space-y-6">
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold !text-gray-800">Pareto Efficiency Evaluation</h2>
                            <button
                                onClick={() => generateParetoEvaluation(100)}
                                disabled={loading}
                                className="px-4 py-2 !bg-blue-600 !text-white rounded-lg font-medium flex items-center gap-2 hover:bg-blue-700 transition disabled:opacity-50"
                            >
                                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                                Generate 100 Cases
                            </button>
                        </div>

                        {!paretoData ? (
                            <div className="text-center py-12 text-gray-500">
                                <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p>No evaluation data. Click "Generate" to create synthetic test cases.</p>
                            </div>
                        ) : (
                            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <div className="bg-blue-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-gray-600">Accuracy</p>
                                    <p className="text-3xl font-bold text-blue-600">{(paretoData.metrics?.accuracy * 100 || 0).toFixed(1)}%</p>
                                </div>
                                <div className="bg-green-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-gray-600">Avg Cost</p>
                                    <p className="text-3xl font-bold text-green-600">${paretoData.metrics?.avg_cost?.toFixed(0) || 0}</p>
                                </div>
                                <div className="bg-purple-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-gray-600">Avg Tests</p>
                                    <p className="text-3xl font-bold text-purple-600">{paretoData.metrics?.avg_tests?.toFixed(1) || 0}</p>
                                </div>
                                <div className="bg-yellow-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-gray-600">Pareto Optimal</p>
                                    <p className="text-3xl font-bold text-yellow-600">{paretoData.metrics?.pareto_optimal || 0}%</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {paretoData && paretoData.cases && (
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <h3 className="text-lg font-bold !text-gray-800 mb-4">Sample Cases</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="p-2 text-left">Case</th>
                                            <th className="p-2 text-left">True Diagnosis</th>
                                            <th className="p-2 text-left">Predicted</th>
                                            <th className="p-2 text-center">Tests</th>
                                            <th className="p-2 text-right">Cost</th>
                                            <th className="p-2 text-center">Correct</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {paretoData.cases.slice(0, 10).map((c, i) => (
                                            <tr key={i} className="border-t">
                                                <td className="p-2">{i + 1}</td>
                                                <td className="p-2">{c.true_diagnosis}</td>
                                                <td className="p-2">{c.predicted}</td>
                                                <td className="p-2 text-center">{c.n_tests}</td>
                                                <td className="p-2 text-right">${c.cost}</td>
                                                <td className="p-2 text-center">
                                                    {c.correct ? (
                                                        <CheckCircle className="w-4 h-4 text-green-600 mx-auto" />
                                                    ) : (
                                                        <AlertCircle className="w-4 h-4 text-red-600 mx-auto" />
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Likert Tab */}
            {activeTab === "likert" && (
                <div className="space-y-6">
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold !text-gray-800">Likert Survey Analysis</h2>
                            <button
                                onClick={() => generateLikertEvaluation(50)}
                                disabled={loading}
                                className="px-4 py-2 !bg-blue-600 !text-white rounded-lg font-medium flex items-center gap-2 hover:bg-blue-700 transition disabled:opacity-50"
                            >
                                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                                Generate 50 Responses
                            </button>
                        </div>

                        {!likertData ? (
                            <div className="text-center py-12 text-gray-500">
                                <LineChart className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p>No survey data. Click "Generate" to create simulated clinician responses.</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {likertData.questions && likertData.questions.map((q, i) => (
                                    <div key={i} className="bg-gray-50 rounded-lg p-4">
                                        <p className="font-medium text-gray-800 mb-2">{q.question}</p>
                                        <div className="flex items-center gap-4">
                                            <div className="flex-1 h-4 bg-gray-200 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-blue-600 transition-all"
                                                    style={{ width: `${(q.mean / 5) * 100}%` }}
                                                />
                                            </div>
                                            <span className="font-bold text-blue-600">{q.mean?.toFixed(2)}/5</span>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">σ = {q.std?.toFixed(2)}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {likertData && likertData.summary && (
                        <div className="bg-white rounded-xl shadow-lg p-6">
                            <h3 className="text-lg font-bold !text-gray-800 mb-4">Summary Statistics</h3>
                            <div className="grid md:grid-cols-3 gap-4">
                                <div className="bg-blue-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-gray-600">Overall Mean</p>
                                    <p className="text-3xl font-bold text-blue-600">{likertData.summary.overall_mean?.toFixed(2)}</p>
                                </div>
                                <div className="bg-green-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-gray-600">Response Count</p>
                                    <p className="text-3xl font-bold text-green-600">{likertData.summary.n_responses}</p>
                                </div>
                                <div className="bg-purple-50 rounded-lg p-4 text-center">
                                    <p className="text-sm text-gray-600">Cronbach's α</p>
                                    <p className="text-3xl font-bold text-purple-600">{likertData.summary.cronbachs_alpha?.toFixed(3)}</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
