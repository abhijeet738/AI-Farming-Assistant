"""
LLM Provider Factory — Switch between models via LLM_PROVIDER env variable.

Usage in .env:
    LLM_PROVIDER=gemini     → Uses Google Gemini (default)
    LLM_PROVIDER=anthropic  → Uses Anthropic Claude

Add keys to .env:
    GOOGLE_API_KEY=...
    ANTHROPIC_API_KEY=...
    ANTHROPIC_MODEL=claude-sonnet-4-6  (optional, has a default)
"""

import os

import structlog

logger = structlog.get_logger()


def get_llm(temperature: float = 0.3):
    """
    Returns an LLM instance based on the LLM_PROVIDER environment variable.
    Defaults to Gemini if not set.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

    if provider == "anthropic":
        return _build_anthropic(temperature)
    else:
        return _build_gemini(temperature)


def _build_gemini(temperature: float):
    """Build and return a Gemini LLM instance."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError("Run: pip install langchain-google-genai")

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        logger.warning("GOOGLE_API_KEY not set — using dummy key (agent calls will fail)")

    logger.info("LLM provider loaded", provider="gemini", model=model)
    return ChatGoogleGenerativeAI(
        model=model,
        api_key=api_key or "dummy-key-for-testing",
        temperature=temperature,
        convert_system_message_to_human=False,
    )


def _build_anthropic(temperature: float):
    """Build and return an Anthropic Claude LLM instance."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError("Run: pip install langchain-anthropic")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set in your .env file. "
            "Add it to use the Anthropic provider."
        )

    logger.info("LLM provider loaded", provider="anthropic", model=model)
    return ChatAnthropic(
        model=model,
        api_key=api_key,
        temperature=temperature,
    )


