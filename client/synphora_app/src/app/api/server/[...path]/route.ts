import type { NextRequest } from "next/server";

const PASSTHROUGH_RESPONSE_HEADERS = [
  "content-type",
  "content-length",
  "cache-control",
  "etag",
  "last-modified",
];

function serverApiBase(): string {
  const raw = process.env.NEXT_PUBLIC_SERVER_API_URL?.trim();
  if (!raw) {
    throw new Error("NEXT_PUBLIC_SERVER_API_URL is not configured");
  }
  return raw.replace(/\/+$/, "");
}

function buildUpstreamHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  const apiKey = request.headers.get("x-api-key");
  if (apiKey) {
    headers.set("x-api-key", apiKey);
  }
  return headers;
}

function buildResponseHeaders(upstream: Response): Headers {
  const headers = new Headers();
  for (const key of PASSTHROUGH_RESPONSE_HEADERS) {
    const value = upstream.headers.get(key);
    if (value !== null) {
      headers.set(key, value);
    }
  }
  return headers;
}

async function proxyRequest(request: NextRequest, params: { path: string[] }) {
  const path = (params.path || []).join("/");
  const search = request.nextUrl.search || "";
  const routePath = request.nextUrl.pathname.replace(/^\/api\/server/, "");
  const normalizedPath = routePath || `/${path}`;
  const targetUrl = `${serverApiBase()}${normalizedPath}${search}`;

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? await request.text() : undefined;
  const requestHeaders = buildUpstreamHeaders(request);
  const doFetch = (url: string) =>
    fetch(url, {
      method: request.method,
      headers: requestHeaders,
      body,
      cache: "no-store",
      redirect: "manual",
    });

  let upstream: Response;
  try {
    upstream = await doFetch(targetUrl);

    if (upstream.status === 307 || upstream.status === 308) {
      const redirectTo = upstream.headers.get("location");
      if (redirectTo) {
        const redirectUrl = new URL(redirectTo, targetUrl).toString();
        upstream = await doFetch(redirectUrl);
      }
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
        detail: "Upstream server proxy request failed",
        error: error instanceof Error ? error.message : String(error),
        cause: causeMessage,
        code: causeCode,
      },
      { status: 502 }
    );
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: buildResponseHeaders(upstream),
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxyRequest(request, await context.params);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxyRequest(request, await context.params);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxyRequest(request, await context.params);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxyRequest(request, await context.params);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxyRequest(request, await context.params);
}
