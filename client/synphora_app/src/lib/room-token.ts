const CONTROL_TOKEN_KEY_PREFIX = "synphora_room_control_token_";

export function tokenStorageKey(roomId: string): string {
  return `${CONTROL_TOKEN_KEY_PREFIX}${roomId}`;
}
