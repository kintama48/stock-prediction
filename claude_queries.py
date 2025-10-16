import asyncio
from typing import Optional, FrozenSet, Any, List
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam
from loguru import logger

from src.cache import async_cache_decorator
from src.utils import log_time
from env_real import CLAUDE_API_KEY

# Initialize client
claude_client = AsyncAnthropic(api_key=CLAUDE_API_KEY)

@async_cache_decorator(typed=True)
async def query_to_claude_async(
    prompt: str,
    stop_sequences: Optional[FrozenSet[str]] = None,
    extra_data: Optional[dict] = None,
    prefill: Optional[str] = None,
    system_message: Optional[str] = None,
) -> Optional[str]:
    """Async Claude query with caching"""
    if extra_data and type(extra_data) != dict:
        extra_data = dict(extra_data)
    else:
        extra_data = {}
    try:
        # Create properly typed messages
        messages: List[MessageParam] = [
            {
                "role": "user",
                "content": prompt.strip(),
            }
        ]
        if prefill:
            messages.append({
                "role": "assistant",
                "content": prefill.strip(),
            })

        timeout = extra_data.get("timeout", 30) if extra_data else 30

        with log_time("Claude async query"):
            logger.info(f"Querying Claude with prompt: {prompt}")

            message = await asyncio.wait_for(
                claude_client.messages.create(
                    max_tokens=2024,
                    messages=messages,
                    model="claude-sonnet-4-5-20250929",
                    system=system_message.strip() if system_message else "",
                    stop_sequences=list(stop_sequences) if stop_sequences else [],
                ),
                timeout=timeout
            )

            if message.content:
                # Fix content access - check type before accessing text
                content_block = message.content[0]
                if hasattr(content_block, 'text'):
                    generated_text = content_block.text
                    logger.info(f"Claude Generated text: {generated_text}")
                    return generated_text
            return None

    except Exception as e:
        logger.error(f"Error in Claude query: {e}")
        return None
