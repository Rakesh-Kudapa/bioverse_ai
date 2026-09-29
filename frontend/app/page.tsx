import Link from "next/link";

import { AppFooter, AppHeader } from "@/components/shell/app-shell";
import { SearchForm } from "@/components/search/search-form";

const examples = [
  { label: "Aspirin", meta: "Compound · PubChem", href: "/compound/2244" },
  { label: "EGFR", meta: "Protein structures · RCSB", href: "/protein/EGFR" },
  { label: "Ibuprofen", meta: "Compound · PubChem", href: "/compound/3672" },
] as const;

export default function Home() {
  return (
    <main className="landing-shell">
      <AppHeader />
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-content">
          <p className="eyebrow"><span aria-hidden="true" />Source-grounded biology exploration</p>
          <h1 id="hero-title">Explore biology<br /><em>in three dimensions.</em></h1>
          <p className="hero-copy">Move from real molecules to experimental protein structures through an interface where every displayed scientific fact remains connected to its source.</p>
          <SearchForm />
          <div className="example-links" aria-label="Example explorations">
            <span>Start with</span>
            {examples.map((example) => <Link href={example.href} key={example.label}><strong>{example.label}</strong><small>{example.meta}</small></Link>)}
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="molecular-field"><i /><i /><i /><i /><i /><i /><b /><b /><b /><span /></div>
          <p>Visualize real source coordinates</p>
        </div>
      </section>
      <section className="capability-strip" aria-label="Current BioVerse capabilities">
        <div><span>01</span><strong>Compounds</strong><small>PubChem properties and conformers</small></div>
        <div><span>02</span><strong>Protein structures</strong><small>Experimental RCSB entries</small></div>
        <div><span>03</span><strong>Traceable facts</strong><small>Field-level provenance</small></div>
      </section>
      <AppFooter />
    </main>
  );
}
