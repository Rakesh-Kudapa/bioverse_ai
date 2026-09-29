import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MoleculeViewer } from "@/components/molecular-viewer/molecule-viewer";
import { ProteinStructureViewer } from "@/components/protein-viewer/protein-structure-viewer";

const moleculeViewer = {
  addModel: vi.fn(), setStyle: vi.fn(), zoomTo: vi.fn(), render: vi.fn(), resize: vi.fn(), clear: vi.fn(),
};
vi.mock("3dmol", () => ({ createViewer: vi.fn(() => moleculeViewer) }));

const dispose = vi.fn();
const applyPreset = vi.fn().mockResolvedValue(undefined);
const plugin = {
  dispose,
  canvas3d: { setProps: vi.fn(), handleResize: vi.fn() },
  builders: {
    data: { download: vi.fn().mockResolvedValue({}) },
    structure: { parseTrajectory: vi.fn().mockResolvedValue({}), hierarchy: { applyPreset } },
  },
  managers: { camera: { reset: vi.fn() } },
};
const interactivity = vi.fn();
vi.mock("molstar/lib/mol-plugin-ui", () => ({ createPluginUI: vi.fn().mockResolvedValue(plugin) }));
vi.mock("molstar/lib/mol-plugin-ui/react18", () => ({ renderReact18: vi.fn() }));
vi.mock("molstar/lib/mol-plugin-ui/spec", () => ({ DefaultPluginUISpec: () => ({ components: {}, config: [] }) }));
vi.mock("molstar/lib/mol-plugin/config", () => ({ PluginConfig: { VolumeStreaming: { Enabled: "volume" }, Viewport: { ShowSettings: "settings", ShowSelectionMode: "selection", ShowAnimation: "animation", ShowScreenshotControls: "screenshot", ShowExpand: "expand", ShowToggleFullscreen: "fullscreen", ShowReset: "reset" } } }));
vi.mock("molstar/lib/mol-util/color", () => ({ Color: (value: number) => value }));
vi.mock("molstar/lib/extensions/plugin/interactivity", () => ({ applyStructureInteractivity: interactivity }));

class ResizeObserverMock {
  observe = vi.fn();
  disconnect = vi.fn();
}

describe("viewer lifecycle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("ResizeObserver", ResizeObserverMock);
  });

  it("clears 3Dmol state when the molecule viewer unmounts", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => "aspirin sdf" }));
    const view = render(<MoleculeViewer cid={2244} name="Aspirin" />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Reset view" })).toBeEnabled());
    view.unmount();
    expect(moleculeViewer.clear).toHaveBeenCalledOnce();
  });

  it("disposes Mol*, supports source-ID ligand focus, and avoids WebGL in tests", async () => {
    const view = render(<ProteinStructureViewer pdbId="1M17" ligandIds={["AQ4"]} />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Reset camera" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "AQ4" }));
    await waitFor(() => expect(interactivity).toHaveBeenCalledTimes(2));
    expect(applyPreset).toHaveBeenCalled();
    view.unmount();
    expect(dispose).toHaveBeenCalledOnce();
  });
});
