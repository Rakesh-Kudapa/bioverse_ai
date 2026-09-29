import { SearchResults } from "@/components/search/search-results";
import { SearchForm } from "@/components/search/search-form";
import { AppFooter, AppHeader } from "@/components/shell/app-shell";
import { EmptyState } from "@/components/states/scientific-state";

export default async function ExplorePage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const query = (await searchParams).q?.trim() ?? "";
  return (
    <main className="application-shell">
      <AppHeader><SearchForm initialQuery={query} compact /></AppHeader>
      <div className="page-container search-page">
        <header className="page-intro"><p className="eyebrow"><span aria-hidden="true" />Deterministic source search</p><h1>Scientific records</h1><p>Compounds and experimental protein structures are queried separately and labeled by source.</p></header>
        {query ? <SearchResults query={query} /> : <EmptyState title="Search BioVerse" detail="Enter a compound name, protein symbol, or protein name to begin." />}
      </div>
      <AppFooter />
    </main>
  );
}
