import type { NextRequest } from "next/server";

const PASSTHROUGH_RESPONSE_HEADERS = [
  "content-type",
  "content-length",
  "accept-ranges",
  "content-range",
  "cache-control",
  "etag",
  "last-modified",
];

function audioStorageBase(): string {
  const raw = process.env.NEXT_PUBLIC_AUDIO_STORAGE_API_URL?.trim();
  if (!raw) {
    throw new Error("NEXT_PUBLIC_AUDIO_STORAGE_API_URL is not configured");
  }
  return raw.replace(/\/+$/, "");
}

function upstreamHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  const range = request.headers.get("range");
  if (range) {
    headers.set("range", range);
  }
  return headers;
}

function responseHeaders(upstream: Response): Headers {
  const headers = new Headers();
  for (const key of PASSTHROUGH_RESPONSE_HEADERS) {
    const value = upstream.headers.get(key);
    if (value !== null) {
      headers.set(key, value);
    }
  }
  return headers;
}

async function proxyAudio(request: NextRequest, fileName: string) {
  const safe = encodeURIComponent(fileName);
  const target = `${audioStorageBase()}/files/${safe}`;
  const method = request.method;

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method,
      headers: upstreamHeaders(request),
      cache: "no-store",
    });

    if (method === "HEAD" && upstream.status === 405) {
      upstream = await fetch(target, {
        method: "GET",
        headers: upstreamHeaders(request),
        cache: "no-store",
      });
    }
  } catch (error) {
    const cause = error instanceof Error && "cause" in error ? (error as Error & { cause?: unknown }).cause : undefined;
    const causeMessage =
      cause && typeof cause === "object" && "message" in cause
        ? String((cause as { message?: unknown }).message)
        : cause
          ? String(cause)
          : "";
    const causeCode =
      cause && typeof cause === "object" && "code" in cause ? String((cause as { code?: unknown }).code) : "";
    return Response.json(
      {
        detail: "Upstream audio proxy request failed",
        error: error instanceof Error ? error.message : String(error),
        cause: causeMessage,
        code: causeCode,
      },
      { status: 502 }
    );
  }

  return new Response(method === "HEAD" ? null : upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders(upstream),
  });
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ fileName: string }> }
) {
  const params = await context.params;
  return proxyAudio(request, params.fileName);
}

export async function HEAD(
  request: NextRequest,
  context: { params: Promise<{ fileName: string }> }
) {
  const params = await context.params;
  return proxyAudio(request, params.fileName);
}
