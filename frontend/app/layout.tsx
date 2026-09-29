import type { Metadata } from "next";
import type { ReactNode } from "react";

import "molstar/build/viewer/molstar.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "BioVerse AI",
  description: "Explore real compounds and protein structures in three dimensions.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
