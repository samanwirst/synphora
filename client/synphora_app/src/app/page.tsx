"use client";

import "@telegram-apps/telegram-ui/dist/styles.css";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { Button, Input, List, Section } from "@telegram-apps/telegram-ui";

import styles from "./home.module.css";

export default function Home() {
  const router = useRouter();
  const [roomId, setRoomId] = useState("");

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const clean = roomId.trim();
    if (!clean) return;
    router.push(`/room/${clean}`);
  };

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <section className={styles.hero}>
          <h1 className={styles.heroTitle}>Synphora</h1>
          <p className={styles.heroText}>Listen together.</p>
        </section>

        <List className={styles.list}>
          <Section header="Room">
            <form className={styles.form} onSubmit={onSubmit}>
              <Input
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
                placeholder="Room ID"
              />
              <Button type="submit" mode="filled" stretched disabled={roomId.trim() === ""}>
                Open
              </Button>
            </form>
          </Section>
        </List>
      </div>
    </main>
  );
}
