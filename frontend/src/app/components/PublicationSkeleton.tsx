export default function PublicationSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden animate-pulse">
      <div className="p-6">
        {/* Title skeleton */}
        <div className="h-6 bg-gray-200 rounded mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>

        {/* Authors skeleton */}
        <div className="flex items-center gap-2 mb-3">
          <div className="h-4 w-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-48"></div>
        </div>

        {/* Date and score skeleton */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <div className="h-4 w-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-24"></div>
          </div>
          <div className="h-6 bg-gray-200 rounded w-20"></div>
        </div>

        {/* Abstract skeleton */}
        <div className="border-t border-gray-100 pt-4">
          <div className="h-4 bg-gray-200 rounded mb-2"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>

        {/* Action button skeleton */}
        <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100">
          <div className="h-10 bg-gray-200 rounded w-32"></div>
        </div>
      </div>
    </div>
  );
}

export function SearchSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, index) => (
        <PublicationSkeleton key={index} />
      ))}
    </div>
  );
}
