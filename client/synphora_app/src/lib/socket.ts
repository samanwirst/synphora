"use client";

import { io, type Socket } from "socket.io-client";
import type {
  ClientToServerEvents,
  ControlPayload,
  JoinedRoomPayload,
  JoinRoomPayload,
  RoomControlAction,
  RoomPlaybackState,
  RoomRole,
  RoomSnapshot,
  RoomTrack,
  ServerToClientEvents,
  SocketErrorPayload,
} from "@/lib/room-protocol";

export type {
  ClientToServerEvents,
  ControlPayload,
  JoinedRoomPayload,
  JoinRoomPayload,
  RoomControlAction,
  RoomPlaybackState,
  RoomRole,
  RoomSnapshot,
  RoomTrack,
  ServerToClientEvents,
  SocketErrorPayload,
};

export type RoomSocket = Socket<ServerToClientEvents, ClientToServerEvents>;

function socketServerUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SOCKET_SERVER_URL?.trim();
  if (!raw) {
    throw new Error("NEXT_PUBLIC_SOCKET_SERVER_URL is not configured");
  }
  return raw.replace(/\/+$/, "");
}

export function createRoomSocket(): RoomSocket {
  return io(socketServerUrl(), {
    transports: ["websocket", "polling"],
  });
}
