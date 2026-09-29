import { StructureExplorer } from "@/components/protein/structure-explorer";
import { SearchForm } from "@/components/search/search-form";
import { AppFooter, AppHeader } from "@/components/shell/app-shell";

export default async function StructurePage({ params }: { params: Promise<{ pdbId: string }> }) {
  const pdbId = (await params).pdbId.toUpperCase();
  return (
    <main className="application-shell explorer-page">
      <AppHeader><SearchForm compact /></AppHeader>
      <div className="explorer-container"><StructureExplorer pdbId={pdbId} /></div>
      <AppFooter />
    </main>
  );
}
