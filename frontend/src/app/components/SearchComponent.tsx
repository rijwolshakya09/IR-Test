"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ApiService, Publication } from "../services/api";
import LoadingSpinner from "./LoadingSpinner";
import { SearchSkeleton } from "./PublicationSkeleton";
import SearchStats from "./SearchStats";
import QuickSearch from "./QuickSearch";
import PublicationCard from "./PublicationCard";

export default function SearchComponent() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [results, setResults] = useState<Publication[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalResults, setTotalResults] = useState(0);
  const [pageSize] = useState(10);
  const [error, setError] = useState<string | null>(null);
  const [searchTime, setSearchTime] = useState<number>(0);
  const [sortBy, setSortBy] = useState("relevance");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Debounce effect for query
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(query);
    }, 400);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query]);

  // Clear search function
  const handleClearSearch = () => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    setQuery("");
    setDebouncedQuery("");
    setCurrentPage(1);
    setError(null);
  };

  // Search function
  const searchPublications = useCallback(
    async (searchQuery: string, page: number = 1) => {
      setLoading(true);
      setError(null);
      const startTime = Date.now();

      try {
        const response = await ApiService.searchPublications(searchQuery, page, pageSize);

        // Always sort by score first (highest to lowest), then apply additional sorting
        const sortedResults = [...response.results].sort((a, b) => {
          // Primary sort: by score (highest first)
          const scoreA = a.score || 0;
          const scoreB = b.score || 0;

          if (scoreA !== scoreB) {
            return scoreB - scoreA; // Higher scores first
          }

          // Secondary sort: if scores are equal, apply user's sort preference
          if (sortBy !== "relevance") {
            let aValue, bValue;
            switch (sortBy) {
              case "date":
                aValue = new Date(a.published_date || 0).getTime();
                bValue = new Date(b.published_date || 0).getTime();
                break;
              case "title":
                aValue = a.title.toLowerCase();
                bValue = b.title.toLowerCase();
                break;
              default:
                return 0; // No secondary sort
            }

            if (sortOrder === "asc") {
              return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
            } else {
              return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
            }
          }

          return 0; // Equal scores, no secondary sort
        });

        setResults(sortedResults);
        setTotalResults(response.total);
        setTotalPages(response.total_pages);
        setSearchTime(Date.now() - startTime);
      } catch (err) {
        console.error("Search error:", err);
        setError("Failed to fetch search results. Please try again.");
        setResults([]);
        setTotalResults(0);
        setTotalPages(0);
      } finally {
        setLoading(false);
      }
    },
    [pageSize, sortBy, sortOrder]
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    searchPublications(query, 1);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    searchPublications(debouncedQuery, page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSortChange = (newSortBy: string, newSortOrder: "asc" | "desc") => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
    setCurrentPage(1);
    searchPublications(debouncedQuery, 1);
  };

  // Load initial results
  useEffect(() => {
    searchPublications("");
  }, [searchPublications]);

  // Effect to trigger search when debounced query changes
  useEffect(() => {
    setCurrentPage(1);
    searchPublications(debouncedQuery, 1);
  }, [debouncedQuery, searchPublications]);

  return (
    <div className="space-y-8">
      {/* Enhanced Search Section */}
      <div className="glass rounded-3xl shadow-2xl p-8 border border-white/20 dark:border-gray-700/20 animate-fade-in">
        <form onSubmit={handleSearch} className="space-y-6">
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none z-10">
              <div className="w-6 h-6 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center">
                <svg className="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Discover research papers, authors, and insights..."
              className="w-full pl-16 pr-16 py-5 bg-white/90 dark:bg-gray-800/90 border-2 border-gray-200 dark:border-gray-600 rounded-2xl focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 dark:focus:border-indigo-400 text-lg text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 shadow-lg backdrop-blur-sm transition-all duration-300 hover:shadow-xl group-focus-within:shadow-xl"
            />
            {query && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute inset-y-0 right-0 pr-6 flex items-center text-gray-400 hover:text-red-500 transition-all duration-200 cursor-pointer z-10 group"
                aria-label="Clear search"
              >
                <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 hover:bg-red-100 dark:hover:bg-red-900/20 flex items-center justify-center transition-colors">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
              </button>
            )}
          </div>

          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-6">
            <div className="flex flex-wrap gap-4">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary px-8 py-4 rounded-2xl font-semibold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-3 shadow-lg hover:shadow-2xl transform hover:-translate-y-1 cursor-pointer group"
              >
                {loading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Discovering...</span>
                  </>
                ) : (
                  <>
                    <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white/30 transition-colors">
                      <svg className="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                      </svg>
                    </div>
                    <span>Explore Research</span>
                  </>
                )}
              </button>

              {query && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="bg-white/90 dark:bg-gray-800/90 text-gray-700 dark:text-gray-300 px-6 py-4 rounded-2xl hover:bg-gray-50 dark:hover:bg-gray-700 focus:ring-4 focus:ring-gray-500/20 font-semibold transition-all duration-300 flex items-center space-x-2 shadow-lg hover:shadow-xl transform hover:-translate-y-1 cursor-pointer border border-gray-200 dark:border-gray-600"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  <span>Reset Search</span>
                </button>
              )}
            </div>

            {totalResults > 0 && (
              <div className="bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/30 dark:to-green-900/30 text-emerald-700 dark:text-emerald-300 px-6 py-3 rounded-2xl border border-emerald-200 dark:border-emerald-700 shadow-lg animate-scale-in">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                  <span className="font-semibold">
                    Discovered{" "}
                    <span className="text-emerald-800 dark:text-emerald-200 font-bold">
                      {totalResults.toLocaleString()}
                    </span>{" "}
                    publications
                  </span>
                  {loading && <LoadingSpinner size="sm" />}
                </div>
              </div>
            )}
          </div>
        </form>

        {/* Quick Search Suggestions */}
        <QuickSearch onQuickSearch={setQuery} />
      </div>

      {/* Error Message */}
      {error && (
        <div className="glass rounded-2xl p-6 shadow-xl border border-red-200 dark:border-red-800 animate-slide-up">
          <div className="flex items-center space-x-3 text-red-700 dark:text-red-300">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-red-800 dark:text-red-200">Search Error</h3>
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Search Stats & Sort Controls */}
      {!loading && totalResults > 0 && (
        <SearchStats
          totalResults={totalResults}
          currentPage={currentPage}
          pageSize={pageSize}
          totalPages={totalPages}
          searchTime={searchTime}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSortChange={handleSortChange}
        />
      )}

      {/* Results Section */}
      <div className="space-y-6">
        {loading ? (
          <SearchSkeleton />
        ) : (
          results.map((publication, index) => (
            <PublicationCard key={`${publication.link}-${index}`} publication={publication} />
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
      )}

      {/* No Results */}
      {!loading && results.length === 0 && query && (
        <div className="text-center py-16 glass rounded-3xl shadow-xl border border-white/20 dark:border-gray-700/20 animate-slide-up">
          <div className="max-w-md mx-auto">
            <div className="bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 rounded-full p-6 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
              <svg
                className="h-12 w-12 text-gray-400 dark:text-gray-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0120 12a8 8 0 00-16 0 8 8 0 002 5.291"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">No Research Found</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              We couldn&apos;t find any publications matching your search criteria.
            </p>
            <div className="space-y-3 mb-6">
              <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Suggestions:</p>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                <li className="flex items-center space-x-2">
                  <div className="w-1 h-1 bg-indigo-500 rounded-full"></div>
                  <span>Try different or broader keywords</span>
                </li>
                <li className="flex items-center space-x-2">
                  <div className="w-1 h-1 bg-indigo-500 rounded-full"></div>
                  <span>Check your spelling</span>
                </li>
                <li className="flex items-center space-x-2">
                  <div className="w-1 h-1 bg-indigo-500 rounded-full"></div>
                  <span>Use more general search terms</span>
                </li>
              </ul>
            </div>
            <button
              onClick={handleClearSearch}
              className="btn-primary px-6 py-3 rounded-2xl font-semibold shadow-lg hover:shadow-xl cursor-pointer transform hover:-translate-y-1 transition-all duration-300"
            >
              Explore All Publications
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Simple Pagination Component
function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const pages = [];
  const maxVisible = 5;
  let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  const end = Math.min(totalPages, start + maxVisible - 1);

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return (
    <div className="flex justify-center items-center space-x-2 py-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-4 py-2 rounded-xl bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 cursor-pointer"
      >
        Previous
      </button>

      {pages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 cursor-pointer ${
            currentPage === page
              ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg"
              : "bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          }`}
        >
          {page}
        </button>
      ))}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 rounded-xl bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 cursor-pointer"
      >
        Next
      </button>
    </div>
  );
}
