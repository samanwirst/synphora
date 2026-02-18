"use client";

import { useParams, useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { Button, Input, List, Section } from "@telegram-apps/telegram-ui";

import { authRoomByPin, isApiError } from "@/lib/api";
import { impact } from "@/lib/haptics";
import { routeParamToString } from "@/lib/route-params";
import { tokenStorageKey } from "@/lib/room-token";
import styles from "../room-ui.module.css";

export default function RoomAuthPage() {
  const params = useParams<{ roomId: string }>();
  const router = useRouter();

  const roomId = useMemo(() => {
    return routeParamToString(params?.roomId);
  }, [params]);

  const [pinCode, setPinCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authenticate = async () => {
    if (roomId === "") return;
    if (!/^\d{6}$/.test(pinCode.trim())) {
      setError("PIN must be 6 digits.");
      return;
    }

    const initData = window.Telegram?.WebApp?.initData || "";
    if (!initData) {
      setError("Open this page inside Telegram Mini App to authenticate creator.");
      return;
    }

    setIsSubmitting(true);
    impact("medium");
    try {
      const auth = await authRoomByPin(roomId, pinCode.trim(), initData);
      localStorage.setItem(tokenStorageKey(roomId), auth.control_token);
      setError(null);
      router.replace(`/room/${roomId}`);
    } catch (e) {
      if (isApiError(e)) {
        setError(e.message);
      } else if (e instanceof Error && e.message) {
        setError(e.message);
      } else {
        setError("Failed to authenticate creator.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <section className={styles.hero}>
          <h1 className={styles.title}>Enter PIN</h1>
        </section>

        <List className={styles.list}>
          <Section>
            <div className={styles.form}>
              <Input
                value={pinCode}
                onChange={(e) => setPinCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric"
                maxLength={6}
                placeholder="6-digit code"
                status={error ? "error" : "default"}
              />
              {error && <span className={styles.errorText}>{error}</span>}
              <Button onClick={authenticate} loading={isSubmitting} stretched mode="filled">
                Continue
              </Button>
              <Button onClick={() => router.push(`/room/${roomId}`)} stretched mode="bezeled">
                Back
              </Button>
            </div>
          </Section>
        </List>
      </div>
    </main>
  );
}
