import { ProteinResults } from "@/components/protein/protein-results";
import { SearchForm } from "@/components/search/search-form";
import { AppFooter, AppHeader } from "@/components/shell/app-shell";

export default async function ProteinPage({ params }: { params: Promise<{ query: string }> }) {
  const query = decodeURIComponent((await params).query).trim();
  return (
    <main className="application-shell">
      <AppHeader><SearchForm initialQuery={query} compact /></AppHeader>
      <div className="page-container protein-page">
        <header className="page-intro"><p className="eyebrow"><span aria-hidden="true" />RCSB Protein Data Bank</p><h1>Structures matching “{query}”</h1><p>Experimental polymer entities from RCSB. Result order does not represent biological importance.</p></header>
        <ProteinResults query={query} />
      </div>
      <AppFooter />
    </main>
  );
}
