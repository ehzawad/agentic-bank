"""Thin wrapper around the Anthropic SDK for Claude API calls."""

from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import APIError, AsyncAnthropic, AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)

from chatbot.config import settings


class ClaudeClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._client = AsyncAnthropic(api_key=api_key or settings.anthropic_api_key, max_retries=3)
        self._model = settings.model_name

    async def create(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        """Single Claude API call. Returns the Message object."""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": settings.max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        return await self._client.messages.create(**kwargs)

    async def run_tool_loop(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict],
        tool_executor: Any,
        fact_store: Any = None,
        turn_number: int = 0,
    ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        """Run the agentic tool loop until Claude produces a text response.

        Returns: (final_text, updated_messages, tool_calls_made)
        """
        current_messages = list(messages)
        tool_calls_made: list[dict[str, Any]] = []

        while True:
            try:
                response = await self.create(system, current_messages, tools)
            except AuthenticationError:
                raise
            except RateLimitError as exc:
                logger.warning("Rate-limited by Claude API: %s", exc)
                return (
                    "I'm sorry, the system is experiencing high demand right now. "
                    "Please try again in a moment.",
                    current_messages,
                    tool_calls_made,
                )
            except APIError as exc:
                logger.error("Claude API error: %s", exc)
                return (
                    "I'm sorry, I encountered an unexpected error while processing "
                    "your request. Please try again shortly.",
                    current_messages,
                    tool_calls_made,
                )

            # Collect text and tool_use blocks
            text_parts: list[str] = []
            tool_use_blocks: list[Any] = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_use_blocks.append(block)

            if response.stop_reason != "tool_use" or not tool_use_blocks:
                return "\n".join(text_parts), current_messages, tool_calls_made

            # Append assistant response (with tool_use blocks) to messages
            current_messages.append({
                "role": "assistant",
                "content": [_block_to_dict(b) for b in response.content],
            })

            # Execute each tool and collect results
            tool_results: list[dict[str, Any]] = []
            for tool_block in tool_use_blocks:
                result_str = await tool_executor.execute(
                    tool_block.name, tool_block.input
                )
                try:
                    parsed_result = json.loads(result_str)
                except (json.JSONDecodeError, TypeError):
                    parsed_result = result_str
                tool_calls_made.append({
                    "tool": tool_block.name,
                    "input": tool_block.input,
                    "result": parsed_result,
                })

                if fact_store is not None:
                    fact_data = parsed_result if isinstance(parsed_result, dict) else {"raw": result_str}
                    fact_store.write(
                        key=f"{tool_block.name}_{tool_block.id[:6]}",
                        value=fact_data,
                        source_tool=tool_block.name,
                        turn_number=turn_number,
                    )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result_str,
                })

            # Append tool results as user message
            current_messages.append({"role": "user", "content": tool_results})


def _block_to_dict(block: Any) -> dict[str, Any]:
    """Convert an Anthropic content block to a dict for message assembly."""
    if block.type == "text":
        return {"type": "text", "text": block.text}
    elif block.type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    return {"type": block.type}
