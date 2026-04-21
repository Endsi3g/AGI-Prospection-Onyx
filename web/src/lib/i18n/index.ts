/**
 * AGI Prospection — i18n System
 *
 * Lightweight internationalization without external dependencies.
 * Uses React Context + JSON locale files. Supports nested keys via dot notation.
 *
 * Usage:
 *   const { t, locale, setLocale } = useI18n();
 *   t("settings.title") // → "Paramètres" (if locale is "fr")
 *   t("tools.prospectScorer.name") // → "Évaluateur ICP de Prospect"
 */

export type Locale = "en" | "fr";

export const SUPPORTED_LOCALES: { code: Locale; label: string; flag: string }[] = [
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "fr", label: "Français", flag: "🇫🇷" },
];

export const DEFAULT_LOCALE: Locale = "fr";
const LOCALE_STORAGE_KEY = "onyx-locale";

// Lazy-load locale files
const localeModules: Record<Locale, () => Promise<Record<string, any>>> = {
  en: () => import("./locales/en.json").then((m) => m.default),
  fr: () => import("./locales/fr.json").then((m) => m.default),
};

let cachedMessages: Record<Locale, Record<string, any> | null> = {
  en: null,
  fr: null,
};

export async function loadMessages(locale: Locale): Promise<Record<string, any>> {
  if (cachedMessages[locale]) {
    return cachedMessages[locale]!;
  }
  const messages = await localeModules[locale]();
  cachedMessages[locale] = messages;
  return messages;
}

/**
 * Resolve a dot-separated key from a nested object.
 * Example: getNestedValue(obj, "tools.prospectScorer.name")
 */
export function getNestedValue(obj: Record<string, any>, key: string): string {
  const parts = key.split(".");
  let current: any = obj;
  for (const part of parts) {
    if (current === undefined || current === null) return key;
    current = current[part];
  }
  return typeof current === "string" ? current : key;
}

/**
 * Get the saved locale from localStorage, or return the default.
 */
export function getSavedLocale(): Locale {
  if (typeof window === "undefined") return DEFAULT_LOCALE;
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
  if (saved && SUPPORTED_LOCALES.some((l) => l.code === saved)) {
    return saved as Locale;
  }
  return DEFAULT_LOCALE;
}

/**
 * Persist the chosen locale to localStorage.
 */
export function saveLocale(locale: Locale): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(LOCALE_STORAGE_KEY, locale);
}
