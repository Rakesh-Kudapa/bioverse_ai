import Link from "next/link";
import type { ReactNode } from "react";

export function Brand() {
  return (
    <Link className="brand" href="/" aria-label="BioVerse AI home">
      <span className="brand-mark" aria-hidden="true"><span /></span>
      <span>BIOVERSE</span><span className="brand-ai">AI</span>
    </Link>
  );
}

export function AppHeader({ children }: { children?: ReactNode }) {
  return (
    <header className="app-header">
      <Brand />
      {children}
      <span className="source-status"><span aria-hidden="true" /> Source grounded</span>
    </header>
  );
}

export function AppFooter() {
  return (
    <footer className="app-footer">
      <span>BioVerse is an educational and research exploration tool.</span>
      <span>Public scientific data · Not medical advice</span>
    </footer>
  );
}
