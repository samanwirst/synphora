"use client";

import React from "react";
import useTelegramWebApp from "@/hooks/useTelegramWebApp";
import { AppRoot } from "@telegram-apps/telegram-ui";

type Props = {
  children: React.ReactNode;
};

export default function LayoutDefault({ children }: Props) {
  const ready = useTelegramWebApp();
  if (!ready) return null;

  return <AppRoot>{children}</AppRoot>;
}