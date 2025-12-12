import { useEffect, useState } from "react";
import { init as initApp } from "@/core/init";

export default function useTelegramWebApp() {
    const [ready, setReady] = useState(false);

    // debug configuration
    const debug = false;
    const eruda = false;
    const mockForMacOS = false;

    useEffect(() => {
        const script = document.createElement("script");
        script.src = "https://telegram.org/js/telegram-web-app.js";
        script.async = true;

        script.onload = async () => {
            const webapp = window.Telegram?.WebApp;
            if (!webapp) {
                console.warn("Telegram WebApp not available after script load.");
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

            setReady(true);
        };

        script.onerror = () => {
            console.warn("Failed to load telegram-web-app.js");
        };

        document.head.appendChild(script);
        return () => {
            try {
                script.remove();
            } catch { }
        };
    }, []);

    return ready;
}