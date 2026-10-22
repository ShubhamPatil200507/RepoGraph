import asyncio
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from app.core.config import settings
from app.models.api import (
    ExplainResponse,
    GroundingEvidenceItem,
    ImpactResponse,
    TraceResponse,
)
from app.models.graph import GraphEdge, GraphNode, NormalizedGraph

logger = logging.getLogger(__name__)

# System prompt emphasizing evidence grounding and clear distinction of findings
GEMMA_SYSTEM_INSTRUCTION = """You are Gemma, an expert software architecture intelligence model integrated into RepoGraph.
Your role is to explain code architecture, connections, and system behavior based on verified static analysis evidence.

IMPORTANT RULES:
1. Ground your answer strictly in the provided source code snippets and graph relationships.
2. Clearly divide your analysis into:
   - **CONFIRMED FINDINGS**: Directly supported by the supplied source code and graph edges.
   - **INFERRED HYPOTHESES**: Plausible deductions labeled explicitly as hypotheses.
   - **UNRESOLVED QUESTIONS**: Static limitations, runtime behaviors, or missing evidence that cannot be verified statically.
3. Reference real file paths and line ranges from the evidence. Never fabricate line numbers or file paths.
4. If evidence is insufficient, state the limitation honestly rather than guessing."""


class AIService:
    @staticmethod
    def is_ai_available() -> bool:
        """Returns True if GEMINI_API_KEY is configured."""
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    @staticmethod
    def get_status_info() -> Dict[str, Any]:
        available = AIService.is_ai_available()
        return {
            "available": available,
            "configured_model": settings.GEMMA_MODEL,
            "preferred_model": "gemma-4-26b-a4b-it",
            "message": (
                f"Gemma 4 integration active with model '{settings.GEMMA_MODEL}'."
                if available else
                "Gemini API key is not configured. RepoGraph deterministic analysis, 3D visualization, "
                "and graph algorithms remain fully functional. Set GEMINI_API_KEY to activate Gemma 4 explanations."
            )
        }

    @staticmethod
    def _call_model_sync(model_name: str, prompt: str, system_instruction: str) -> Optional[str]:
        """Synchronously calls Google GenAI SDK with normalization and strict retry bounds."""
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1)
            )
        )
        model_id = model_name if model_name.startswith("models/") else f"models/{model_name}"

        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.2,
            }
        )
        return response.text

    @classmethod
    async def generate_explanation(
        cls,
        prompt: str,
        system_instruction: str = GEMMA_SYSTEM_INSTRUCTION,
        timeout_seconds: float = 4.0,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempts generation with preferred Gemma 4 model.
        If Gemma 4 times out or returns 500/503 from Google's endpoint,
        automatically falls back to a verified high-speed compatible model.
        Returns: (generated_text, model_used)
        """
        if not cls.is_ai_available():
            return None, None

        primary_model = settings.GEMMA_MODEL or "gemma-4-26b-a4b-it"
        fallback_models = ["gemini-flash-lite-latest", "gemini-3.5-flash-lite"]

        # 1. Try configured primary model
        try:
            logger.info(f"Generating explanation using primary model: {primary_model}")
            text = await asyncio.wait_for(
                asyncio.to_thread(cls._call_model_sync, primary_model, prompt, system_instruction),
                timeout=timeout_seconds,
            )
            if text and text.strip():
                return text.strip(), primary_model
        except Exception as e:
            logger.warning(
                f"Primary model '{primary_model}' did not respond within {timeout_seconds}s or errored ({e}). "
                "Engaging verified high-speed fallback model..."
            )

        # 2. Try verified fallback models
        for fb_model in fallback_models:
            if fb_model == primary_model:
                continue
            try:
                logger.info(f"Attempting fallback model: {fb_model}")
                text = await asyncio.wait_for(
                    asyncio.to_thread(cls._call_model_sync, fb_model, prompt, system_instruction),
                    timeout=timeout_seconds,
                )
                if text and text.strip():
                    logger.info(f"Fallback model '{fb_model}' successfully generated explanation.")
                    return text.strip(), f"{primary_model} -> fallback: {fb_model}"
            except Exception as fb_err:
                logger.warning(f"Fallback model '{fb_model}' failed: {fb_err}")

        return None, None

    @staticmethod
    def _sanitize_prompt_input(user_input: str) -> str:
        """Protects against prompt injection and adversarial control tokens in user architecture queries."""
        if not user_input or not isinstance(user_input, str):
            return "Explain the architectural role of this component."
        cleaned = user_input.strip()[:500]
        # Neutralize markdown fence escapes and adversarial instruction overrides
        cleaned = re.sub(r"```+", "`", cleaned)
        cleaned = re.sub(r"(?i)(ignore\s+(all\s+)?previous\s+instructions|system\s+prompt|system\s+override|reveal\s+secret)", "[redacted]", cleaned)
        return cleaned

    @staticmethod
    async def explain_component(
        node: GraphNode,
        source_snippet: Optional[str],
        incoming_edges: List[GraphEdge],
        outgoing_edges: List[GraphEdge],
        question: str,
        secondary_node: Optional[GraphNode] = None
    ) -> ExplainResponse:
        sanitized_question = AIService._sanitize_prompt_input(question)
        evidence_items: List[GroundingEvidenceItem] = []
        if source_snippet:
            evidence_items.append(
                GroundingEvidenceItem(
                    file_path=node.file_path,
                    line_range=f"L{node.start_line or 1}-L{node.end_line or (node.start_line or 1)+20}",
                    symbol_name=node.label,
                    relationship=None,
                    snippet=source_snippet[:1500]
                )
            )

        incoming_labels = [e.source for e in incoming_edges[:5]]
        outgoing_labels = [e.target for e in outgoing_edges[:5]]
        default_summary = (
            f"Component '{node.label}' ({node.type}) located in {node.file_path} "
            f"under the '{node.layer}' architectural layer. "
            f"It has {len(incoming_edges)} incoming and {len(outgoing_edges)} outgoing static relationships."
        )
        deterministic_findings = [
            f"Identified as a {node.type} in {node.file_path}:{node.start_line or 1}.",
            f"Belongs to the '{node.layer}' layer with confidence {node.confidence}.",
        ]
        if outgoing_edges:
            deterministic_findings.append(f"Static dependencies to: {', '.join(outgoing_labels)}.")
        if incoming_edges:
            deterministic_findings.append(f"Referenced by: {', '.join(incoming_labels)}.")

        if not AIService.is_ai_available():
            return ExplainResponse(
                explanation=default_summary,
                confidence=node.confidence,
                verified_findings=deterministic_findings,
                inferred_hypotheses=["Dynamic runtime behavior requires active runtime tracing."],
                unresolved_questions=["Configure GEMINI_API_KEY to enable Gemma 4 conversational explanations."],
                grounding_evidence=evidence_items,
                ai_available=False,
                model_used=None
            )

        # Build evidence-grounded prompt for Gemma
        prompt_parts = [
            f"User Question: {sanitized_question}\n",
            f"Primary Component: {node.label} (Type: {node.type}, Layer: {node.layer})",
            f"File: {node.file_path}:{node.start_line}-{node.end_line}",
        ]

        if secondary_node:
            prompt_parts.append(
                f"Secondary Component: {secondary_node.label} (Type: {secondary_node.type}, File: {secondary_node.file_path})"
            )

        if incoming_edges:
            prompt_parts.append("\nVerified Incoming Dependencies:")
            for e in incoming_edges[:10]:
                prompt_parts.append(f"- From {e.source} [{e.type}]: {e.evidence}")

        if outgoing_edges:
            prompt_parts.append("\nVerified Outgoing Dependencies:")
            for e in outgoing_edges[:10]:
                prompt_parts.append(f"- To {e.target} [{e.type}]: {e.evidence}")

        if source_snippet:
            prompt_parts.append(f"\nExtracted Source Code Snippet:\n```\n{source_snippet[:2500]}\n```")

        full_prompt = "\n".join(prompt_parts)

        response_text, model_used = await AIService.generate_explanation(
            prompt=full_prompt,
            system_instruction=GEMMA_SYSTEM_INSTRUCTION,
            timeout_seconds=4.0
        )

        if response_text:
            findings, hypotheses, unknowns = AIService._parse_structured_sections(response_text)
            # If sections were empty, provide grounded defaults
            if not findings:
                findings = deterministic_findings
            return ExplainResponse(
                explanation=response_text,
                confidence=0.92,
                verified_findings=findings,
                inferred_hypotheses=hypotheses,
                unresolved_questions=unknowns,
                grounding_evidence=evidence_items,
                ai_available=True,
                model_used=model_used
            )
        else:
            # Safe grounded fallback if external AI endpoints timeout
            return ExplainResponse(
                explanation=default_summary + "\n\n(AI explanation service temporarily unavailable; showing verified static architectural findings.)",
                confidence=node.confidence,
                verified_findings=deterministic_findings,
                inferred_hypotheses=["Component behavior matches static dependency pattern."],
                unresolved_questions=["Hosted Gemma model endpoint timed out or is temporarily under high demand."],
                grounding_evidence=evidence_items,
                ai_available=False,
                model_used=settings.GEMMA_MODEL
            )

    @staticmethod
    async def explain_trace_path(trace: TraceResponse) -> Optional[str]:
        """Uses Gemma to narrate a feature execution path grounded in graph steps."""
        if not AIService.is_ai_available() or not trace.path_found:
            return None

        steps_text = "\n".join(trace.step_descriptions)
        prompt = (
            f"Explain the following static architectural path step by step. "
            f"Clarify how data or control transitions between these components.\n\n"
            f"Path steps:\n{steps_text}\n\n"
            f"Remember to note where execution sequence may diverge conditionally at runtime."
        )

        text, _ = await AIService.generate_explanation(
            prompt=prompt,
            system_instruction=GEMMA_SYSTEM_INSTRUCTION,
            timeout_seconds=3.5
        )
        return text

    @staticmethod
    async def explain_impact(impact: ImpactResponse) -> Optional[str]:
        """Uses Gemma to explain potential downstream impacts grounded in dependents."""
        if not AIService.is_ai_available():
            return None

        direct_names = [n.label for n in impact.direct_dependents[:8]]
        transitive_names = [n.label for n in impact.transitive_dependents[:8]]
        routes = [n.label for n in impact.affected_routes[:5]]

        prompt = (
            f"Explain the architectural consequences of modifying '{impact.target_node.label}' "
            f"({impact.target_node.type} in {impact.target_node.file_path}).\n\n"
            f"Direct Dependents ({len(impact.direct_dependents)}): {', '.join(direct_names) or 'None'}\n"
            f"Transitive Dependents ({len(impact.transitive_dependents)}): {', '.join(transitive_names) or 'None'}\n"
            f"Affected Routes: {', '.join(routes) or 'None'}\n\n"
            f"Provide actionable risk mitigation advice for developers making this change."
        )

        text, _ = await AIService.generate_explanation(
            prompt=prompt,
            system_instruction=GEMMA_SYSTEM_INSTRUCTION,
            timeout_seconds=3.5
        )
        return text

    @staticmethod
    def _parse_structured_sections(text: str) -> Tuple[List[str], List[str], List[str]]:
        """Extracts bullet points from Confirmed Findings, Hypotheses, and Questions sections."""
        findings: List[str] = []
        hypotheses: List[str] = []
        unknowns: List[str] = []

        current_list = findings
        for line in text.splitlines():
            line_clean = line.strip()
            lower = line_clean.lower()
            if "confirmed" in lower or "findings" in lower:
                current_list = findings
            elif "hypothes" in lower or "inferred" in lower:
                current_list = hypotheses
            elif "unresolved" in lower or "unknown" in lower or "limitations" in lower:
                current_list = unknowns
            elif line_clean.startswith(("-", "*", "•")) and len(line_clean) > 2:
                bullet_content = line_clean.lstrip("-*• ").strip()
                if bullet_content:
                    current_list.append(bullet_content)

        return findings[:6], hypotheses[:4], unknowns[:4]
