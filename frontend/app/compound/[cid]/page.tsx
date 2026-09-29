import { CompoundExplorer } from "@/components/compound/compound-explorer";
import { SearchForm } from "@/components/search/search-form";
import { AppFooter, AppHeader } from "@/components/shell/app-shell";
import { ErrorState } from "@/components/states/scientific-state";

export default async function CompoundPage({ params }: { params: Promise<{ cid: string }> }) {
  const cidText = (await params).cid;
  const cid = Number(cidText);
  return (
    <main className="application-shell explorer-page">
      <AppHeader><SearchForm compact /></AppHeader>
      <div className="explorer-container">
        {Number.isSafeInteger(cid) && cid > 0 ? <CompoundExplorer cid={cid} /> : <ErrorState title="Invalid compound identifier" detail="A PubChem CID must be a positive whole number." />}
      </div>
      <AppFooter />
    </main>
  );
}
