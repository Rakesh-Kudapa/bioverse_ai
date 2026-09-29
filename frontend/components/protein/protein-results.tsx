"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { bioverseApi, userFacingError } from "@/lib/api";
import { formatResolution, joinOrUnavailable } from "@/lib/format";
import type { ProteinEntity } from "@/types/bioverse";
import { EmptyState, ErrorState, LoadingState } from "@/components/states/scientific-state";

export function ProteinResults({ query }: { query: string }) {
  const [results, setResults] = useState<ProteinEntity[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    bioverseApi.searchProteins(query, controller.signal)
      .then((response) => setResults(response.results))
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) setError(userFacingError(reason, "No protein structure was found for this search."));
      });
    return () => controller.abort();
  }, [query, attempt]);

  if (error) return <ErrorState title="Protein structure data unavailable" detail={error} onRetry={() => setAttempt((value) => value + 1)} />;
  if (!results) return <LoadingState title="Searching experimental protein structures..." detail="Retrieving source-reported RCSB polymer entities." />;
  if (results.length === 0) return <EmptyState title="No protein structures found" detail="No experimental RCSB polymer entity matched this search." />;

  return (
    <div className="protein-results-grid">
      {results.map((protein) => {
        const structure = protein.associated_structures[0];
        return (
          <article className="protein-result-card" key={protein.id}>
            <div className="protein-card-heading"><span>{protein.pdb_id}</span><small>Entity {protein.entity_id}</small></div>
            <p className="entity-kind">RCSB polymer entity</p>
            <h2>{protein.name ?? protein.source_id}</h2>
            <p className="protein-title">{structure?.title ?? "Structure title not reported"}</p>
            <dl>
              <div><dt>Method</dt><dd>{joinOrUnavailable(structure?.experimental_methods ?? [])}</dd></div>
              <div><dt>Resolution</dt><dd>{formatResolution(structure?.resolution_angstroms ?? null)}</dd></div>
              <div><dt>Chains</dt><dd>{joinOrUnavailable(protein.auth_chain_ids)}</dd></div>
              <div><dt>Organism</dt><dd>{joinOrUnavailable(protein.source_organisms)}</dd></div>
            </dl>
            <Link href={`/structure/${protein.pdb_id}`}>Explore structure <span aria-hidden="true">→</span></Link>
          </article>
        );
      })}
    </div>
  );
}
