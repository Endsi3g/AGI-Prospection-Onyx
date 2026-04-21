"""
Dataset Ingestion Tool — AGI Prospection Suite
Loads prospect datasets (Google Places JSON, CSV, etc.), auto-scores all entries
against the ICP, and returns enriched data ready for personalized outreach.
"""
import json
import os
import glob
from typing import Any
from typing_extensions import override
from onyx.chat.emitter import Emitter
from onyx.server.query_and_chat.placement import Placement
from onyx.server.query_and_chat.streaming_models import CustomToolDelta, CustomToolStart, Packet
from onyx.tools.interface import Tool
from onyx.tools.models import CustomToolCallSummary, ToolResponse
from onyx.utils.logger import setup_logger

logger = setup_logger()

# Default directory where datasets are mounted/placed
DATASET_DIR = os.environ.get("AGI_DATASET_DIR", "/app/custom_knowledge")

# ICP scoring weights for auto-scoring
HIGH_VALUE_CATEGORIES = [
    "dentiste", "cabinet dentaire", "dentiste cosmétique", "orthodontiste",
    "clinique", "médecin", "chiropracteur", "optométriste", "physiothérapie",
    "avocat", "comptable", "courtier", "agent immobilier",
    "restaurant", "salon", "spa", "gym", "garage",
]


def _score_google_places_prospect(entry: dict) -> dict:
    """Auto-score a Google Places entry against the agency ICP."""
    score = 0
    signals = []

    # Has phone → can be reached
    phone = entry.get("phone", "")
    if phone and phone.strip():
        score += 20
        signals.append("📞 Téléphone disponible")
    else:
        signals.append("⚠️ Pas de téléphone")

    # Review count → established business
    reviews = entry.get("reviewsCount", 0)
    if reviews >= 50:
        score += 25
        signals.append(f"⭐ {reviews} avis (établi)")
    elif reviews >= 20:
        score += 18
        signals.append(f"⭐ {reviews} avis (actif)")
    elif reviews >= 5:
        score += 10
        signals.append(f"⭐ {reviews} avis (émergent)")
    else:
        score += 3
        signals.append(f"⭐ {reviews} avis (nouveau)")

    # Rating → quality indicator
    rating = entry.get("totalScore", 0)
    if rating >= 4.5:
        score += 15
        signals.append(f"🏆 Note: {rating}/5 (excellent)")
    elif rating >= 4.0:
        score += 10
        signals.append(f"👍 Note: {rating}/5 (bon)")
    elif rating > 0:
        score += 5
        signals.append(f"📊 Note: {rating}/5")

    # Category match → industry fit
    categories = [c.lower() for c in entry.get("categories", [])]
    category_match = any(cat in c for c in categories for cat in HIGH_VALUE_CATEGORIES)
    if category_match:
        score += 20
        signals.append("🎯 Industrie haute valeur")
    elif categories:
        score += 8
        signals.append(f"📋 Catégorie: {entry.get('categoryName', 'N/A')}")

    # Location — local Quebec market bonus
    city = entry.get("city", "")
    state = entry.get("state", "")
    if "québec" in state.lower() or "qc" in state.lower():
        score += 10
        signals.append(f"📍 Marché local: {city}, QC")
    elif city:
        score += 5
        signals.append(f"📍 {city}, {state}")

    # Multiple categories → broader service offering
    if len(categories) >= 3:
        score += 10
        signals.append(f"🔗 {len(categories)} services (polyvalent)")

    # Determine tier
    if score >= 70:
        tier = "🔥 TIER A — Prioritaire"
        action = "Cold Loom immédiat (Charlie Morgan)"
    elif score >= 45:
        tier = "⚡ TIER B — Solide"
        action = "Cold Email personnalisé (Aaron Shepherd)"
    elif score >= 25:
        tier = "📋 TIER C — À Nourrir"
        action = "Séquence de nurturing"
    else:
        tier = "❄️ TIER D — Faible Priorité"
        action = "Mettre de côté"

    return {
        "name": entry.get("title", "Inconnu"),
        "phone": phone,
        "city": city,
        "category": entry.get("categoryName", "N/A"),
        "rating": rating,
        "reviews": reviews,
        "icp_score": min(score, 100),
        "tier": tier,
        "recommended_action": action,
        "signals": signals,
        "google_maps_url": entry.get("url", ""),
        "address": entry.get("street", ""),
    }


