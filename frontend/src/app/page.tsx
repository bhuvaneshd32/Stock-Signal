"use client";

import { useState } from "react";
import { Search, ExternalLink, FileText, Calendar, RefreshCw } from "lucide-react";

export default function Home() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    
    try {
      const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}&top_k=5`);
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error("Failed to fetch results:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    setUpdating(true);
    setUpdateMessage("");
    try {
      const response = await fetch('http://localhost:8000/update', { method: 'POST' });
      const data = await response.json();
      setUpdateMessage(data.message);
    } catch (error) {
      setUpdateMessage("Failed to trigger update.");
    } finally {
      setUpdating(false);
      // Clear the message after 5 seconds
      setTimeout(() => setUpdateMessage(""), 5000);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header with Update Button */}
        <div className="relative text-center space-y-2">
          <button 
            onClick={handleUpdate} 
            disabled={updating}
            className="absolute right-0 top-0 flex items-center space-x-2 text-sm bg-white border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 text-gray-600 disabled:opacity-50 transition"
          >
            <RefreshCw size={14} className={updating ? "animate-spin" : ""} />
            <span>{updating ? "Starting..." : "Sync Latest Data"}</span>
          </button>
          
          <h1 className="text-4xl font-bold text-slate-800 tracking-tight">StockSignal</h1>
          <p className="text-slate-600">Evidence retrieval for Indian Equities</p>
          
          {updateMessage && (
            <p className="text-sm text-green-600 font-medium mt-2">{updateMessage}</p>
          )}
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="relative w-full max-w-2xl mx-auto">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., dividend declaration or management changes..."
            className="w-full p-4 pr-12 rounded-xl border border-gray-300 shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Search size={20} />
          </button>
        </form>

        {/* Results Area */}
        <div className="space-y-6">
          {loading && <p className="text-center text-slate-500 animate-pulse">Scanning regulatory filings...</p>}
          
          {!loading && searched && results.length === 0 && (
            <p className="text-center text-slate-500">No evidence found for this query.</p>
          )}

          {!loading && results.map((result, idx) => (
            <div key={idx} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-lg text-blue-900 leading-tight">
                    {result.metadata.Company_Name} ({result.metadata.Scrip_Code})
                  </h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-500 mt-2">
                    <span className="flex items-center"><Calendar size={14} className="mr-1" /> {result.metadata.Date.split(' ')[0]}</span>
                    <span className="flex items-center"><FileText size={14} className="mr-1" /> {result.metadata.Category}</span>
                    <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs font-medium border border-blue-100">
                      Score: {result.score.toFixed(2)}
                    </span>
                  </div>
                </div>
                <a 
                  href={result.metadata.Link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  View Source <ExternalLink size={14} className="ml-1" />
                </a>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                <p className="text-sm font-medium text-gray-700 mb-2">{result.metadata.Headline}</p>
                <p className="text-sm text-gray-600 leading-relaxed font-serif">
                  "... {result.text} ..."
                </p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}