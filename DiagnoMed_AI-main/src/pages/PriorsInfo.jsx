import React, { useState, useEffect } from "react";
import { Info, Map, Activity } from "lucide-react";

const BACKEND_URL = import.meta.env.VITE_API_URL;

export default function PriorsInfo({ region = "Global" }) {
    const [epiPriors, setEpiPriors] = useState([]);
    const [distribution, setDistribution] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch Epipriors
                const epiRes = await fetch(`${BACKEND_URL}/api/priors/epidemiology?region=${region}`);
                const epiData = await epiRes.json();
                if (epiData.priors) {
                    const sorted = Object.entries(epiData.priors)
                        .sort(([, a], [, b]) => b - a)
                        .slice(0, 5); // Top 5
                    setEpiPriors(sorted);
                }

                // Fetch Distribution
                const distRes = await fetch(`${BACKEND_URL}/api/doctor/diagnosis-distribution`);
                const distData = await distRes.json();
                setDistribution(distData.slice(0, 5));
            } catch (e) {
                console.error("Failed to fetch priors", e);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [region]);

    if (loading) return null;

    return (
        <div className="grid md:grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                <h4 className="text-sm font-bold text-blue-800 mb-3 flex items-center gap-2">
                    <Map className="w-4 h-4" />
                    Top Diseases in {region}
                </h4>
                <div className="space-y-2">
                    {epiPriors.map(([name, prob], i) => (
                        <div key={i} className="flex justify-between text-xs">
                            <span className="text-gray-600">{name}</span>
                            <span className="font-medium text-blue-600">{(prob * 100).toFixed(1)}% prevalence</span>
                        </div>
                    ))}
                    {epiPriors.length === 0 && <p className="text-xs text-gray-500">No data available</p>}
                </div>
            </div>

            <div className="bg-purple-50/50 p-4 rounded-xl border border-purple-100">
                <h4 className="text-sm font-bold text-purple-800 mb-3 flex items-center gap-2">
                    <Activity className="w-4 h-4" />
                    Global Trends
                </h4>
                <div className="space-y-2">
                    {distribution.map((d, i) => (
                        <div key={i} className="flex justify-between text-xs">
                            <span className="text-gray-600">{d.name}</span>
                            <span className="font-medium text-purple-600">{d.value} cases</span>
                        </div>
                    ))}
                    {distribution.length === 0 && <p className="text-xs text-gray-500">No data available</p>}
                </div>
            </div>
        </div>
    );
}
