import { existsSync, readFileSync } from "node:fs";
import { createServer as createHttpServer } from "node:http";
import { createServer as createHttpsServer } from "node:https";
import type { IncomingMessage, ServerResponse } from "node:http";
import { resolve } from "node:path";
import { loadEnvConfig } from "@next/env";
import { Server, Socket } from "socket.io";
import type {
  ClientToServerEvents,
  ControlPayload,
  JoinRoomPayload,
  JoinedRoomPayload,
  RoomRole,
  RoomSnapshot,
  ServerToClientEvents,
  SocketErrorPayload,
} from "./src/lib/room-protocol";

interface InterServerEvents {}

interface SocketData {
  roomId?: string;
  role?: RoomRole;
  controlToken?: string;
}

type SynphoraSocket = Socket<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>;

class ApiError extends Error {
  status: number;
  body: string;

  constructor(status: number, body: string) {
    super(`API error: ${status}`);
    this.status = status;
    this.body = body;
  }
}

loadEnvConfig(process.cwd());

const SERVER_API_URL = normalizeBaseUrl(process.env.NEXT_PUBLIC_SERVER_API_URL);
const SOCKET_PUBLIC_URL = normalizeBaseUrl(process.env.NEXT_PUBLIC_SOCKET_SERVER_URL);
const SOCKET_PORT = Number(process.env.SOCKET_PORT || "3001");
const SOCKET_CORS_ORIGIN = process.env.SOCKET_CORS_ORIGIN || "*";
const SOCKET_HTTPS_KEY_PATH = process.env.SOCKET_HTTPS_KEY_PATH || "./certificates/localhost-key.pem";
const SOCKET_HTTPS_CERT_PATH = process.env.SOCKET_HTTPS_CERT_PATH || "./certificates/localhost.pem";

if (!SERVER_API_URL) {
  throw new Error("NEXT_PUBLIC_SERVER_API_URL is required");
}

if (!SOCKET_PUBLIC_URL) {
  throw new Error("NEXT_PUBLIC_SOCKET_SERVER_URL is required");
}

if (!Number.isInteger(SOCKET_PORT) || SOCKET_PORT <= 0) {
  throw new Error(`Invalid SOCKET_PORT value: ${process.env.SOCKET_PORT}`);
}

function normalizeBaseUrl(raw: string | undefined): string {
  if (!raw) return "";
  return raw.trim().replace(/\/+$/, "");
}

function emitSocketError(socket: SynphoraSocket, payload: SocketErrorPayload) {
  socket.emit("socket_error", payload);
}

