"use client";

import { useState } from "react";
import { Publication } from "../services/api";

interface PublicationCardProps {
  publication: Publication;
}

export default function PublicationCard({ publication }: PublicationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatDate = (dateString: string) => {
    if (!dateString) return "Date not available";
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return dateString;
      }
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  const getScoreColor = (score: number) => {
    const numScore = Number(score) || 0;
    if (numScore >= 0.8) return "from-emerald-500 to-green-500";
    if (numScore >= 0.6) return "from-blue-500 to-indigo-500";
    if (numScore >= 0.4) return "from-yellow-500 to-orange-500";
    if (numScore >= 0.2) return "from-orange-500 to-red-500";
    return "from-gray-500 to-slate-500";
  };

  return (
    <div className="group relative bg-slate-800 backdrop-blur-sm rounded-2xl border border-slate-700/50 hover:border-slate-600/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/10 animate-fade-in overflow-hidden shadow-xl">
      {/* Gradient overlay for extra depth */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800/90 via-slate-900/80 to-slate-800/90 pointer-events-none" />

      {/* Hover glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* Score badge - Always show if score exists */}
      {publication.score !== undefined && publication.score !== null && (
        <div className="absolute -top-3 -right-3 z-20">
          <div
            className={`bg-gradient-to-r ${getScoreColor(
              publication.score
            )} text-white px-3 py-1.5 rounded-full text-xs font-bold shadow-lg flex items-center gap-1.5 border-2 border-white/20`}
          >
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            <span>{Number(publication.score).toFixed(2)}</span>
          </div>
        </div>
      )}

      <div className="relative p-6 space-y-4">
        {/* Title */}
        <div className="space-y-2">
          <h3 className="text-lg font-bold text-white leading-tight group-hover:text-indigo-300 transition-colors duration-300 line-clamp-2">
            <a
              href={publication.link}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline decoration-2 decoration-indigo-400 cursor-pointer"
            >
              {publication.title}
            </a>
          </h3>
        </div>

        {/* Authors and Date */}
        <div className="flex flex-wrap items-center gap-3 text-sm">
          {/* Authors */}
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <div className="flex flex-wrap gap-2">
              {publication.authors && publication.authors.length > 0 ? (
                publication.authors.slice(0, isExpanded ? publication.authors.length : 2).map((author, index) => (
                  <span key={index} className="flex items-center">
                    {author.profile ? (
                      <a
                        href={author.profile}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={`View ${author.name}'s profile`}
                        className="group inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 hover:from-indigo-500/20 hover:to-purple-500/20 border border-indigo-400/30 hover:border-indigo-400/50 rounded-full text-indigo-300 hover:text-indigo-200 transition-all duration-200 font-medium hover:shadow-lg hover:shadow-indigo-500/10 transform hover:-translate-y-0.5 animate-pulse-glow cursor-pointer"
                      >
                        <svg
                          className="w-3.5 h-3.5 text-indigo-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                          />
                        </svg>
                        <span>{author.name}</span>
                        <svg
                          className="w-3 h-3 text-indigo-400 opacity-70 group-hover:opacity-100 transition-opacity"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                          />
                        </svg>
                      </a>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-700/50 border border-slate-600/50 rounded-full text-slate-300 font-medium">
                        <svg
                          className="w-3.5 h-3.5 text-slate-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                          />
                        </svg>
                        <span>{author.name}</span>
                      </span>
                    )}
                    {index < publication.authors.length - 1 && <span className="text-slate-500 ml-2 mr-1">•</span>}
                  </span>
                ))
              ) : (
                <span className="text-slate-400">No authors available</span>
              )}
              {!isExpanded && publication.authors && publication.authors.length > 2 && (
                <button
                  onClick={() => setIsExpanded(true)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-700/30 hover:bg-slate-700/50 border border-slate-600/30 hover:border-slate-600/50 rounded-full text-indigo-400 hover:text-indigo-300 transition-all duration-200 font-medium text-sm cursor-pointer"
                >
                  <span>+{publication.authors.length - 2} more</span>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Separator */}
          <div className="w-1 h-1 bg-slate-500 rounded-full" />

          {/* Date */}
          <div className="flex items-center gap-2 text-slate-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span className="font-medium">{formatDate(publication.published_date)}</span>
          </div>

          {/* Score Display */}
          {publication.score !== undefined && publication.score !== null && (
            <>
              <div className="w-1 h-1 bg-slate-500 rounded-full" />
              <div className="flex items-center gap-2 text-slate-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                <span className="font-medium text-indigo-400">Score: {Number(publication.score).toFixed(2)}</span>
              </div>
            </>
          )}
        </div>

        {/* Abstract */}
        {publication.abstract && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span className="font-medium">Abstract</span>
            </div>
            <p className="text-slate-300 leading-relaxed text-sm">
              {isExpanded ? publication.abstract : truncateText(publication.abstract, 200)}
            </p>
            {publication.abstract.length > 200 && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-indigo-400 hover:text-indigo-300 font-medium text-sm flex items-center gap-1 transition-colors duration-200 cursor-pointer"
              >
                <span>{isExpanded ? "Show less" : "Read more"}</span>
                <svg
                  className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
          <div className="flex items-center gap-3">
            {/* View Publication Button */}
            <a
              href={publication.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 text-sm cursor-pointer"
            >
              <span>View Publication</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>
          </div>

          {/* Additional metadata */}
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
            <span>External Link</span>
          </div>
        </div>
      </div>
    </div>
  );
}
