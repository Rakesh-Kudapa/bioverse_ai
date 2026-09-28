const explorationTypes = ["Drugs", "Proteins", "Genes", "Diseases"] as const;

export default function Home() {
  return (
    <main className="landing-shell">
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />

      <nav className="navigation" aria-label="Primary navigation">
        <a className="brand" href="#top" aria-label="BioVerse AI home">
          <span className="brand-mark" aria-hidden="true">
            <span />
          </span>
          <span>BIOVERSE</span>
          <span className="brand-ai">AI</span>
        </a>
        <span className="milestone-label">Foundation preview</span>
      </nav>

      <section id="top" className="hero" aria-labelledby="hero-title">
        <div className="eyebrow">
          <span className="eyebrow-dot" aria-hidden="true" />
          Source-grounded biology exploration
        </div>

        <h1 id="hero-title">
          Explore life,
          <span> visually.</span>
        </h1>

        <p className="hero-copy">
          Move through the relationships that connect molecules, proteins, genes, and disease—with
          every biological fact traced to an approved scientific source.
        </p>

        <div className="search-shell" role="search" aria-label="BioVerse search preview">
          <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22">
            <path d="m21 21-4.35-4.35m2.35-5.15a7.5 7.5 0 1 1-15 0 7.5 7.5 0 0 1 15 0Z" />
          </svg>
          <label className="sr-only" htmlFor="bioverse-search">
            Search BioVerse
          </label>
          <input
            id="bioverse-search"
            type="search"
            placeholder="Search aspirin, EGFR, breast cancer..."
            disabled
          />
          <button type="button" disabled>
            Search coming soon
          </button>
        </div>

        <ul className="entity-list" aria-label="Planned exploration categories">
          {explorationTypes.map((type) => (
            <li key={type}>{type}</li>
          ))}
        </ul>
      </section>

      <aside className="visual-orbit" aria-hidden="true">
        <div className="orbit orbit-outer" />
        <div className="orbit orbit-inner" />
        <div className="orbital-node node-one" />
        <div className="orbital-node node-two" />
        <div className="orbital-node node-three" />
        <div className="core-sphere">
          <div />
        </div>
      </aside>

      <footer>
        Educational and research exploration only. Not medical advice.
      </footer>
    </main>
  );
}

