import type {
  CompoundEntity,
  CompoundSearchResponse,
  ErrorResponse,
  ProteinSearchResponse,
  StructureEntity,
} from "@/types/bioverse";

const API_PREFIX = "/bioverse-api";

export class BioVerseApiError extends Error {
  readonly code: string;
  readonly source: string | null;
  readonly retryable: boolean;
  readonly status: number;

  constructor(detail: ErrorResponse["error"], status: number) {
    super(detail.message);
    this.name = "BioVerseApiError";
    this.code = detail.code;
    this.source = detail.source;
    this.retryable = detail.retryable;
    this.status = status;
  }
}

function apiUrl(path: string): string {
  if (!path.startsWith("/api/v1/")) {
    throw new Error("BioVerse API paths must start with /api/v1/.");
  }
  return `${API_PREFIX}${path}`;
}

async function requestJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(apiUrl(path), {
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    let detail: ErrorResponse["error"] = {
      code: "SOURCE_UNAVAILABLE",
      message: "BioVerse could not load this scientific record.",
      source: null,
      retryable: response.status >= 500,
    };
    try {
      const payload = (await response.json()) as Partial<ErrorResponse>;
      if (payload.error?.code && payload.error.message) detail = payload.error;
    } catch {
      // Keep the safe local failure. Raw upstream or proxy content is never rendered.
    }
    throw new BioVerseApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export const bioverseApi = {
  searchCompounds(query: string, signal?: AbortSignal) {
    return requestJson<CompoundSearchResponse>(
      `/api/v1/compounds/search?q=${encodeURIComponent(query)}`,
      signal,
    );
  },

  getCompound(cid: number, signal?: AbortSignal) {
    return requestJson<CompoundEntity>(`/api/v1/compounds/${cid}`, signal);
  },

  searchProteins(query: string, signal?: AbortSignal) {
    return requestJson<ProteinSearchResponse>(
      `/api/v1/proteins/search?q=${encodeURIComponent(query)}`,
      signal,
    );
  },

  getStructure(pdbId: string, signal?: AbortSignal) {
    return requestJson<StructureEntity>(
      `/api/v1/structures/${encodeURIComponent(pdbId)}`,
      signal,
    );
  },
};

export function compoundStructureUrl(cid: number, dimension: "2d" | "3d"): string {
  return apiUrl(`/api/v1/compounds/${cid}/structure/${dimension}`);
}

export function macromolecularStructureUrl(pdbId: string): string {
  return apiUrl(`/api/v1/structures/${encodeURIComponent(pdbId)}/file`);
}

export function userFacingError(error: unknown, fallback: string): string {
  if (error instanceof BioVerseApiError) {
    if (error.code === "ENTITY_NOT_FOUND") return fallback;
    if (error.code === "STRUCTURE_NOT_AVAILABLE") {
      return "The requested structure is not available from the current source.";
    }
    if (error.retryable) return "Scientific source data is temporarily unavailable. Please try again.";
    return error.message;
  }
  return fallback;
}
