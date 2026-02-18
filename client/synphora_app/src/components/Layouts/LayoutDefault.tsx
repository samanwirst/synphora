"use client";

import React, { useEffect, useState } from "react";
import useTelegramWebApp from "@/hooks/useTelegramWebApp";
import { AppRoot } from "@telegram-apps/telegram-ui";

type Props = {
  children: React.ReactNode;
};

export default function LayoutDefault({ children }: Props) {
  const ready = useTelegramWebApp();
  const [appearance, setAppearance] = useState<"light" | "dark">("light");

  useEffect(() => {
    if (!ready) return;

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const webApp = window.Telegram?.WebApp;

    const resolveAppearance = (): "light" | "dark" => {
      const fromTelegram = webApp?.colorScheme;
      if (fromTelegram === "dark" || fromTelegram === "light") {
        return fromTelegram;
      }
      return media.matches ? "dark" : "light";
    };

    const applyAppearance = () => {
      const next = resolveAppearance();
      setAppearance(next);
      document.documentElement.dataset.theme = next;
    };

    applyAppearance();

    const onMediaChange = () => {
      applyAppearance();
    };
    media.addEventListener("change", onMediaChange);

    const onThemeChanged = () => {
      applyAppearance();
    };
    if (webApp?.onEvent) {
      webApp.onEvent("themeChanged", onThemeChanged);
    }

    return () => {
      media.removeEventListener("change", onMediaChange);
      if (webApp?.offEvent) {
        webApp.offEvent("themeChanged", onThemeChanged);
      }
    };
  }, [ready]);

  if (!ready) return null;

  return (
    <AppRoot platform="ios" appearance={appearance}>
      {children}
    </AppRoot>
  );
}
