"use client";

import type { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import { useEffect, useRef, useState } from "react";

import { macromolecularStructureUrl } from "@/lib/api";
import { ErrorState, LoadingState } from "@/components/states/scientific-state";

export function ProteinStructureViewer({ pdbId, ligandIds }: { pdbId: string; ligandIds: string[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pluginRef = useRef<PluginUIContext | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const container = containerRef.current;
    let plugin: PluginUIContext | null = null;
    let observer: ResizeObserver | null = null;
    let active = true;

    async function load() {
      if (!container) return;
      setState("loading");
      try {
        const [{ createPluginUI }, { renderReact18 }, { DefaultPluginUISpec }, { PluginConfig }, { Color }] = await Promise.all([
          import("molstar/lib/mol-plugin-ui"),
          import("molstar/lib/mol-plugin-ui/react18"),
          import("molstar/lib/mol-plugin-ui/spec"),
          import("molstar/lib/mol-plugin/config"),
          import("molstar/lib/mol-util/color"),
        ]);
        if (!active) return;
        const defaultSpec = DefaultPluginUISpec();
        plugin = await createPluginUI({
          target: container,
          render: renderReact18,
          spec: {
            ...defaultSpec,
            layout: { initial: { isExpanded: false, showControls: false } },
            components: {
              ...defaultSpec.components,
              controls: { top: "none", bottom: "none", left: "none" },
              remoteState: "none",
            },
            config: [
              [PluginConfig.VolumeStreaming.Enabled, false],
              [PluginConfig.Viewport.ShowSettings, false],
              [PluginConfig.Viewport.ShowSelectionMode, false],
              [PluginConfig.Viewport.ShowAnimation, false],
              [PluginConfig.Viewport.ShowScreenshotControls, false],
              [PluginConfig.Viewport.ShowExpand, false],
              [PluginConfig.Viewport.ShowToggleFullscreen, false],
              [PluginConfig.Viewport.ShowReset, true],
            ],
          },
        });
        if (!active) {
          plugin.dispose();
          return;
        }
        pluginRef.current = plugin;
        plugin.canvas3d?.setProps({ renderer: { backgroundColor: Color(0x071019) } });
        const data = await plugin.builders.data.download(
          { url: macromolecularStructureUrl(pdbId), isBinary: false, label: `BioVerse ${pdbId}` },
          { state: { isGhost: true } },
        );
        const trajectory = await plugin.builders.structure.parseTrajectory(data, "mmcif");
        await plugin.builders.structure.hierarchy.applyPreset(trajectory, "default", {
          showUnitcell: false,
          representationPreset: "auto",
        });
        if (!active) return;
        observer = new ResizeObserver(() => plugin?.canvas3d?.handleResize());
        observer.observe(container);
        setState("ready");
      } catch (error) {
        console.error("Mol* structure load failed", error instanceof Error ? error.stack : error);
        if (active) setState("error");
      }
    }

    void load();
    return () => {
      active = false;
      observer?.disconnect();
      plugin?.dispose();
      pluginRef.current = null;
      if (container) container.replaceChildren();
    };
  }, [pdbId]);

  async function focusLigand(componentId: string) {
    const plugin = pluginRef.current;
    if (!plugin) return;
    const { applyStructureInteractivity } = await import("molstar/lib/extensions/plugin/interactivity");
    applyStructureInteractivity(plugin, { action: ["select", "focus"] });
    applyStructureInteractivity(plugin, {
      elements: { label_comp_id: componentId },
      action: ["select", "focus"],
      applyGranularity: true,
    });
  }

  return (
    <section className="viewer-panel protein-viewer-panel" aria-label={`Interactive protein structure ${pdbId}`}>
      <div className="viewer-toolbar">
        <div><span className="live-dot" aria-hidden="true" />Interactive structure <small>RCSB mmCIF</small></div>
        <button className="control-button" type="button" onClick={() => pluginRef.current?.managers.camera.reset()} disabled={state !== "ready"}>Reset camera</button>
      </div>
      <div className="viewer-stage protein-stage">
        <div ref={containerRef} className="viewer-canvas molstar-host" data-testid="protein-viewer-canvas" />
        {state === "loading" && <div className="viewer-overlay"><LoadingState title="Loading protein coordinates..." detail="Mol* is preparing the backend-delivered mmCIF structure." /></div>}
        {state === "error" && <div className="viewer-overlay"><ErrorState title="Structure file unavailable" detail="The protein coordinates could not be displayed. Metadata remains available below." /></div>}
      </div>
      {ligandIds.length > 0 && (
        <div className="viewer-ligand-controls" aria-label="Ligand focus controls">
          <span>Focus ligand</span>
          {ligandIds.map((ligandId) => <button key={ligandId} type="button" disabled={state !== "ready"} onClick={() => void focusLigand(ligandId)}>{ligandId}</button>)}
        </div>
      )}
      <p className="viewer-help">Drag to rotate · Scroll or pinch to zoom · Default macromolecular representation by Mol*</p>
    </section>
  );
}
