"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  Locale,
  DEFAULT_LOCALE,
  getSavedLocale,
  saveLocale,
  loadMessages,
  getNestedValue,
} from "@/lib/i18n";

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, replacements?: Record<string, string>) => string;
  isLoading: boolean;
}

const I18nContext = createContext<I18nContextValue>({
  locale: DEFAULT_LOCALE,
  setLocale: () => {},
  t: (key: string) => key,
  isLoading: true,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);
  const [messages, setMessages] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(true);

  // Load the saved locale on mount
  useEffect(() => {
    const saved = getSavedLocale();
    setLocaleState(saved);
    loadMessages(saved).then((msgs) => {
      setMessages(msgs);
      setIsLoading(false);
    });
  }, []);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    saveLocale(newLocale);
    setIsLoading(true);
    loadMessages(newLocale).then((msgs) => {
      setMessages(msgs);
      setIsLoading(false);
    });
    // Also update the html lang attribute
    document.documentElement.lang = newLocale;
  }, []);

  const t = useCallback(
    (key: string, replacements?: Record<string, string>): string => {
      let value = getNestedValue(messages, key);
      if (replacements) {
        Object.entries(replacements).forEach(([placeholder, replacement]) => {
          value = value.replace(`{${placeholder}}`, replacement);
        });
      }
      return value;
    },
    [messages]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t, isLoading }}>
      {children}
    </I18nContext.Provider>
  );
}

/**
 * Hook to access translations and locale management.
 *
 * @example
 * const { t, locale, setLocale } = useI18n();
 * <h1>{t("settings.title")}</h1>
 * <button onClick={() => setLocale("fr")}>Français</button>
 */
export function useI18n() {
  return useContext(I18nContext);
}