async function requestJson<T>(method: "GET" | "POST", path: string, payload?: unknown): Promise<T> {
  const response = await fetch(`${SERVER_API_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: payload !== undefined ? JSON.stringify(payload) : undefined,
  });

  const bodyText = await response.text();
  if (!response.ok) {
    throw new ApiError(response.status, bodyText);
  }

  if (!bodyText) {
    throw new ApiError(response.status, "Server returned empty response body");
  }

  try {
    return JSON.parse(bodyText) as T;
  } catch {
    throw new ApiError(response.status, "Server returned invalid JSON");
  }
}

function asCleanString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function usesHttps(url: string): boolean {
  return /^https:\/\//i.test(url);
}

const shouldUseHttps = usesHttps(SOCKET_PUBLIC_URL);

const requestHandler = (_req: IncomingMessage, res: ServerResponse) => {
  res.statusCode = 200;
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.end("Synphora Socket.IO server is running");
};

const httpServer = shouldUseHttps
  ? (() => {
      const keyPath = resolve(process.cwd(), SOCKET_HTTPS_KEY_PATH);
      const certPath = resolve(process.cwd(), SOCKET_HTTPS_CERT_PATH);

      if (!existsSync(keyPath) || !existsSync(certPath)) {
        throw new Error(
          `HTTPS is required for socket (${SOCKET_PUBLIC_URL}), but certificate files are missing: key=${keyPath}, cert=${certPath}`
        );
      }

      return createHttpsServer(
        {
          key: readFileSync(keyPath),
          cert: readFileSync(certPath),
        },
        requestHandler
      );
    })()
  : createHttpServer(requestHandler);

const io = new Server<ClientToServerEvents, ServerToClientEvents, InterServerEvents, SocketData>(httpServer, {
  cors: {
    origin: SOCKET_CORS_ORIGIN,
    methods: ["GET", "POST"],
  },
});

io.on("connection", (socket) => {
  socket.data.role = "listener";

  socket.on("join_room", async (rawPayload: JoinRoomPayload) => {
    const roomId = asCleanString(rawPayload?.roomId);
    const controlToken = asCleanString(rawPayload?.controlToken);

    if (!roomId) {
      emitSocketError(socket, { code: "invalid_room_id", message: "roomId is required" });
      return;
    }

    try {
      const auth = await requestJson<JoinedRoomPayload>("POST", `/rooms/${encodeURIComponent(roomId)}/socket-auth`, {
        control_token: controlToken || null,
      });

      socket.join(roomId);
      socket.data.roomId = roomId;
      socket.data.role = auth.role;
      socket.data.controlToken = auth.role === "creator" ? controlToken : undefined;

      socket.emit("joined_room", auth);
    } catch (e) {
      if (e instanceof ApiError) {
        emitSocketError(socket, {
          code: "join_failed",
          message: `Failed to join room (${e.status})`,
        });
        return;
      }
      emitSocketError(socket, { code: "join_failed", message: "Unexpected join error" });
    }
  });

  socket.on("request_snapshot", async () => {
    const roomId = socket.data.roomId;
    if (!roomId) {
      emitSocketError(socket, {
        code: "room_not_joined",
        message: "Join a room before requesting snapshot",
      });
      return;
    }

    try {
      const snapshot = await requestJson<RoomSnapshot>("GET", `/rooms/${encodeURIComponent(roomId)}`);
      socket.emit("room_state", snapshot);
    } catch {
      emitSocketError(socket, { code: "snapshot_failed", message: "Failed to load room snapshot" });
    }
  });

  socket.on("control", async (rawPayload: ControlPayload) => {
    const roomId = socket.data.roomId;
    const role = socket.data.role;
    const controlToken = socket.data.controlToken;

    if (!roomId) {
      emitSocketError(socket, { code: "room_not_joined", message: "Join a room before sending controls" });
      return;
    }

    if (!rawPayload || asCleanString(rawPayload.roomId) !== roomId) {
      emitSocketError(socket, {
        code: "invalid_room_context",
        message: "Control payload roomId mismatch",
      });
      return;
    }

    if (role !== "creator" || !controlToken) {
      emitSocketError(socket, {
        code: "method_not_allowed",
        message: "Method Not Allowed for listeners",
      });
      return;
    }

    try {
      const updatedState = await requestJson<RoomSnapshot>("POST", `/rooms/${encodeURIComponent(roomId)}/control`, {
        control_token: controlToken,
        action: rawPayload.action,
        position_sec: rawPayload.positionSec,
        playback_rate: rawPayload.playbackRate,
        track_index: rawPayload.trackIndex,
      });
      io.to(roomId).emit("room_state", updatedState);
    } catch (e) {
      if (e instanceof ApiError && e.status === 405) {
        emitSocketError(socket, {
          code: "method_not_allowed",
          message: "Method Not Allowed for listeners",
        });
        return;
      }
      emitSocketError(socket, {
        code: "control_failed",
        message: "Failed to apply control command",
      });
    }
  });
});

httpServer.listen(SOCKET_PORT, () => {
  const protocol = shouldUseHttps ? "https" : "http";
  console.log(`Socket.IO server started on ${protocol}://127.0.0.1:${SOCKET_PORT}`);
});
