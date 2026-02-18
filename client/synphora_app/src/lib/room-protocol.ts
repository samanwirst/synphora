export type RoomRole = "creator" | "listener";
export type RoomControlAction = "play" | "pause" | "seek" | "set_rate" | "next" | "prev" | "set_track";

export type RoomTrack = {
  track_id: string;
  url: string;
};

export type RoomPlaybackState = {
  current_track_index: number;
  position_sec: number;
  is_playing: boolean;
  playback_rate: number;
  version: number;
  updated_at_ms: number;
};

export type RoomSnapshot = {
  room_id: string;
  playlist: RoomTrack[];
  state: RoomPlaybackState;
  is_active: boolean;
};

export type JoinRoomPayload = {
  roomId: string;
  controlToken?: string;
};

export type ControlPayload = {
  roomId: string;
  action: RoomControlAction;
  positionSec?: number;
  playbackRate?: number;
  trackIndex?: number;
};

export type SocketErrorPayload = {
  code: string;
  message: string;
};

export type JoinedRoomPayload = RoomSnapshot & {
  role: RoomRole;
};

export type ClientToServerEvents = {
  join_room: (payload: JoinRoomPayload) => void;
  control: (payload: ControlPayload) => void;
  request_snapshot: () => void;
};

export type ServerToClientEvents = {
  joined_room: (payload: JoinedRoomPayload) => void;
  room_state: (payload: RoomSnapshot) => void;
  socket_error: (payload: SocketErrorPayload) => void;
};
