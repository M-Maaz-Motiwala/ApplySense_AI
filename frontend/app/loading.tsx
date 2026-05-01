import { SkeletonCard, SkeletonLine } from "../components/ui/Loader";

export default function Loading() {
  return (
    <main className="animate-pulse py-8">
      <div className="flex justify-between items-center mb-8">
        <div className="w-1/3">
          <SkeletonLine className="h-8 w-3/4 mb-2" />
          <SkeletonLine className="h-4 w-1/2" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </main>
  );
}
