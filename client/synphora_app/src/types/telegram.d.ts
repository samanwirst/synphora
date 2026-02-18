declare global {
    interface Window {
        Telegram?: {
            WebApp?: {
                ready(): void;
                initData?: string;
                colorScheme?: 'light' | 'dark';
                onEvent?(eventType: 'themeChanged', callback: () => void): void;
                offEvent?(eventType: 'themeChanged', callback: () => void): void;
                themeParams?: {
                    bg_color?: string;
                    text_color?: string;
                    hint_color?: string;
                    link_color?: string;
                    button_color?: string;
                    button_text_color?: string;
                    secondary_bg_color?: string;
                };
                HapticFeedback?: {
                    impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): void;
                };
                initDataUnsafe?: {
                    user?: {
                        id: number;
                        first_name: string;
                        last_name?: string;
                        username?: string;
                        language_code?: string;
                        is_premium?: boolean;
                    };
                };
            };
        };
    }
}

export { };
