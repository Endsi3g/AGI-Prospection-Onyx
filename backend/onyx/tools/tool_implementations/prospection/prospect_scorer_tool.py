"""
Prospect Scorer Tool — AGI Prospection Suite
Scores prospects against the agency's ICP using the Manuel de Vente d'Élite methodology.
All output strings are sourced from the i18n module (no hardcoding).
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
T = "prospect_scorer"  # i18n namespace


class ProspectScorerTool(Tool[None]):
    NAME = "score_prospect"
    DISPLAY_NAME = "Prospect ICP Scorer"
    DESCRIPTION = (
        "Score a prospect against your Ideal Customer Profile (ICP). "
        "Analyzes company size, decision-maker level, industry, revenue signals, "
        "and pain indicators to produce a 0-100 fit score."
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
                        "company_name": {"type": "string", "description": "Name of the prospect's company"},
                        "industry": {"type": "string", "description": "Industry or sector"},
                        "employee_count": {"type": "integer", "description": "Approximate number of employees"},
                        "decision_maker_title": {"type": "string", "description": "Title of the contact"},
                        "annual_revenue": {"type": "string", "description": "Estimated annual revenue"},
                        "pain_indicators": {"type": "string", "description": "Known pain points or growth signals"},
                    },
                    "required": ["company_name", "decision_maker_title"],
                },
            },
        }

    @override
    def emit_start(self, placement: Placement) -> None:
        self.emitter.emit(Packet(placement=placement, obj=CustomToolStart(tool_name=self.NAME, tool_id=self._id)))

    @override
    def run(self, placement: Placement, override_kwargs: None = None, **llm_kwargs: Any) -> ToolResponse:
        company_name = llm_kwargs.get("company_name", "Unknown")
        industry = llm_kwargs.get("industry", "")
        employee_count = llm_kwargs.get("employee_count", 0)
        title = llm_kwargs.get("decision_maker_title", "")
        revenue = llm_kwargs.get("annual_revenue", "")
        pain = llm_kwargs.get("pain_indicators", "")

        score = 0
        breakdown = {}

        # Decision-maker level (0-30 pts)
        title_lower = title.lower()
        if any(x in title_lower for x in ["ceo", "founder", "owner", "président", "directeur général"]):
            breakdown["decision_maker"] = {"score": 30, "label": t(T, "c_level")}
            score += 30
        elif any(x in title_lower for x in ["vp", "vice president", "director", "head of"]):
            breakdown["decision_maker"] = {"score": 22, "label": t(T, "vp_director")}
            score += 22
        elif any(x in title_lower for x in ["manager", "responsable", "lead"]):
            breakdown["decision_maker"] = {"score": 12, "label": t(T, "manager")}
            score += 12
        else:
            breakdown["decision_maker"] = {"score": 5, "label": t(T, "other")}
            score += 5

        # Company size (0-25 pts)
        emp = t(T, "employees")
        if 10 <= employee_count <= 200:
            breakdown["company_size"] = {"score": 25, "label": f"{employee_count} {emp} ({t(T, 'sweet_spot')})"}
            score += 25
        elif 200 < employee_count <= 1000:
            breakdown["company_size"] = {"score": 18, "label": f"{employee_count} {emp} ({t(T, 'mid_market')})"}
            score += 18
        elif employee_count > 1000:
            breakdown["company_size"] = {"score": 10, "label": f"{employee_count} {emp} ({t(T, 'enterprise')})"}
            score += 10
        elif employee_count > 0:
            breakdown["company_size"] = {"score": 8, "label": f"{employee_count} {emp} ({t(T, 'small')})"}
            score += 8
        else:
            breakdown["company_size"] = {"score": 0, "label": t(T, "unknown")}

        # Industry match (0-20 pts)
        high_value = ["saas", "e-commerce", "fintech", "consulting", "agency", "tech", "software"]
        industry_lower = industry.lower()
        if any(i in industry_lower for i in high_value):
            breakdown["industry"] = {"score": 20, "label": f"{industry} ({t(T, 'high_value')})"}
            score += 20
        elif industry:
            breakdown["industry"] = {"score": 10, "label": f"{industry} ({t(T, 'standard')})"}
            score += 10
        else:
            breakdown["industry"] = {"score": 0, "label": t(T, "unknown")}

        # Revenue signals (0-15 pts)
        if revenue:
            breakdown["revenue"] = {"score": 15, "label": revenue}
            score += 15
        else:
            breakdown["revenue"] = {"score": 0, "label": t(T, "not_available")}

        # Pain indicators (0-10 pts)
        if pain:
            breakdown["pain_indicators"] = {"score": 10, "label": pain}
            score += 10
        else:
            breakdown["pain_indicators"] = {"score": 0, "label": t(T, "none_identified")}

        # Determine tier — all strings from i18n
        if score >= 75:
            tier = t(T, "tier_a")
            strategy = t(T, "strategy_a")
        elif score >= 50:
            tier = t(T, "tier_b")
            strategy = t(T, "strategy_b")
        elif score >= 25:
            tier = t(T, "tier_c")
            strategy = t(T, "strategy_c")
        else:
            tier = t(T, "tier_d")
            strategy = t(T, "strategy_d")

        result = {
            "company": company_name,
            "icp_score": score,
            "tier": tier,
            "recommended_strategy": strategy,
            "scoring_breakdown": breakdown,
        }

        self.emitter.emit(Packet(placement=placement, obj=CustomToolDelta(
            tool_name=self.NAME, tool_id=self._id, response_type="json", data=result, file_ids=None, error=None)))
        return ToolResponse(
            rich_response=CustomToolCallSummary(tool_name=self.NAME, response_type="json", tool_result=result, error=None),
            llm_facing_response=json.dumps(result, ensure_ascii=False, indent=2))
