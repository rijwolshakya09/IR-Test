"use client";

import { useState } from "react";
import SearchComponent from "./components/SearchComponent";
import DocumentClassification from "./components/DocumentClassification";
import Header from "./components/Header";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"search" | "classification">("search");

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-900/30 rounded-full mix-blend-lighten filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-yellow-900/30 rounded-full mix-blend-lighten filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-900/30 rounded-full mix-blend-lighten filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>

      <Header />

      {/* Main Content */}
      <main className="relative z-10">
        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-4">
          <div className="text-center animate-fade-in">
            <h2 className="text-4xl md:text-6xl font-bold gradient-text mb-4">Discover Research</h2>
            <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-8 leading-relaxed">
              Explore thousands of academic publications from Coventry Portal and classification system
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="flex justify-center mb-8 animate-slide-up">
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg rounded-2xl p-2 shadow-xl border border-white/20 dark:border-gray-700/20">
              <div className="flex space-x-2">
                <button
                  onClick={() => setActiveTab("search")}
                  className={`relative px-6 py-3 rounded-xl font-semibold transition-all duration-300 cursor-pointer ${
                    activeTab === "search"
                      ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg transform scale-105"
                      : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700"
                  }`}
                >
                  <span className="flex items-center space-x-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                    <span>Publication Search</span>
                  </span>
                </button>
                <button
                  onClick={() => setActiveTab("classification")}
                  className={`relative px-6 py-3 rounded-xl font-semibold transition-all duration-300 cursor-pointer ${
                    activeTab === "classification"
                      ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg transform scale-105"
                      : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700"
                  }`}
                >
                  <span className="flex items-center space-x-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
                      />
                    </svg>
                    <span>Document Classification</span>
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
          <div className="animate-slide-up">
            {activeTab === "search" ? <SearchComponent /> : <DocumentClassification />}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 bg-white/50 dark:bg-gray-900/50 backdrop-blur-lg border-t border-gray-200/50 dark:border-gray-700/50 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">IR-Shankar Ghimire</p>
              </div>
            </div>
            <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
              <span>© 2025 Coventry University</span>
              <span>•</span>
              <span>Made with ❤️ by Shankar Ghimire</span>
            </div>
          </div>
        </div>
      </footer>

      <style jsx global>{`
        @keyframes blob {
          0% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
          100% {
            transform: translate(0px, 0px) scale(1);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}
