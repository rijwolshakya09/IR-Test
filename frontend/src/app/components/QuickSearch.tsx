interface QuickSearchProps {
  onQuickSearch: (query: string) => void;
}

export default function QuickSearch({ onQuickSearch }: QuickSearchProps) {
  const suggestions = [
    "machine learning",
    "artificial intelligence",
    "data science",
    "blockchain",
    "cybersecurity",
    "financial analysis",
    "economics",
    "business strategy",
    "sustainable development",
    "digital transformation",
  ];

  return (
    <div className="bg-slate-800/50 rounded-lg shadow-sm border border-slate-700 p-4 mt-6">
      <h3 className="text-sm font-medium text-slate-300 mb-3">Quick Search Suggestions</h3>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onQuickSearch(suggestion)}
            className="px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-sm hover:bg-indigo-500/30 transition-colors duration-200 cursor-pointer border border-indigo-500/30"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
