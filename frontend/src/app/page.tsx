import { JobSearchForm } from "./components/JobSearchForm";
import { JobList } from "./components/job-list";
import { SearchQueries } from "./components/search-queries";

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Section 1: Job Search Form */}
      <section className="bg-[#11212d] py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          <JobSearchForm />
        </div>
      </section>

      {/* Section 2: Saved Searches */}
      <section className="bg-[#11212d] py-8">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="flex justify-center">
            <div className="w-full max-w-md">
              <SearchQueries />
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Job Listings - Full Width */}
      <section className="w-full">
        <JobList />
      </section>
    </main>
  );
}