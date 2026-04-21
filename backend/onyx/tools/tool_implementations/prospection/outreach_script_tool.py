"""
Outreach Script Generator — AGI Prospection Suite
Generates Cold Loom, Cold Email, and Cold Call scripts using Charlie Morgan,
Aaron Shepherd, and Jordan Platten methodologies.
"""
import json
from typing import Any
from typing_extensions import override
from onyx.chat.emitter import Emitter
from onyx.server.query_and_chat.placement import Placement
from onyx.server.query_and_chat.streaming_models import CustomToolDelta, CustomToolStart, Packet
from onyx.tools.interface import Tool
from onyx.tools.models import CustomToolCallSummary, ToolResponse
from onyx.utils.logger import setup_logger

logger = setup_logger()

SCRIPT_TEMPLATES = {
    "cold_loom": {
        "method": "Charlie Morgan — Cold Loom",
        "structure": [
            {"step": 1, "name": "Accroche Personnelle (0-7s)", "template": "Salut {prospect_name}, j'étais en train de regarder {company_website} et..."},
            {"step": 2, "name": "Introduction Opportunité (8-16s)", "template": "J'ai une opportunité qui pourrait être pertinente pour {company_name}..."},
            {"step": 3, "name": "Établissement Autorité (17-45s)", "template": "Au cours des dernières années, nous avons développé un système qui génère de manière fiable et constante {result_type} pour {niche}..."},
            {"step": 4, "name": "Solution Douce", "template": "...et nous pouvons vous aider à faire de même grâce à un processus étape par étape."},
            {"step": 5, "name": "Curiosité (Rester Vague)", "template": "Les résultats proviennent de multiples sources que nous avons optimisées..."},
            {"step": 6, "name": "Inversion du Risque", "template": "Nous garantissons le retour sur investissement. C'est totalement sans risque."},
            {"step": 7, "name": "Identity Expectation", "template": "C'est pour cette raison que c'est une évidence, et que presque tous ceux que nous contactons deviennent clients."},
            {"step": 8, "name": "Demande Assumée", "template": "J'ai envoyé ceci personnellement et quand vous répondrez, je répondrai personnellement."},
        ],
    },
    "cold_email": {
        "method": "Aaron Shepherd — Cold Email",
        "structure": [
            {"step": 1, "name": "Sujet", "template": "Scénario de croissance rapide"},
            {"step": 2, "name": "Corps", "template": "{prospect_name},\n\nIntéressé par une comparaison montrant les 12-24 prochains mois de {company_name} avec et sans {front_end_offer} ?\n\nPas un argumentaire, juste un appel de 20 minutes pour cartographier les deux voies.\n\nCordialement"},
        ],
    },
    "cold_call": {
        "method": "Jordan Platten / Daniel G — Cold Call",
        "structure": [
            {"step": 1, "name": "Ouverture", "template": "{prospect_name} ? Ici {agent_name}. Je sais que vous êtes occupé(e), je serai bref."},
            {"step": 2, "name": "Question Bénéfice", "template": "Je me demandais simplement si vous pourriez gérer {value_proposition} ce mois-ci ?"},
            {"step": 3, "name": "Garantie", "template": "Si je ne vous obtenais pas de résultats, vous n'auriez pas à payer un sou."},
        ],
    },
}


class OutreachScriptTool(Tool[None]):
    NAME = "generate_outreach_script"
    DISPLAY_NAME = "Outreach Script Generator"
    DESCRIPTION = "Generate Cold Loom, Cold Email, or Cold Call scripts using elite sales methodologies."

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
                        "channel": {
                            "type": "string",
                            "enum": ["cold_loom", "cold_email", "cold_call"],
                            "description": "Outreach channel: cold_loom, cold_email, or cold_call.",
                        },
                        "prospect_name": {"type": "string", "description": "Prospect's first name."},
                        "company_name": {"type": "string", "description": "Prospect's company name."},
                        "niche": {"type": "string", "description": "Prospect's industry or niche."},
                        "value_proposition": {"type": "string", "description": "The specific result you offer (e.g., '10 nouveaux rendez-vous')."},
                        "front_end_offer": {"type": "string", "description": "Your front-end offer description (e.g., 'accélération de capital')."},
                    },
                    "required": ["channel", "prospect_name", "company_name"],
                },
            },
        }

    @override
    def emit_start(self, placement: Placement) -> None:
        self.emitter.emit(Packet(placement=placement, obj=CustomToolStart(tool_name=self.NAME, tool_id=self._id)))

    @override
    def run(self, placement: Placement, override_kwargs: None = None, **llm_kwargs: Any) -> ToolResponse:
        channel = llm_kwargs.get("channel", "cold_email")
        prospect_name = llm_kwargs.get("prospect_name", "")
        company_name = llm_kwargs.get("company_name", "")
        niche = llm_kwargs.get("niche", "votre industrie")
        value_prop = llm_kwargs.get("value_proposition", "de nouveaux clients qualifiés")
        front_end = llm_kwargs.get("front_end_offer", "notre analyse personnalisée")

        template = SCRIPT_TEMPLATES.get(channel, SCRIPT_TEMPLATES["cold_email"])
        filled_steps = []
        for step in template["structure"]:
            text = step["template"].format(
                prospect_name=prospect_name, company_name=company_name,
                niche=niche, value_proposition=value_prop, front_end_offer=front_end,
                company_website=f"le site de {company_name}", result_type=value_prop,
                agent_name="[Votre Nom]",
            )
            filled_steps.append({"step": step["step"], "name": step["name"], "content": text})

        result = {"method": template["method"], "channel": channel, "prospect": prospect_name, "company": company_name, "script_steps": filled_steps}
        self.emitter.emit(Packet(placement=placement, obj=CustomToolDelta(tool_name=self.NAME, tool_id=self._id, response_type="json", data=result, file_ids=None, error=None)))
        return ToolResponse(rich_response=CustomToolCallSummary(tool_name=self.NAME, response_type="json", tool_result=result, error=None), llm_facing_response=json.dumps(result, ensure_ascii=False))
