interface SearchStatsProps {
  totalResults: number;
  currentPage: number;
  pageSize: number;
  totalPages: number;
  searchTime?: number;
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSortChange: (sortBy: string, sortOrder: "asc" | "desc") => void;
}

export default function SearchStats({
  totalResults,
  currentPage,
  pageSize,
  totalPages,
  searchTime,
  sortBy,
  sortOrder,
  onSortChange,
}: SearchStatsProps) {
  const startResult = (currentPage - 1) * pageSize + 1;
  const endResult = Math.min(currentPage * pageSize, totalResults);

  const sortOptions = [
    { value: "relevance", label: "Relevance" },
    { value: "date", label: "Date" },
    { value: "title", label: "Title" },
  ];

  return (
    <div className="glass rounded-2xl shadow-xl border border-white/20 dark:border-gray-700/20 p-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        {/* Left side - Results info */}
        <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-6">
          <div className="text-sm text-gray-300">
            Showing{" "}
            <span className="font-semibold text-white">
              {startResult}-{endResult}
            </span>{" "}
            of <span className="font-semibold text-indigo-400">{totalResults.toLocaleString()}</span> results
          </div>

          {searchTime && (
            <div className="text-xs text-gray-500 hidden sm:block">Found in {(searchTime / 1000).toFixed(2)}s</div>
          )}

          <div className="text-xs text-gray-500">
            Page {currentPage} of {totalPages}
          </div>
        </div>

        {/* Right side - Sort controls */}
        <div className="flex items-center space-x-3">
          <span className="text-xs font-medium text-gray-400 hidden sm:block">Sort by:</span>

          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value, sortOrder)}
            className="text-xs border border-gray-600 rounded-lg px-3 py-2 text-white bg-slate-800/80 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 cursor-pointer hover:bg-slate-700/80 transition-colors"
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value} className="bg-slate-800 text-white">
                {option.label}
              </option>
            ))}
          </select>

          <button
            onClick={() => onSortChange(sortBy, sortOrder === "asc" ? "desc" : "asc")}
            className="flex items-center space-x-1 px-3 py-2 border border-gray-600 rounded-lg hover:bg-slate-700/80 text-xs text-white bg-slate-800/80 cursor-pointer transition-colors"
            title={sortOrder === "asc" ? "Change to Descending" : "Change to Ascending"}
          >
            <svg
              className={`h-3 w-3 transform transition-transform ${sortOrder === "desc" ? "rotate-180" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
            </svg>
            <span className="hidden sm:inline">{sortOrder === "asc" ? "Asc" : "Desc"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
