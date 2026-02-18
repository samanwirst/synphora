"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";
import AudioPlayer from "react-h5-audio-player";
import {
  Button,
  List,
  Placeholder,
  Section,
  SegmentedControl,
} from "@telegram-apps/telegram-ui";

import { getRoomSnapshot, isApiError } from "@/lib/api";
import { impact } from "@/lib/haptics";
import { routeParamToString } from "@/lib/route-params";
import { tokenStorageKey } from "@/lib/room-token";
import {
  createRoomSocket,
  type ControlPayload,
  type RoomRole,
  type RoomSnapshot,
  type RoomSocket,
} from "@/lib/socket";
import styles from "./room-ui.module.css";

const RATE_OPTIONS = [1, 1.25, 1.5] as const;

function suppressForWindow(
  flagRef: MutableRefObject<boolean>,
  timerRef: MutableRefObject<number | null>,
  windowMs = 240
) {
  flagRef.current = true;
  if (timerRef.current !== null) {
    window.clearTimeout(timerRef.current);
  }
  timerRef.current = window.setTimeout(() => {
    flagRef.current = false;
    timerRef.current = null;
  }, windowMs);
}

export default function RoomPage() {
  const params = useParams<{ roomId: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();

  const roomId = useMemo(() => {
    return routeParamToString(params?.roomId);
  }, [params]);

  const isListenerMode = searchParams.get("listener") === "true";

  const socketRef = useRef<RoomSocket | null>(null);
  const playerRef = useRef<AudioPlayer | null>(null);
  const suppressControlEventsRef = useRef(false);
  const suppressControlTimerRef = useRef<number | null>(null);
  const loadedTrackIdRef = useRef<string | null>(null);

  const [snapshot, setSnapshot] = useState<RoomSnapshot | null>(null);
  const [role, setRole] = useState<RoomRole | null>(null);
  const [controlToken, setControlToken] = useState<string | null>(null);
  const [joinState, setJoinState] = useState<"idle" | "connecting" | "joined">("idle");
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [audioBlocked, setAudioBlocked] = useState(false);

  const currentTrack = useMemo(() => {
    if (!snapshot) return null;
    return snapshot.playlist[snapshot.state.current_track_index] || null;
  }, [snapshot]);

  const canControl = role === "creator";

  const playerAudio = useCallback(() => {
    return playerRef.current?.audio.current ?? null;
  }, []);

  const joinRoom = useCallback(
    (token?: string) => {
      if (!roomId) return;

      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }

      const socket = createRoomSocket();
      socketRef.current = socket;
      setJoinState("connecting");
      setActionError(null);

      socket.on("connect", () => {
        socket.emit("join_room", {
          roomId,
          controlToken: token,
        });
      });

      socket.on("joined_room", (payload) => {
        setSnapshot(payload);
        setRole(payload.role);
        setJoinState("joined");
        setError(null);
      });

      socket.on("room_state", (payload) => {
        setSnapshot(payload);
      });

      socket.on("socket_error", (payload) => {
        if (payload.code === "method_not_allowed") {
          setActionError(payload.message);
        } else {
          setJoinState("idle");
          setError(payload.message);
        }
      });
    },
    [roomId]
  );

  const emitControl = useCallback(
    (payload: Omit<ControlPayload, "roomId">) => {
      const socket = socketRef.current;
      if (!socket || role !== "creator") {
        setActionError("Method Not Allowed for listeners");
        return;
      }

      setActionError(null);
      socket.emit("control", {
        roomId,
        ...payload,
      });
    },
    [roomId, role]
  );

  useEffect(() => {
    if (!roomId) return;

    let cancelled = false;
    getRoomSnapshot(roomId)
      .then((payload) => {
        if (!cancelled) {
          setSnapshot(payload);
          setError(null);
        }
      })
      .catch((e) => {
        if (cancelled) return;
        if (isApiError(e)) {
          setError(e.message);
        } else {
          setError("Failed to load room.");
        }
      });

    const storedToken = localStorage.getItem(tokenStorageKey(roomId));
    setControlToken(storedToken);

    return () => {
      cancelled = true;
    };
  }, [roomId]);

  useEffect(() => {
    if (!roomId || isListenerMode) return;
    if (!controlToken) {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
      setRole(null);
      setJoinState("idle");
      return;
    }
    joinRoom(controlToken);
  }, [roomId, isListenerMode, controlToken, joinRoom]);

  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
      if (suppressControlTimerRef.current !== null) {
        window.clearTimeout(suppressControlTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!snapshot || !currentTrack) return;
    const audio = playerAudio();
    if (!audio) return;

    suppressForWindow(suppressControlEventsRef, suppressControlTimerRef);

    const isTrackChanged = loadedTrackIdRef.current !== currentTrack.track_id;
    if (isTrackChanged) {
      audio.src = currentTrack.url;
      audio.load();
      loadedTrackIdRef.current = currentTrack.track_id;
    }

    if (Math.abs(audio.playbackRate - snapshot.state.playback_rate) > 0.01) {
      audio.playbackRate = snapshot.state.playback_rate;
    }

    if (Math.abs(audio.currentTime - snapshot.state.position_sec) > 1.0) {
      try {
        audio.currentTime = snapshot.state.position_sec;
      } catch {
        // ignore seek errors while source is not fully loaded
      }
    }

    if (snapshot.state.is_playing) {
      void audio
        .play()
        .then(() => {
          setAudioBlocked(false);
        })
        .catch((err) => {
          if (err instanceof DOMException && err.name === "AbortError") {
            return;
          }
          setAudioBlocked(true);
        });
    } else {
      audio.pause();
    }
  }, [currentTrack, playerAudio, snapshot]);

  const sendCreatorControl = useCallback(
    (payload: Omit<ControlPayload, "roomId">) => {
      if (!canControl) return;
      if (suppressControlEventsRef.current) return;
      impact("light");
      emitControl(payload);
    },
    [canControl, emitControl]
  );

  const handlePlay = useCallback(() => {
    const audio = playerAudio();
    sendCreatorControl({
      action: "play",
      positionSec: audio?.currentTime ?? undefined,
    });
  }, [playerAudio, sendCreatorControl]);

  const handlePause = useCallback(() => {
    const audio = playerAudio();
    sendCreatorControl({
      action: "pause",
      positionSec: audio?.currentTime ?? undefined,
    });
  }, [playerAudio, sendCreatorControl]);

  const handleSeeked = useCallback(() => {
    const audio = playerAudio();
    sendCreatorControl({
      action: "seek",
      positionSec: audio?.currentTime ?? undefined,
    });
  }, [playerAudio, sendCreatorControl]);

  const handleNext = useCallback(() => {
    sendCreatorControl({ action: "next" });
  }, [sendCreatorControl]);

  const handlePrev = useCallback(() => {
    sendCreatorControl({ action: "prev" });
  }, [sendCreatorControl]);

  const handleEnded = useCallback(() => {
    sendCreatorControl({ action: "next" });
  }, [sendCreatorControl]);

  const activeRate = snapshot?.state.playback_rate ?? 1;

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <section className={styles.hero}>
          <h1 className={styles.title}>Room</h1>
        </section>

        <List className={styles.list}>
          {error && (
            <Section>
              <Placeholder header="Room error" description={error} />
            </Section>
          )}

          {isListenerMode && joinState !== "joined" && (
            <Section>
              <Button
                onClick={() => {
                  impact("medium");
                  joinRoom();
                }}
                loading={joinState === "connecting"}
                stretched
                mode="filled"
              >
                Join
              </Button>
            </Section>
          )}

          {!isListenerMode && !controlToken && (
            <Section>
              <Button
                onClick={() => {
                  impact("light");
                  router.push(`/room/${roomId}/auth`);
                }}
                stretched
                mode="filled"
              >
                Authenticate
              </Button>
            </Section>
          )}

          {!isListenerMode && controlToken && joinState !== "joined" && (
            <Section>
              <Button
                onClick={() => {
                  impact("medium");
                  joinRoom(controlToken);
                }}
                loading={joinState === "connecting"}
                stretched
                mode="filled"
              >
                Connect
              </Button>
            </Section>
          )}

          <Section>
            <div className={styles.playerPanel}>
              <div className={styles.trackRow}>
                <div className={styles.trackPrimary}>
                  {currentTrack ? `${snapshot ? snapshot.state.current_track_index + 1 : "-"} / ${snapshot?.playlist.length ?? "-"}` : "No tracks"}
                </div>
              </div>

              <div className={`${styles.readyPlayer} ${canControl ? "" : styles.lockedPlayer}`}>
                <AudioPlayer
                  ref={playerRef}
                  src={currentTrack?.url}
                  autoPlay={false}
                  autoPlayAfterSrcChange={false}
                  showSkipControls
                  showJumpControls={false}
                  customAdditionalControls={[]}
                  customVolumeControls={[]}
                  hasDefaultKeyBindings={false}
                  onPlay={handlePlay}
                  onPause={handlePause}
                  onSeeked={handleSeeked}
                  onClickNext={handleNext}
                  onClickPrevious={handlePrev}
                  onEnded={handleEnded}
                  onPlayError={() => {
                    setAudioBlocked(true);
                  }}
                />
              </div>

              <div className={styles.speedRow}>
                <SegmentedControl>
                  {RATE_OPTIONS.map((rate) => (
                    <SegmentedControl.Item
                      key={rate}
                      selected={Math.abs(activeRate - rate) < 0.01}
                      onClick={() => {
                        sendCreatorControl({ action: "set_rate", playbackRate: rate });
                      }}
                      disabled={!canControl}
                    >
                      {rate}x
                    </SegmentedControl.Item>
                  ))}
                </SegmentedControl>
              </div>

              {audioBlocked && (
                <Button
                  mode="outline"
                  onClick={() => {
                    const audio = playerAudio();
                    if (!audio) return;
                    void audio
                      .play()
                      .then(() => {
                        setAudioBlocked(false);
                      })
                      .catch(() => {
                        setAudioBlocked(true);
                      });
                  }}
                >
                  Enable audio
                </Button>
              )}

              {actionError && <span className={styles.errorText}>{actionError}</span>}
            </div>
          </Section>

          <Section>
            <Button
              mode="plain"
              stretched
              onClick={() => {
                impact("light");
                router.push("/");
              }}
            >
              Close
            </Button>
          </Section>
        </List>
      </div>
    </main>
  );
}
