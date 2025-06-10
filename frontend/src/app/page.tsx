import { JobSearchForm } from "./components/JobSearchForm";
import { JobList } from "./components/job-list";
import { SearchQueries } from "./components/search-queries";

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-white">
      <div className="container mx-auto py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <JobSearchForm />
            <JobList />
          </div>
          <div>
            <SearchQueries />
          </div>
        </div>
      </div>
    </main>
  );
}