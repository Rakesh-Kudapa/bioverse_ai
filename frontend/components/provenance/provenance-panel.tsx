import type { SourceProvenance } from "@/types/bioverse";

const sourceNames = { pubchem: "PubChem", rcsb_pdb: "RCSB Protein Data Bank" } as const;

export function ProvenancePanel({
  source,
  sourceId,
  sourceUrl,
  provenance,
}: {
  source: SourceProvenance["source_name"];
  sourceId: string;
  sourceUrl: string;
  provenance: SourceProvenance[];
}) {
  const retrievedAt = provenance[0]?.retrieved_at;
  const sourceLabel = source === "pubchem" ? `CID ${sourceId}` : `PDB ${sourceId}`;

  return (
    <aside className="provenance-panel" aria-labelledby="source-heading">
      <p className="panel-kicker" id="source-heading">Source</p>
      <h2>{sourceNames[source]}</h2>
      <span className="source-record">{sourceLabel}</span>
      <dl>
        <div><dt>Retrieved</dt><dd>{retrievedAt ? new Date(retrievedAt).toLocaleString() : "Not reported"}</dd></div>
        <div><dt>Traced fields</dt><dd>{provenance.length}</dd></div>
      </dl>
      <a className="source-link" href={sourceUrl} target="_blank" rel="noreferrer">
        Open source record <span aria-hidden="true">↗</span>
      </a>
      <details>
        <summary>Field provenance</summary>
        <ul>{provenance.slice(0, 12).map((item, index) => <li key={`${item.field_path}-${index}`}>{item.field_path}</li>)}</ul>
      </details>
    </aside>
  );
}
