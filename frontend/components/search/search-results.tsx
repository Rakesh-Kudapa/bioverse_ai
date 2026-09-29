"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { bioverseApi, userFacingError } from "@/lib/api";
import { formatResolution, joinOrUnavailable } from "@/lib/format";
import type { CompoundEntity, ProteinEntity } from "@/types/bioverse";
import { EmptyState, ErrorState, LoadingState } from "@/components/states/scientific-state";

interface SearchState {
  compounds: CompoundEntity[];
  proteins: ProteinEntity[];
  compoundError: string | null;
  proteinError: string | null;
}

export function SearchResults({ query }: { query: string }) {
  const [state, setState] = useState<SearchState | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    async function search() {
      const [compounds, proteins] = await Promise.allSettled([
        bioverseApi.searchCompounds(query, controller.signal),
        bioverseApi.searchProteins(query, controller.signal),
      ]);
      if (controller.signal.aborted) return;
      setState({
        compounds: compounds.status === "fulfilled" ? compounds.value.results : [],
        proteins: proteins.status === "fulfilled" ? proteins.value.results : [],
        compoundError: compounds.status === "rejected" ? userFacingError(compounds.reason, "Compound search is unavailable.") : null,
        proteinError: proteins.status === "rejected" ? userFacingError(proteins.reason, "Protein structure search is unavailable.") : null,
      });
    }
    void search();
    return () => controller.abort();
  }, [query, attempt]);

  if (!state) return <LoadingState title="Searching BioVerse..." detail="Checking PubChem compounds and experimental RCSB protein structures." />;
  const isEmpty = state.compounds.length === 0 && state.proteins.length === 0 && !state.compoundError && !state.proteinError;

  return (
    <div className="search-results" aria-live="polite">
      <div className="result-summary"><span>{state.compounds.length + state.proteins.length}</span> source-grounded results for <strong>“{query}”</strong></div>
      {isEmpty && <EmptyState title="No scientific records found" detail="No compound or experimental protein structure matched this exact search." />}

      <section className="result-section" aria-labelledby="compound-results-heading">
        <div className="section-heading"><div><p className="panel-kicker">PubChem</p><h2 id="compound-results-heading">Compounds</h2></div><span>{state.compounds.length}</span></div>
        {state.compoundError && <ErrorState title="Compound search unavailable" detail={state.compoundError} onRetry={() => setAttempt((value) => value + 1)} />}
        {!state.compoundError && state.compounds.length === 0 && <p className="inline-empty">No compound was found for this search.</p>}
        <div className="result-list">
          {state.compounds.map((compound) => (
            <Link className="result-row" href={`/compound/${compound.cid}`} key={compound.id}>
              <span className="entity-glyph compound-glyph" aria-hidden="true">⬡</span>
              <span className="result-primary"><strong>{compound.name ?? `PubChem compound ${compound.cid}`}</strong><small>Compound · PubChem CID {compound.cid}</small></span>
              <span className="result-facts"><span>{compound.molecular_formula ?? "Formula not reported"}</span><span>{compound.molecular_weight === null ? "Weight not reported" : `${compound.molecular_weight} g/mol`}</span></span>
              <span className="row-arrow" aria-hidden="true">→</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="result-section" aria-labelledby="protein-results-heading">
        <div className="section-heading"><div><p className="panel-kicker">RCSB PDB</p><h2 id="protein-results-heading">Protein structures</h2></div><span>{state.proteins.length}</span></div>
        <p className="section-note">Experimental polymer entities; source order does not indicate biological importance.</p>
        {state.proteinError && <ErrorState title="Protein search unavailable" detail={state.proteinError} onRetry={() => setAttempt((value) => value + 1)} />}
        {!state.proteinError && state.proteins.length === 0 && <p className="inline-empty">No experimental protein structure was found for this search.</p>}
        <div className="result-list">
          {state.proteins.map((protein) => {
            const structure = protein.associated_structures[0];
            return (
              <Link className="result-row" href={`/structure/${protein.pdb_id}`} key={protein.id}>
                <span className="entity-glyph protein-glyph" aria-hidden="true">∿</span>
                <span className="result-primary"><strong>{protein.name ?? protein.source_id}</strong><small>Protein entity · PDB {protein.pdb_id} · Entity {protein.entity_id}</small></span>
                <span className="result-facts"><span>{joinOrUnavailable(structure?.experimental_methods ?? [])}</span><span>{formatResolution(structure?.resolution_angstroms ?? null)}</span></span>
                <span className="row-arrow" aria-hidden="true">→</span>
              </Link>
            );
          })}
        </div>
        <Link className="secondary-link" href={`/protein/${encodeURIComponent(query)}`}>Open protein-only results →</Link>
      </section>
    </div>
  );
}
