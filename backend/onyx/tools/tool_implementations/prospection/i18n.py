"""
Backend i18n support for AGI Prospection tools.
Provides translation dictionaries for tool outputs so the LLM responses
can be served in the user's preferred language.

The locale is determined by the ONYX_LOCALE environment variable (default: "fr").
"""

import os
from typing import Any

SUPPORTED_LOCALES = ("en", "fr")
DEFAULT_LOCALE = "fr"

TRANSLATIONS: dict[str, dict[str, Any]] = {
    "en": {
        "prospect_scorer": {
            "tier_a": "🔥 TIER A — Priority Prospect",
            "tier_b": "⚡ TIER B — Strong Prospect",
            "tier_c": "📋 TIER C — Nurture",
            "tier_d": "❄️ TIER D — Low Priority",
            "strategy_a": "Deploy Cold Loom (Charlie Morgan method) + personalized Front-End Offer immediately.",
            "strategy_b": "Start with Cold Email sequence (Aaron Shepherd method) with a value-first approach.",
            "strategy_c": "Add to nurture sequence. Engage via content and social proof before direct outreach.",
            "strategy_d": "Park for later. Focus efforts on higher-scoring prospects.",
            "c_level": "C-Level / Founder",
            "vp_director": "VP / Director",
            "manager": "Manager",
            "other": "Other",
            "sweet_spot": "Sweet Spot",
            "mid_market": "Mid-Market",
            "enterprise": "Enterprise",
            "small": "Small",
            "unknown": "Unknown",
            "high_value": "High-Value",
            "standard": "Standard",
            "not_available": "Not available",
            "none_identified": "None identified",
            "employees": "employees",
        },
        "objection_handler": {
            "meta_advice": (
                "Remember: The fortune is in the follow-up attempts. "
                "Never abandon at the first objection. Use the Lion Heart, Lamb Sale approach."
            ),
        },
        "outreach_script": {
            "your_name": "[Your Name]",
            "your_industry": "your industry",
            "new_qualified_clients": "new qualified clients",
            "our_personalized_analysis": "our personalized analysis",
        },
    },
    "fr": {
        "prospect_scorer": {
            "tier_a": "🔥 NIVEAU A — Prospect Prioritaire",
            "tier_b": "⚡ NIVEAU B — Prospect Solide",
            "tier_c": "📋 NIVEAU C — À Nourrir",
            "tier_d": "❄️ NIVEAU D — Faible Priorité",
            "strategy_a": "Déployez un Cold Loom (méthode Charlie Morgan) + Offre d'Entrée personnalisée immédiatement.",
            "strategy_b": "Commencez avec une séquence de Cold Email (méthode Aaron Shepherd) axée sur la valeur.",
            "strategy_c": "Ajoutez à la séquence de nurturing. Engagez via le contenu et la preuve sociale avant la prospection directe.",
            "strategy_d": "Mettez de côté pour plus tard. Concentrez vos efforts sur les prospects mieux notés.",
            "c_level": "Direction / Fondateur",
            "vp_director": "VP / Directeur",
            "manager": "Manager",
            "other": "Autre",
            "sweet_spot": "Zone idéale",
            "mid_market": "Marché intermédiaire",
            "enterprise": "Grande entreprise",
            "small": "Petite entreprise",
            "unknown": "Inconnu",
            "high_value": "Haute valeur",
            "standard": "Standard",
            "not_available": "Non disponible",
            "none_identified": "Aucun identifié",
            "employees": "employés",
        },
        "objection_handler": {
            "meta_advice": (
                "Rappelez-vous : la fortune réside dans le nombre de tentatives. "
                "N'abandonnez jamais à la première objection. Utilisez l'approche Cœur de Lion, Vente d'Agneau."
            ),
        },
        "outreach_script": {
            "your_name": "[Votre Nom]",
            "your_industry": "votre industrie",
            "new_qualified_clients": "de nouveaux clients qualifiés",
            "our_personalized_analysis": "notre analyse personnalisée",
        },
    },
}


def get_locale() -> str:
    """Get the current locale from the ONYX_LOCALE environment variable."""
    locale = os.environ.get("ONYX_LOCALE", DEFAULT_LOCALE).lower()
    if locale not in SUPPORTED_LOCALES:
        return DEFAULT_LOCALE
    return locale


def t(tool: str, key: str) -> str:
    """
    Translate a key for a specific tool.

    Args:
        tool: Tool namespace (e.g., "prospect_scorer", "objection_handler")
        key: Translation key within the tool namespace

    Returns:
        Translated string, or the key itself if not found.
    """
    locale = get_locale()
    tool_translations = TRANSLATIONS.get(locale, TRANSLATIONS[DEFAULT_LOCALE])
    tool_dict = tool_translations.get(tool, {})
    return tool_dict.get(key, key)
