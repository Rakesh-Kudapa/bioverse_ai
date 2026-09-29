"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { bioverseApi, userFacingError } from "@/lib/api";
import { formatDate, formatResolution, joinOrUnavailable } from "@/lib/format";
import type { StructureEntity } from "@/types/bioverse";
import { ProvenancePanel } from "@/components/provenance/provenance-panel";
import { ErrorState, LoadingState } from "@/components/states/scientific-state";

const ProteinStructureViewer = dynamic(
  () => import("@/components/protein-viewer/protein-structure-viewer").then((module) => module.ProteinStructureViewer),
  { ssr: false, loading: () => <LoadingState title="Preparing Mol* viewer..." /> },
);

export function StructureExplorer({ pdbId }: { pdbId: string }) {
  const [structure, setStructure] = useState<StructureEntity | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    bioverseApi.getStructure(pdbId, controller.signal)
      .then(setStructure)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(userFacingError(reason, "This PDB structure was not found."));
      });
    return () => controller.abort();
  }, [pdbId, attempt]);

  if (error) return <ErrorState title="Structure unavailable" detail={error} onRetry={() => setAttempt((value) => value + 1)} />;
  if (!structure) return <LoadingState title="Loading structure metadata..." detail="Retrieving normalized RCSB structure facts and provenance." />;

  return (
    <div className="explorer-grid structure-explorer">
      <aside className="entity-sidebar structure-sidebar">
        <p className="entity-kind"><span aria-hidden="true">∿</span> Macromolecular structure</p>
        <h1>{structure.pdb_id}</h1>
        <p className="structure-title">{structure.title ?? "Title not reported"}</p>
        <dl className="property-list">
          <div><dt>Experimental method</dt><dd>{joinOrUnavailable(structure.experimental_methods)}</dd></div>
          <div><dt>Resolution</dt><dd>{formatResolution(structure.resolution_angstroms)}</dd></div>
          <div><dt>Release date</dt><dd>{formatDate(structure.release_date)}</dd></div>
          <div><dt>Polymer entities</dt><dd>{structure.polymer_entity_count ?? "Not reported"}</dd></div>
          <div><dt>Chains</dt><dd>{structure.chains.reduce((count, chain) => count + chain.auth_chain_ids.length, 0)}</dd></div>
          <div><dt>Ligands</dt><dd>{structure.ligands.length}</dd></div>
        </dl>
      </aside>

      <main className="visual-column">
        <ProteinStructureViewer pdbId={structure.pdb_id} ligandIds={structure.ligands.map((ligand) => ligand.chemical_component_id)} />
        <section className="detail-surface" aria-labelledby="ligands-heading">
          <div className="section-heading"><div><p className="panel-kicker">Source-reported non-polymers</p><h2 id="ligands-heading">Ligands</h2></div><span>{structure.ligands.length}</span></div>
          {structure.ligands.length === 0 ? (
            <p className="inline-empty">No bound non-polymer ligands were reported for this structure.</p>
          ) : (
            <div className="ligand-list">
              {structure.ligands.map((ligand) => (
                <article key={ligand.id}>
                  <strong>{ligand.chemical_component_id}</strong><span>{ligand.name ?? "Name not reported"}</span>
                  <dl><div><dt>Formula</dt><dd>{ligand.formula ?? "Not reported"}</dd></div><div><dt>Weight</dt><dd>{ligand.molecular_weight === null ? "Not reported" : `${ligand.molecular_weight} g/mol`}</dd></div><div><dt>Chains</dt><dd>{joinOrUnavailable(ligand.auth_chain_ids)}</dd></div></dl>
                </article>
              ))}
            </div>
          )}
          <p className="scientific-caveat">Ligand records describe structural occurrence only. BioVerse does not infer therapeutic role, function, or binding mechanism.</p>
        </section>
        <section className="detail-surface" aria-labelledby="polymer-heading">
          <div className="section-heading"><div><p className="panel-kicker">Structure hierarchy</p><h2 id="polymer-heading">Polymer entities and chains</h2></div></div>
          <div className="polymer-list">{structure.polymer_entities.map((entity) => <article key={entity.source_id}><strong>Entity {entity.entity_id}</strong><span>{entity.description ?? "Description not reported"}</span><small>Chains {joinOrUnavailable(entity.chains.auth_chain_ids)} · {entity.sequence_length === null ? "Length not reported" : `${entity.sequence_length} residues`}</small></article>)}</div>
        </section>
      </main>

      <ProvenancePanel source="rcsb_pdb" sourceId={structure.source_id} sourceUrl={structure.source_url} provenance={structure.provenance} />
    </div>
  );
}
