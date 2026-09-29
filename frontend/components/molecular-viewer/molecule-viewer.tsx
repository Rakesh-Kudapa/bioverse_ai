"use client";

import type { GLViewer } from "3dmol";
import { useEffect, useRef, useState } from "react";

import { compoundStructureUrl, userFacingError } from "@/lib/api";
import { ErrorState, LoadingState } from "@/components/states/scientific-state";

type MoleculeStyle = "ball-stick" | "stick" | "sphere";

export function MoleculeViewer({ cid, name }: { cid: number; name: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<GLViewer | null>(null);
  const [style, setStyle] = useState<MoleculeStyle>("ball-stick");
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const container = containerRef.current;
    let viewer: GLViewer | null = null;
    let observer: ResizeObserver | null = null;
    let active = true;

    async function load() {
      if (!container) return;
      setState("loading");
      try {
        const [threeDmol, response] = await Promise.all([
          import("3dmol"),
          fetch(compoundStructureUrl(cid, "3d"), { signal: controller.signal }),
        ]);
        if (!response.ok) throw new Error("Structure response was unavailable.");
        const sdf = await response.text();
        if (!active || !sdf.trim()) return;

        viewer = threeDmol.createViewer(container, { backgroundColor: "#071019", antialias: true });
        viewer.addModel(sdf, "sdf");
        viewer.setStyle({}, { stick: { radius: 0.18 }, sphere: { scale: 0.28 } });
        viewer.zoomTo();
        viewer.render();
        viewerRef.current = viewer;
        observer = new ResizeObserver(() => viewer?.resize());
        observer.observe(container);
        setState("ready");
      } catch (loadError) {
        if (!active || controller.signal.aborted) return;
        setError(userFacingError(loadError, "A 3D conformer is not available from PubChem."));
        setState("error");
      }
    }

    void load();
    return () => {
      active = false;
      controller.abort();
      observer?.disconnect();
      viewer?.clear();
      viewerRef.current = null;
      if (container) container.replaceChildren();
    };
  }, [cid]);

  function applyStyle(nextStyle: MoleculeStyle) {
    const viewer = viewerRef.current;
    if (!viewer) return;
    setStyle(nextStyle);
    if (nextStyle === "stick") viewer.setStyle({}, { stick: { radius: 0.2 } });
    if (nextStyle === "sphere") viewer.setStyle({}, { sphere: { scale: 0.78 } });
    if (nextStyle === "ball-stick") {
      viewer.setStyle({}, { stick: { radius: 0.18 }, sphere: { scale: 0.28 } });
    }
    viewer.render();
  }

  return (
    <section className="viewer-panel" aria-label={`Interactive 3D structure of ${name}`}>
      <div className="viewer-toolbar">
        <div><span className="live-dot" aria-hidden="true" />Interactive 3D <small>PubChem SDF</small></div>
        <div className="segmented-control" aria-label="Molecule representation">
          {(["ball-stick", "stick", "sphere"] as const).map((item) => (
            <button key={item} type="button" aria-pressed={style === item} onClick={() => applyStyle(item)} disabled={state !== "ready"}>
              {item === "ball-stick" ? "Ball + stick" : item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}
          <button type="button" onClick={() => viewerRef.current?.zoomTo()} disabled={state !== "ready"}>Reset view</button>
        </div>
      </div>
      <div className="viewer-stage molecule-stage">
        <div ref={containerRef} className="viewer-canvas" data-testid="molecule-viewer-canvas" />
        {state === "loading" && <div className="viewer-overlay"><LoadingState title="Loading molecular structure..." detail="Preparing source coordinates for interactive viewing." /></div>}
        {state === "error" && <div className="viewer-overlay"><ErrorState title="3D structure unavailable" detail={error} /></div>}
      </div>
      <p className="viewer-help">Drag to rotate · Scroll or pinch to zoom · Visualization does not add scientific claims</p>
    </section>
  );
}
