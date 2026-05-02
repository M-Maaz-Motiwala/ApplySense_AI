export function Spinner({ className = "" }: { className?: string }) {
  return (
    <svg
      className={`animate-spin h-5 w-5 ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      ></circle>
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  );
}

export function SkeletonLine({ className = "" }: { className?: string }) {
  return (
    <div className={`skeleton-shimmer h-4 rounded-md ${className}`} />
  );
}

export function SkeletonCard() {
  return (
    <div className="glass-panel p-6 mb-4 animate-pulse">
      <div className="flex justify-between items-start mb-4">
        <div className="w-1/2">
          <SkeletonLine className="h-6 w-3/4 mb-2" />
          <SkeletonLine className="w-1/2" />
        </div>
        <SkeletonLine className="h-6 w-16 rounded-full" />
      </div>
      <div className="mt-4">
        <SkeletonLine className="mb-2" />
        <SkeletonLine className="w-5/6 mb-2" />
        <SkeletonLine className="w-4/6" />
      </div>
      <div className="flex gap-4 mt-6">
        <SkeletonLine className="h-10 w-32 rounded-lg" />
        <SkeletonLine className="h-10 w-40 rounded-lg" />
      </div>
    </div>
  );
}
