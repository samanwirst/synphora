import { useEffect, useState } from "react";
import { init as initApp } from "@/core/init";

export default function useTelegramWebApp() {
    const [ready, setReady] = useState(false);

    // debug configuration
    const debug = false;
    const eruda = false;
    const mockForMacOS = false;

    useEffect(() => {
        let cancelled = false;

        const initialize = async () => {
            if (cancelled) return;
            const webapp = window.Telegram?.WebApp;
            if (!webapp) {
                console.warn("Telegram WebApp not available after script load.");
                if (!cancelled) setReady(true);
                return;
            }

            try {
                if (typeof webapp.ready === "function") webapp.ready();
            } catch (e) {
                console.warn("webapp.ready() failed:", e);
            }
            try {
                await initApp({
                    debug: debug,
                    eruda: eruda,
                    mockForMacOS: mockForMacOS,
                });
            } catch (e) {
                console.warn("SDK init failed:", e);
            }

            if (!cancelled) setReady(true);
        };

        if (window.Telegram?.WebApp) {
            void initialize();
            return () => {
                cancelled = true;
            };
        }

        const existing = document.querySelector<HTMLScriptElement>('script[data-telegram-webapp="1"]');
        if (existing) {
            if (existing.dataset.loaded === "1") {
                void initialize();
            } else {
                const onLoad = () => {
                    existing.dataset.loaded = "1";
                    void initialize();
                };
                const onError = () => {
                    console.warn("Failed to load telegram-web-app.js");
                    if (!cancelled) setReady(true);
                };
                existing.addEventListener("load", onLoad);
                existing.addEventListener("error", onError);
                return () => {
                    cancelled = true;
                    existing.removeEventListener("load", onLoad);
                    existing.removeEventListener("error", onError);
                };
            }
            return () => {
                cancelled = true;
            };
        }

        const script = document.createElement("script");
        script.src = "https://telegram.org/js/telegram-web-app.js";
        script.async = true;
        script.dataset.telegramWebapp = "1";

        const onLoad = () => {
            script.dataset.loaded = "1";
            void initialize();
        };

        const onError = () => {
            console.warn("Failed to load telegram-web-app.js");
            if (!cancelled) setReady(true);
        };

        script.addEventListener("load", onLoad);
        script.addEventListener("error", onError);
        document.head.appendChild(script);

        return () => {
            cancelled = true;
            script.removeEventListener("load", onLoad);
            script.removeEventListener("error", onError);
        };
    }, []);

    return ready;
}
