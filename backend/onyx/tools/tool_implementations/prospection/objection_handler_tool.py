"""
Objection Handler Tool — AGI Prospection Suite
Uses Daniel G's 3-attempt framework and Manuel de Vente d'Élite methodology.
"""
import json
from typing import Any
from typing_extensions import override
from onyx.chat.emitter import Emitter
from onyx.server.query_and_chat.placement import Placement
from onyx.server.query_and_chat.streaming_models import CustomToolDelta, CustomToolStart, Packet
from onyx.tools.interface import Tool
from onyx.tools.models import CustomToolCallSummary, ToolResponse
from onyx.tools.tool_implementations.prospection.i18n import t
from onyx.utils.logger import setup_logger

logger = setup_logger()
T = "objection_handler"  # i18n namespace

OBJECTION_DB = {
    "no_money": {
        "label": "Je n'ai pas l'argent",
        "psychology": "Defense mechanism hiding fear or uncertainty.",
        "attempts": [
            {"name": "Vérité Nue", "script": "Ne vous inquiétez pas pour l'investissement. Si on met l'argent de côté, est-ce la bonne solution pour vous ?"},
            {"name": "Justification", "script": "Si l'argent n'était pas un problème, pourquoi feriez-vous cela ?"},
            {"name": "Engagement Conditionnel", "script": "Si je pouvais rendre cet investissement plus accessible, seriez-vous prêt(e) à avancer ?"},
        ],
    },
    "send_email": {
        "label": "Envoyez-moi un courriel",
        "psychology": "Classic dismissal to end the conversation politely.",
        "attempts": [
            {"name": "Direct (Platten)", "script": "Les courriels sont une perte de temps. Mon objectif est un appel de 10-15 min car notre service est très personnalisé."},
        ],
    },
    "not_interested": {
        "label": "Ça ne m'intéresse pas",
        "psychology": "Automatic defense in the first 5 seconds.",
        "attempts": [
            {"name": "Curiosity Pivot", "script": "C'est exactement ce que [Client similaire] a dit avant qu'on lui montre comment il perdait [X]€/mois. Une seule question ?"},
            {"name": "Pattern Interrupt", "script": "Je ne vous demande pas d'être intéressé maintenant. Juste 30 secondes pour voir si c'est pertinent."},
        ],
    },
    "too_busy": {
        "label": "Je suis occupé(e)",
        "psychology": "Most common first-30-second objection.",
        "attempts": [
            {"name": "Time Mirror (Daniel G)", "script": "Moi aussi j'ai 30 secondes. Pourriez-vous gérer [X] nouveaux clients ce mois-ci ?"},
        ],
    },
    "already_have_provider": {
        "label": "On travaille déjà avec quelqu'un",
        "psychology": "Loyalty or inertia. Doesn't mean satisfied.",
        "attempts": [
            {"name": "Complementary", "script": "Nos meilleurs clients travaillaient déjà avec quelqu'un. Ce qu'on fait est complémentaire."},
            {"name": "Benchmark Offer", "script": "Que diriez-vous d'une analyse comparative gratuite ? Aucun engagement, juste de la data."},
        ],
    },
    "need_to_think": {
        "label": "Il faut que j'y réfléchisse",
        "psychology": "Unresolved doubts they don't want to confront.",
        "attempts": [
            {"name": "Clarify", "script": "Quand vous dites réfléchir, c'est par rapport à l'investissement, le timing, ou la confiance dans les résultats ?"},
        ],
    },
}


class ObjectionHandlerTool(Tool[None]):
    NAME = "handle_objection"
    DISPLAY_NAME = "Objection Handler (Manuel d'Élite)"
    DESCRIPTION = "Generate elite objection responses using Daniel G's framework."

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
                        "objection_type": {
                            "type": "string",
                            "enum": list(OBJECTION_DB.keys()),
                            "description": "Type of objection to handle.",
                        },
                        "prospect_context": {
                            "type": "string",
                            "description": "Context about the prospect.",
                        },
                    },
                    "required": ["objection_type"],
                },
            },
        }

    @override
    def emit_start(self, placement: Placement) -> None:
        self.emitter.emit(Packet(placement=placement, obj=CustomToolStart(tool_name=self.NAME, tool_id=self._id)))

    @override
    def run(self, placement: Placement, override_kwargs: None = None, **llm_kwargs: Any) -> ToolResponse:
        objection_type = llm_kwargs.get("objection_type", "no_money")
        framework = OBJECTION_DB.get(objection_type, OBJECTION_DB["no_money"])
        result = {
            "objection": framework["label"],
            "psychology": framework["psychology"],
            "attempts": framework["attempts"],
            "meta_advice": t(T, "meta_advice"),
        }
        self.emitter.emit(Packet(placement=placement, obj=CustomToolDelta(tool_name=self.NAME, tool_id=self._id, response_type="json", data=result, file_ids=None, error=None)))
        return ToolResponse(rich_response=CustomToolCallSummary(tool_name=self.NAME, response_type="json", tool_result=result, error=None), llm_facing_response=json.dumps(result, ensure_ascii=False))
