import type { RoomSnapshot } from "@/lib/socket";

export type RoomPinAuthResponse = {
  room_id: string;
  control_token: string;
};

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function requestJson<T>(method: "GET" | "POST", path: string, payload?: unknown): Promise<T> {
  const response = await fetch(`/api/server${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: payload !== undefined ? JSON.stringify(payload) : undefined,
    cache: "no-store",
  });

  const bodyText = await response.text();
  if (!response.ok) {
    let detail = bodyText || `HTTP ${response.status}`;
    try {
      const parsed = JSON.parse(bodyText);
      if (typeof parsed?.detail === "string") {
        detail = parsed.detail;
      }
    } catch {
      // keep raw detail
    }
    throw new ApiError(response.status, detail);
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

export async function getRoomSnapshot(roomId: string): Promise<RoomSnapshot> {
  return requestJson<RoomSnapshot>("GET", `/rooms/${encodeURIComponent(roomId)}`);
}

export async function authRoomByPin(
  roomId: string,
  pinCode: string,
  initData: string
): Promise<RoomPinAuthResponse> {
  return requestJson<RoomPinAuthResponse>("POST", `/rooms/${encodeURIComponent(roomId)}/auth-pin`, {
    pin_code: pinCode,
    init_data: initData,
  });
}

export function isApiError(error: unknown): error is ApiError {
  if (error instanceof ApiError) {
    return true;
  }
  if (!error || typeof error !== "object") {
    return false;
  }

  const candidate = error as { status?: unknown; message?: unknown };
  return typeof candidate.status === "number" && typeof candidate.message === "string";
}
