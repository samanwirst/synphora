type HapticImpactStyle = "light" | "medium" | "heavy" | "rigid" | "soft";

export function impact(style: HapticImpactStyle = "light"): void {
  const haptic = window.Telegram?.WebApp?.HapticFeedback;
  if (!haptic || typeof haptic.impactOccurred !== "function") {
    return;
  }

  try {
    haptic.impactOccurred(style);
  } catch {
    // ignore unsupported haptic runtime errors
  }
}
