"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useEffect, useState } from "react";

import { compoundStructureUrl, bioverseApi, userFacingError } from "@/lib/api";
import { displayValue } from "@/lib/format";
import type { CompoundEntity } from "@/types/bioverse";
import { ProvenancePanel } from "@/components/provenance/provenance-panel";
import { ErrorState, LoadingState } from "@/components/states/scientific-state";

const MoleculeViewer = dynamic(
  () => import("@/components/molecular-viewer/molecule-viewer").then((module) => module.MoleculeViewer),
  { ssr: false, loading: () => <LoadingState title="Loading molecular viewer..." /> },
);

const primaryProperties = [
  ["Molecular formula", "molecular_formula"],
  ["Molecular weight", "molecular_weight"],
  ["XLogP", "xlogp"],
  ["Topological polar surface area", "tpsa"],
  ["H-bond donors", "hydrogen_bond_donor_count"],
  ["H-bond acceptors", "hydrogen_bond_acceptor_count"],
] as const;

export function CompoundExplorer({ cid }: { cid: number }) {
  const [compound, setCompound] = useState<CompoundEntity | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [imageState, setImageState] = useState<"loading" | "ready" | "error">("loading");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    bioverseApi.getCompound(cid, controller.signal)
      .then(setCompound)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(userFacingError(reason, "No compound was found for this identifier."));
      });
    return () => controller.abort();
  }, [cid, attempt]);

  if (error) return <ErrorState title="Compound unavailable" detail={error} onRetry={() => setAttempt((value) => value + 1)} />;
  if (!compound) return <LoadingState title="Loading compound record..." detail="Retrieving normalized PubChem properties and provenance." />;
  const name = compound.name ?? `PubChem compound ${compound.cid}`;

  return (
    <div className="explorer-grid compound-explorer">
      <aside className="entity-sidebar">
        <p className="entity-kind"><span aria-hidden="true">⬡</span> Compound</p>
        <h1>{name}</h1>
        <p className="entity-id">PubChem CID {compound.cid}</p>
        <div className="structure-2d">
          {imageState === "loading" && <span role="status">Loading 2D structure...</span>}
          {imageState === "error" ? (
            <div className="image-unavailable">2D structure is unavailable from PubChem.</div>
          ) : (
            <Image
              src={compoundStructureUrl(compound.cid, "2d")}
              alt={`PubChem 2D molecular structure for ${name}`}
              width={420}
              height={320}
              unoptimized
              onLoad={() => setImageState("ready")}
              onError={() => setImageState("error")}
              className={imageState === "ready" ? "is-ready" : ""}
            />
          )}
        </div>
        <dl className="property-list">
          {primaryProperties.map(([label, key]) => (
            <div key={key}><dt>{label}</dt><dd>{displayValue(compound[key])}{key === "molecular_weight" && compound[key] !== null ? " g/mol" : key === "tpsa" && compound[key] !== null ? " Å²" : ""}</dd></div>
          ))}
        </dl>
      </aside>

      <main className="visual-column">
        {compound.has_3d_conformer && compound.structure_3d ? (
          <MoleculeViewer cid={compound.cid} name={name} />
        ) : (
          <div className="viewer-panel viewer-unavailable"><ErrorState title="No 3D conformer" detail="A 3D conformer is not available from PubChem. The 2D structure and properties remain available." /></div>
        )}
        <section className="detail-surface" aria-labelledby="identifiers-heading">
          <div className="section-heading"><div><p className="panel-kicker">Scientific record</p><h2 id="identifiers-heading">Identifiers</h2></div></div>
          <dl className="identifier-list">
            <div><dt>Connectivity SMILES</dt><dd>{displayValue(compound.canonical_smiles)}</dd></div>
            <div><dt>Isomeric SMILES</dt><dd>{displayValue(compound.isomeric_smiles)}</dd></div>
            <div><dt>InChIKey</dt><dd>{displayValue(compound.inchikey)}</dd></div>
          </dl>
          <details className="advanced-fields"><summary>Show advanced identifier</summary><dl className="identifier-list"><div><dt>InChI</dt><dd>{displayValue(compound.inchi)}</dd></div></dl></details>
        </section>
      </main>

      <ProvenancePanel source="pubchem" sourceId={compound.source_id} sourceUrl={compound.source_url} provenance={compound.provenance} />
    </div>
  );
}