class DatasetIngestionTool(Tool[None]):
    NAME = "ingest_prospect_dataset"
    DISPLAY_NAME = "Dataset Ingestion (Google Places, CSV)"
    DESCRIPTION = (
        "Load a prospect dataset file (Google Places JSON, Apify export, or CSV), "
        "auto-score all entries against the ICP, and return enriched prospect data "
        "with personalized outreach recommendations."
    )

    def __init__(self, tool_id: int, emitter: Emitter) -> None:
        super().__init__(emitter=emitter)
        self._id = tool_id

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def description(self) -> str:
        return self.DESCRIPTION

    @property
    def display_name(self) -> str:
        return self.DISPLAY_NAME

    @override
    def tool_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": (
                                "Path to the dataset file. Can be a full path or a filename "
                                "in the datasets directory. Supports Google Places JSON and CSV."
                            ),
                        },
                        "min_score": {
                            "type": "integer",
                            "description": "Minimum ICP score to include in results (0-100). Default: 0",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of prospects to return. Default: 50",
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["score", "reviews", "rating"],
                            "description": "Sort results by this field. Default: score",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        }

    @override
    def emit_start(self, placement: Placement) -> None:
        self.emitter.emit(Packet(
            placement=placement,
            obj=CustomToolStart(tool_name=self.NAME, tool_id=self._id),
        ))

    def _find_file(self, file_path: str) -> str | None:
        """Find the dataset file, searching multiple locations."""
        # Try absolute path first
        if os.path.isfile(file_path):
            return file_path

        # Try in the dataset directory
        candidate = os.path.join(DATASET_DIR, file_path)
        if os.path.isfile(candidate):
            return candidate

        # Try glob matching
        patterns = [
            os.path.join(DATASET_DIR, f"*{file_path}*"),
            os.path.join(DATASET_DIR, "**", f"*{file_path}*"),
        ]
        for pattern in patterns:
            matches = glob.glob(pattern, recursive=True)
            if matches:
                return matches[0]

        return None

    @override
    def run(self, placement: Placement, override_kwargs: None = None, **llm_kwargs: Any) -> ToolResponse:
        file_path = llm_kwargs.get("file_path", "")
        min_score = llm_kwargs.get("min_score", 0)
        limit = llm_kwargs.get("limit", 50)
        sort_by = llm_kwargs.get("sort_by", "score")

        # Find the file
        resolved = self._find_file(file_path)
        if not resolved:
            error_result = {
                "error": f"Dataset not found: {file_path}",
                "searched_locations": [file_path, DATASET_DIR],
                "available_files": os.listdir(DATASET_DIR) if os.path.isdir(DATASET_DIR) else [],
            }
            self.emitter.emit(Packet(
                placement=placement,
                obj=CustomToolDelta(
                    tool_name=self.NAME, tool_id=self._id,
                    response_type="json", data=error_result,
                    file_ids=None, error=f"File not found: {file_path}",
                ),
            ))
            return ToolResponse(
                rich_response=CustomToolCallSummary(
                    tool_name=self.NAME, response_type="json",
                    tool_result=error_result, error=f"File not found: {file_path}",
                ),
                llm_facing_response=json.dumps(error_result, ensure_ascii=False),
            )

        # Load and parse
        try:
            with open(resolved, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            error_result = {"error": f"Invalid JSON: {str(e)}", "file": resolved}
            self.emitter.emit(Packet(
                placement=placement,
                obj=CustomToolDelta(
                    tool_name=self.NAME, tool_id=self._id,
                    response_type="json", data=error_result,
                    file_ids=None, error=str(e),
                ),
            ))
            return ToolResponse(
                rich_response=CustomToolCallSummary(
                    tool_name=self.NAME, response_type="json",
                    tool_result=error_result, error=str(e),
                ),
                llm_facing_response=json.dumps(error_result, ensure_ascii=False),
            )

        # Ensure it's a list
        if isinstance(raw_data, dict):
            raw_data = [raw_data]

        # Score all prospects
        scored = [_score_google_places_prospect(entry) for entry in raw_data]

        # Filter by min_score
        filtered = [p for p in scored if p["icp_score"] >= min_score]

        # Sort
        sort_key = {
            "score": lambda p: p["icp_score"],
            "reviews": lambda p: p["reviews"],
            "rating": lambda p: p["rating"],
        }.get(sort_by, lambda p: p["icp_score"])
        filtered.sort(key=sort_key, reverse=True)

        # Limit
        prospects = filtered[:limit]

        # Build summary
        tier_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
        for p in prospects:
            if "TIER A" in p["tier"] or "Prioritaire" in p["tier"]:
                tier_counts["A"] += 1
            elif "TIER B" in p["tier"] or "Solide" in p["tier"]:
                tier_counts["B"] += 1
            elif "TIER C" in p["tier"] or "Nourrir" in p["tier"]:
                tier_counts["C"] += 1
            else:
                tier_counts["D"] += 1

        result = {
            "source_file": os.path.basename(resolved),
            "total_raw_entries": len(raw_data),
            "total_filtered": len(filtered),
            "returned": len(prospects),
            "tier_distribution": tier_counts,
            "avg_score": round(sum(p["icp_score"] for p in prospects) / max(len(prospects), 1), 1),
            "prospects": prospects,
        }

        self.emitter.emit(Packet(
            placement=placement,
            obj=CustomToolDelta(
                tool_name=self.NAME, tool_id=self._id,
                response_type="json", data=result,
                file_ids=None, error=None,
            ),
        ))
        return ToolResponse(
            rich_response=CustomToolCallSummary(
                tool_name=self.NAME, response_type="json",
                tool_result=result, error=None,
            ),
            llm_facing_response=json.dumps(result, ensure_ascii=False, indent=2),
        )
