"""AI participant for Planning Poker story point estimation."""

import asyncio
import json
import re
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from ..llm import LLMClient
from ..config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class AIEstimate:
    """AI-generated story point estimate."""
    points: int
    reasoning: str
    confidence: str  # "low", "medium", "high"
    factors: List[str]


class AIVoter:
    """AI participant that estimates story points using LLM."""

    NAME = "AI Assistant"

    def __init__(self, config: dict = None):
        if config is None:
            config = ConfigManager().load()
        llm_config = config.get("llm", {})
        self.llm = LLMClient(llm_config)
        self._current_task: Optional[asyncio.Task] = None
        self._current_estimate: Optional[AIEstimate] = None
        self.fibonacci = [1, 2, 3, 5, 8, 13, 21]

    def set_fibonacci(self, fibonacci: List[int]):
        """Set valid story point values."""
        self.fibonacci = fibonacci

    async def estimate_async(
        self,
        task_key: str,
        summary: str,
        description: str,
        current_points: Optional[float] = None
    ) -> AIEstimate:
        """
        Estimate story points for a task asynchronously.

        This is started in parallel when a task is selected.
        """
        prompt = self._build_prompt(task_key, summary, description, current_points)

        try:
            response = await asyncio.to_thread(self.llm.chat, prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"AI estimation failed: {e}")
            # Fallback: middle value
            mid_idx = len(self.fibonacci) // 2
            return AIEstimate(
                points=self.fibonacci[mid_idx],
                reasoning=f"Estimation failed: {e}",
                confidence="low",
                factors=[]
            )

    def start_estimation(
        self,
        task_key: str,
        summary: str,
        description: str,
        current_points: Optional[float] = None
    ):
        """Start parallel estimation when task is selected."""
        # Cancel previous estimation
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

        self._current_estimate = None
        self._current_task = asyncio.create_task(
            self.estimate_async(task_key, summary, description, current_points)
        )

    async def get_estimate(self) -> Optional[AIEstimate]:
        """Get current estimate result (waits if still running)."""
        if self._current_task:
            try:
                self._current_estimate = await self._current_task
            except asyncio.CancelledError:
                pass
        return self._current_estimate

    def get_vote(self) -> Optional[int]:
        """Get vote value for voting."""
        if self._current_estimate:
            return self._current_estimate.points
        return None

    def _build_prompt(
        self,
        task_key: str,
        summary: str,
        description: str,
        current_points: Optional[float]
    ) -> str:
        """Build LLM prompt for estimation."""
        fib_str = ", ".join(str(p) for p in self.fibonacci)

        prompt = f"""You are an experienced software developer. Estimate story points for the following task.

## Task Information
- **Key**: {task_key}
- **Summary**: {summary}
- **Description**: {description or 'No description provided'}
{f'- **Current Estimate**: {current_points} points' if current_points else ''}

## Fibonacci Scale
Valid values: {fib_str}

- 1: Very simple, a few lines of code
- 2: Simple, small feature or bug fix
- 3: Medium complexity, a few files
- 5: Medium-large, multiple components
- 8: Large feature, requires testing
- 13: Very large, might need to be split
- 21: Might not fit in a sprint

## Response Format
Respond in JSON format:
```json
{{
  "points": <fibonacci_value>,
  "reasoning": "<brief explanation>",
  "confidence": "<low|medium|high>",
  "factors": ["<factor1>", "<factor2>"]
}}
```"""
        return prompt

    def _parse_response(self, response: str) -> AIEstimate:
        """Parse LLM response."""
        # Find JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            json_str = json_match.group(0) if json_match else "{}"

        try:
            data = json.loads(json_str)
            points = int(data.get("points", 5))

            # Round to nearest valid fibonacci value
            if points not in self.fibonacci:
                points = min(self.fibonacci, key=lambda x: abs(x - points))

            return AIEstimate(
                points=points,
                reasoning=data.get("reasoning", ""),
                confidence=data.get("confidence", "medium"),
                factors=data.get("factors", [])
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI response: {e}")
            return AIEstimate(
                points=5,
                reasoning="Could not parse response",
                confidence="low",
                factors=[]
            )
