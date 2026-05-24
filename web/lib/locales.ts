// Liste des langues marketing supportées par le cockpit.
// Centralisée ici pour rester cohérente entre l'API, l'UI et les utilitaires.

export const SUPPORTED_LOCALES = ["fr", "en", "de", "it", "es"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const LOCALE_NAMES: Record<Locale, string> = {
  fr: "français",
  en: "anglais",
  de: "allemand",
  it: "italien",
  es: "espagnol",
};
