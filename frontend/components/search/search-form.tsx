"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export function SearchForm({ initialQuery = "", compact = false }: { initialQuery?: string; compact?: boolean }) {
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = query.trim();
    if (normalized) router.push(`/explore?q=${encodeURIComponent(normalized)}`);
  }

  return (
    <form className={compact ? "search-form compact" : "search-form"} role="search" onSubmit={submit}>
      <label className="sr-only" htmlFor={compact ? "header-search" : "bioverse-search"}>Search BioVerse</label>
      <span className="search-icon" aria-hidden="true">⌕</span>
      <input
        id={compact ? "header-search" : "bioverse-search"}
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search aspirin, EGFR, hemoglobin..."
        minLength={1}
        maxLength={200}
        required
      />
      <button type="submit">Explore <span aria-hidden="true">→</span></button>
    </form>
  );
}
