import type { NextRequest } from "next/server";

const forwardedHeaders = ["content-type", "content-disposition", "cache-control"] as const;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const segments = (await params).path;
  if (segments.length < 3 || segments[0] !== "api" || segments[1] !== "v1") {
    return Response.json({ error: { code: "ENTITY_NOT_FOUND", message: "Unknown BioVerse API path.", source: null, retryable: false } }, { status: 404 });
  }

  const backendBaseUrl = process.env.BIOVERSE_API_BASE_URL ?? "http://localhost:8000";
  const target = new URL(segments.map(encodeURIComponent).join("/"), `${backendBaseUrl.replace(/\/$/, "")}/`);
  target.search = request.nextUrl.search;

  try {
    const upstream = await fetch(target, {
      headers: { Accept: request.headers.get("accept") ?? "*/*" },
      cache: "no-store",
      signal: request.signal,
    });
    const headers = new Headers();
    for (const name of forwardedHeaders) {
      const value = upstream.headers.get(name);
      if (value) headers.set(name, value);
    }
    return new Response(upstream.body, { status: upstream.status, headers });
  } catch {
    return Response.json(
      { error: { code: "SOURCE_UNAVAILABLE", message: "The BioVerse API is temporarily unavailable.", source: null, retryable: true } },
      { status: 503 },
    );
  }
}
