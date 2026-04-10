"""LangGraph orchestrator that coordinates parsing, normalization, embedding, and matching."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, TypedDict

import structlog
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.matching_agent import MatchingAgent
from app.agents.normalization_agent import NormalizationAgent
from app.agents.parsing_agent import ParsingAgent
from app.core.config import get_settings
from app.models.schemas import AgentTrace, CandidateProfile, MatchWeights, SkillProfile
from app.services.embedding_service import EmbeddingService
from app.utils.metrics import record_agent_run

logger = structlog.get_logger(__name__)
settings = get_settings()


class OrchestratorState(TypedDict, total=False):
    """LangGraph state shared across the resume pipeline."""

    job_id: str
    raw_file_bytes: bytes
    mime_type: str
    job_description: str
    weights: dict[str, float]
    match_mode: str
    parsed_profile: dict[str, Any]
    raw_text: str
    normalized_profile: dict[str, Any]
    candidate_embedding: list[float]
    match_result: dict[str, Any]
    traces: list[dict[str, Any]]
    errors: list[str]
    partial: bool
    _session: AsyncSession


class ResumeOrchestrator:
    """Execute the multi-agent resume intelligence workflow through a state graph."""

    def __init__(
        self,
        parsing_agent: ParsingAgent,
        normalization_agent: NormalizationAgent,
        matching_agent: MatchingAgent,
        embedding_service: EmbeddingService,
    ) -> None:
        """Build the LangGraph state machine."""

        self.parsing_agent = parsing_agent
        self.normalization_agent = normalization_agent
        self.matching_agent = matching_agent
        self.embedding_service = embedding_service

        graph = StateGraph(OrchestratorState)
        graph.add_node("parse_node", self.parse_node)
        graph.add_node("normalize_node", self.normalize_node)
        graph.add_node("embed_node", self.embed_node)
        graph.add_node("match_node", self.match_node)
        graph.add_edge(START, "parse_node")
        graph.add_edge("parse_node", "normalize_node")
        graph.add_edge("normalize_node", "embed_node")
        graph.add_edge("embed_node", "match_node")
        graph.add_edge("match_node", END)
        self.graph = graph.compile()

    async def run(
        self,
        session: AsyncSession,
        file_bytes: bytes,
        mime_type: str,
        job_description: str = "",
        weights: MatchWeights | None = None,
        match_mode: str | None = None,
        job_id: str | None = None,
    ) -> OrchestratorState:
        """Run the graph end-to-end for one resume."""

        initial_state: OrchestratorState = {
            "job_id": job_id or str(uuid.uuid4()),
            "raw_file_bytes": file_bytes,
            "mime_type": mime_type,
            "job_description": job_description,
            "weights": (weights or MatchWeights()).model_dump(),
            "match_mode": match_mode or "",
            "traces": [],
            "errors": [],
            "partial": False,
            "_session": session,  # type: ignore[typeddict-item]
        }
        return await self.graph.ainvoke(initial_state)

    async def run_batch(
        self,
        session: AsyncSession,
        items: list[dict[str, Any]],
        job_description: str = "",
    ) -> list[OrchestratorState]:
        """Run the graph concurrently for a batch of files using a semaphore."""

        semaphore = asyncio.Semaphore(settings.max_workers)

        async def _runner(item: dict[str, Any]) -> OrchestratorState:
            async with semaphore:
                return await self.run(
                    session=session,
                    file_bytes=item["file_bytes"],
                    mime_type=item["mime_type"],
                    job_description=job_description,
                    job_id=item.get("job_id"),
                )

        return await asyncio.gather(*(_runner(item) for item in items))

    async def parse_node(self, state: OrchestratorState) -> OrchestratorState:
        """Parse a resume into a structured candidate profile."""

        session: AsyncSession = state["_session"]  # type: ignore[index]

        async def _execute() -> OrchestratorState:
            message = await self.parsing_agent.run(state["job_id"], state["raw_file_bytes"], state["mime_type"])
            return {
                "parsed_profile": message.payload["candidate_profile"],
                "raw_text": message.payload["raw_text"],
                "traces": state["traces"] + [message.trace.model_dump()],
            }

        return await self._execute_node("parse_node", state, _execute, session)

    async def normalize_node(self, state: OrchestratorState) -> OrchestratorState:
        """Normalize the candidate skill inventory."""

        session: AsyncSession = state["_session"]  # type: ignore[index]

        async def _execute() -> OrchestratorState:
            profile = CandidateProfile.model_validate(state.get("parsed_profile", {}))
            message = await self.normalization_agent.run(state["job_id"], profile, state.get("raw_text", ""), session)
            return {
                "normalized_profile": message.payload["skill_profile"],
                "traces": state["traces"] + [message.trace.model_dump()],
            }

        return await self._execute_node("normalize_node", state, _execute, session)

    async def embed_node(self, state: OrchestratorState) -> OrchestratorState:
        """Compute a weighted aggregate embedding for normalized candidate skills."""

        session: AsyncSession = state["_session"]  # type: ignore[index]

        async def _execute() -> OrchestratorState:
            started_at = time.perf_counter()
            skill_profile = SkillProfile.model_validate(state.get("normalized_profile", {}))
            names = [skill.name for skill in skill_profile.normalized_skills]
            vectors = await self.embedding_service.embed_batch(names)
            weights = [skill.proficiency_weight for skill in skill_profile.normalized_skills]
            aggregate = self.embedding_service.weighted_average(vectors, weights)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            trace = AgentTrace(agent="embed_node", latency_ms=latency_ms, quality_score=1.0 if aggregate else 0.0)
            updated_profile = skill_profile.model_copy(update={"embedding_vector": aggregate})
            return {
                "candidate_embedding": aggregate,
                "normalized_profile": updated_profile.model_dump(),
                "traces": state["traces"] + [trace.model_dump()],
            }

        return await self._execute_node("embed_node", state, _execute, session)

    async def match_node(self, state: OrchestratorState) -> OrchestratorState:
        """Match the normalized candidate profile to the job description when available."""

        session: AsyncSession = state["_session"]  # type: ignore[index]

        async def _execute() -> OrchestratorState:
            if not state.get("job_description"):
                started_at = time.perf_counter()
                latency_ms = int((time.perf_counter() - started_at) * 1000)
                trace = AgentTrace(agent="matching_agent", latency_ms=latency_ms, quality_score=0.0, error="No job description supplied.")
                return {"traces": state["traces"] + [trace.model_dump()]}
            skill_profile = SkillProfile.model_validate(state.get("normalized_profile", {}))
            message = await self.matching_agent.run(
                state["job_id"],
                skill_profile,
                state.get("job_description", ""),
                MatchWeights.model_validate(state.get("weights", {})),
                state.get("match_mode"),
            )
            return {
                "match_result": message.payload["match_result"],
                "traces": state["traces"] + [message.trace.model_dump()],
            }

        return await self._execute_node("match_node", state, _execute, session)

    async def _execute_node(
        self,
        agent_name: str,
        state: OrchestratorState,
        callback,
        session: AsyncSession,
    ) -> OrchestratorState:
        """Execute a graph node with retry handling and graceful degradation."""

        for attempt in range(3):
            try:
                update = await callback()
                record_agent_run(agent_name, "success", max(update.get("traces", state["traces"])[-1]["latency_ms"] / 1000, 0.0))
                update["_session"] = session  # type: ignore[index]
                update["errors"] = state.get("errors", [])
                update["partial"] = state.get("partial", False)
                return update
            except Exception as exc:
                if attempt == 2:
                    trace = AgentTrace(agent=agent_name, latency_ms=0, quality_score=0.0, error=str(exc))
                    record_agent_run(agent_name, "failure", 0.0)
                    return {
                        "_session": session,  # type: ignore[index]
                        "traces": state.get("traces", []) + [trace.model_dump()],
                        "errors": state.get("errors", []) + [str(exc)],
                        "partial": True,
                    }
                await asyncio.sleep(2**attempt)
