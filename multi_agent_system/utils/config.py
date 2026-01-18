"""
Configuration Module: Environment and Model Setup

WHAT THIS MODULE DOES:
Loads environment variables, configures LLM clients, and provides utility
functions for accessing configuration throughout the system.

WHY IT EXISTS:
Centralizing configuration:
1. Keeps API keys and secrets secure (loaded from .env)
2. Makes it easy to change models system-wide
3. Provides consistent error handling for missing configs
4. Allows per-agent model customization

KEY LEARNING CONCEPTS:
- Environment variable management with python-dotenv
- Factory pattern for creating LLM instances
- Configuration validation
- Defensive programming (graceful handling of missing vars)

USAGE EXAMPLE:
    from utils.config import get_model, get_config

    # Get default model
    llm = get_model()

    # Get specific agent's model
    llm = get_model("writing")

    # Get configuration value
    max_iterations = get_config("MAX_ITERATIONS", default=10, cast=int)
"""

import os
import logging
from typing import Any, Optional, Callable
from pathlib import Path
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# Try to import tomllib (Python 3.11+) or fall back to tomli
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

# ============================================================================
# LEARNING POINT: Load configuration from multiple sources
# ============================================================================
# Priority order:
# 1. TOML file (if exists) - more structured, supports nested config
# 2. .env file - traditional environment variable approach
# This allows flexible configuration management
# ============================================================================

# Store TOML config globally
_toml_config = {}

# Configure basic logging FIRST (before using logger)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def _load_toml_config():
    """Load configuration from config.toml if it exists."""
    global _toml_config

    # Look for config.toml in parent directory (project root)
    # Current file is in: bots/multi_agent_system/utils/config.py
    # We want to check: bots/config.toml
    current_dir = Path(__file__).parent  # utils/
    project_root = current_dir.parent.parent  # bots/
    toml_path = project_root / "config.toml"

    if toml_path.exists() and tomllib is not None:
        try:
            with open(toml_path, "rb") as f:
                _toml_config = tomllib.load(f)
            logger.info(f"Loaded configuration from {toml_path}")
        except Exception as e:
            logger.warning(f"Failed to load TOML config from {toml_path}: {e}")
    elif toml_path.exists() and tomllib is None:
        logger.warning(
            "config.toml found but tomllib/tomli not available. "
            "Install tomli for Python < 3.11: pip install tomli"
        )

# Load .env file (traditional approach)
load_dotenv()

# Load TOML config (if available)
_load_toml_config()


def get_config(
    key: str,
    default: Any = None,
    required: bool = False,
    cast: Optional[Callable] = None
) -> Any:
    """
    Get a configuration value from TOML or environment variables.

    WHY THIS FUNCTION EXISTS:
    Instead of calling os.getenv() everywhere, this function provides:
    1. Multi-source configuration (TOML then .env)
    2. Type casting (string to int, bool, etc.)
    3. Required variable validation
    4. Consistent error messages
    5. Default value handling

    CONFIGURATION PRIORITY:
    1. TOML file (config.toml) - checked first
    2. Environment variables (.env file)
    3. Default value (if provided)

    Args:
        key: Configuration key (e.g., "ANTHROPIC_API_KEY")
        default: Value to return if key not found (default: None)
        required: If True, raise error when key missing (default: False)
        cast: Function to convert string value (e.g., int, bool)

    Returns:
        Configuration value (cast to appropriate type if specified)

    Raises:
        ValueError: If required=True and key is missing

    Examples:
        >>> api_key = get_config("ANTHROPIC_API_KEY", required=True)
        >>> max_iter = get_config("MAX_ITERATIONS", default=10, cast=int)
        >>> debug = get_config("DEBUG", default=False, cast=lambda x: x.lower() == "true")
    """
    value = None

    # Priority 1: Check TOML config
    # Handle nested keys like "anthropic.api_key"
    if _toml_config:
        # Try direct key first
        value = _toml_config.get(key.lower())

        # If not found and key looks like it should be nested, try common patterns
        if value is None and key == "ANTHROPIC_API_KEY":
            value = _toml_config.get("anthropic", {}).get("api_key")
        elif value is None and key == "DEFAULT_MODEL":
            value = _toml_config.get("settings", {}).get("default_model")
        elif value is None and key == "TEMPERATURE":
            value = _toml_config.get("settings", {}).get("temperature")
        elif value is None and key == "MAX_ITERATIONS":
            value = _toml_config.get("features", {}).get("max_iterations")
        elif value is None and key == "SHOW_DECISION_LOG":
            value = _toml_config.get("features", {}).get("show_decision_log")

    # Priority 2: Check environment variables if not found in TOML
    if value is None:
        value = os.getenv(key, default)
    else:
        # Value found in TOML, but use default if it's None
        if value is None:
            value = default

    # Check if required variable is missing
    if required and value is None:
        error_msg = (
            f"Required configuration '{key}' is not set. "
            f"Please add it to config.toml or .env file. See .env.example for reference."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Return early if no value and not required
    if value is None:
        return None

    # Cast to desired type if cast function provided
    if cast is not None:
        try:
            # Special handling for booleans from TOML (they're already bool type)
            if isinstance(value, bool) and cast.__name__ == '<lambda>':
                # Already a boolean from TOML, return as-is
                return value
            # For string values from .env, apply the cast function
            elif isinstance(value, str):
                value = cast(value)
            # For numeric values from TOML, cast if needed
            else:
                value = cast(value) if not isinstance(value, type(cast(value))) else value
        except Exception as e:
            logger.warning(
                f"Failed to cast '{key}' value '{value}' using {cast.__name__}: {e}. "
                f"Returning default: {default}"
            )
            return default

    return value


def get_model(
    agent_name: Optional[str] = None,
    temperature: Optional[float] = None,
    model_name: Optional[str] = None
) -> ChatAnthropic:
    """
    Factory function to create a ChatAnthropic LLM instance.

    LEARNING OBJECTIVE: Factory Pattern
    Instead of creating ChatAnthropic() directly in each agent, this factory:
    1. Centralizes LLM configuration
    2. Allows per-agent model customization
    3. Handles API key validation
    4. Provides consistent error messages

    WHY THIS MATTERS:
    In production systems, you might want:
    - Different models for different tasks (fast model for routing, powerful for coding)
    - Different temperature settings (deterministic for data, creative for writing)
    - Easy A/B testing of models
    - Centralized cost tracking

    Args:
        agent_name: Name of agent ("writing", "code", "data", "research", "delegator")
                   If provided, looks for agent-specific model config
        temperature: Temperature override (0.0-1.0). If None, uses env config
        model_name: Model name override. If None, uses agent-specific or default

    Returns:
        Configured ChatAnthropic instance

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set

    Examples:
        >>> # Get default model
        >>> llm = get_model()

        >>> # Get agent-specific model (if configured)
        >>> llm = get_model(agent_name="code")

        >>> # Override temperature
        >>> llm = get_model(agent_name="writing", temperature=0.9)

        >>> # Use specific model
        >>> llm = get_model(model_name="claude-opus-4-5-20251101")
    """
    # ========================================================================
    # STEP 1: Get API Key (Required)
    # ========================================================================
    api_key = get_config("ANTHROPIC_API_KEY", required=True)

    # ========================================================================
    # STEP 2: Determine which model to use
    # ========================================================================
    # Priority order:
    # 1. Explicit model_name parameter
    # 2. Agent-specific environment variable (e.g., CODE_AGENT_MODEL)
    # 3. DEFAULT_MODEL environment variable
    # 4. Hardcoded fallback

    if model_name is None:
        if agent_name:
            # Try agent-specific model (e.g., "WRITING_AGENT_MODEL")
            agent_model_key = f"{agent_name.upper()}_AGENT_MODEL"
            model_name = get_config(agent_model_key)

        # Fall back to default model
        if model_name is None:
            model_name = get_config(
                "DEFAULT_MODEL",
                default="claude-3-5-haiku-20241022"  # Cheapest model as fallback
            )

    # ========================================================================
    # STEP 3: Determine temperature
    # ========================================================================
    if temperature is None:
        temperature = get_config("TEMPERATURE", default=0.7, cast=float)

    # ========================================================================
    # STEP 4: Create and return LLM instance
    # ========================================================================
    logger.info(
        f"Creating LLM instance: model={model_name}, "
        f"temperature={temperature}, agent={agent_name or 'default'}"
    )

    return ChatAnthropic(
        anthropic_api_key=api_key,
        model_name=model_name,
        temperature=temperature,
        # Additional useful parameters:
        max_tokens=4096,  # Maximum response length
        # timeout=60,  # Request timeout in seconds
        # max_retries=2,  # Retry on failures
    )


def validate_config() -> bool:
    """
    Validate that all required configuration is present.

    WHY THIS FUNCTION EXISTS:
    It's better to fail fast at startup with clear error messages than to
    fail partway through execution. This function checks all critical config.

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If required configuration is missing

    Example:
        >>> # Call at startup in main.py
        >>> validate_config()
    """
    logger.info("Validating configuration...")

    # Required configurations
    required_vars = [
        "ANTHROPIC_API_KEY",
    ]

    # Optional but recommended
    optional_vars = [
        "DEFAULT_MODEL",
        "MAX_ITERATIONS",
        "LOG_LEVEL",
    ]

    # Check required variables
    missing_required = []
    for var in required_vars:
        try:
            get_config(var, required=True)
        except ValueError:
            missing_required.append(var)

    if missing_required:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_required)}. "
            f"Please check your .env file against .env.example"
        )

    # Warn about missing optional variables
    for var in optional_vars:
        value = get_config(var)
        if value is None:
            logger.warning(
                f"Optional environment variable '{var}' not set. "
                f"Using default value."
            )

    logger.info("Configuration validation successful!")
    return True


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================
# These are commonly-used configuration values that can be imported directly
# instead of calling get_config() repeatedly
# ============================================================================

MAX_ITERATIONS = get_config("MAX_ITERATIONS", default=10, cast=int)
SHOW_DECISION_LOG = get_config(
    "SHOW_DECISION_LOG",
    default="true",
    cast=lambda x: x.lower() == "true"
)
SHOW_STATE_TRANSITIONS = get_config(
    "SHOW_STATE_TRANSITIONS",
    default="false",
    cast=lambda x: x.lower() == "true"
)


# ============================================================================
# KEY CONCEPT: Why use a config module?
# ============================================================================
"""
╔════════════════════════════════════════════════════════════════════════╗
║ KEY CONCEPT: Centralized Configuration                                 ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║ PROBLEM: Scattered configuration makes systems hard to maintain        ║
║   - API keys hardcoded in multiple files                               ║
║   - Inconsistent error handling                                        ║
║   - Difficult to change settings                                       ║
║                                                                         ║
║ SOLUTION: Single source of truth for configuration                     ║
║   - All config in one module                                           ║
║   - Validation at startup (fail fast)                                  ║
║   - Easy to mock for testing                                           ║
║   - Type safety with casting                                           ║
║                                                                         ║
║ REAL-WORLD EXAMPLE:                                                    ║
║   In production, you might have:                                       ║
║   - Different configs per environment (dev/staging/prod)               ║
║   - Feature flags to enable/disable agents                             ║
║   - Cost tracking and rate limiting                                    ║
║   - Secret management integration (AWS Secrets Manager, etc.)          ║
║                                                                         ║
╚════════════════════════════════════════════════════════════════════════╝
"""


if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration module...")

    try:
        validate_config()
        print("✅ Configuration is valid")

        # Try creating a model
        llm = get_model()
        print(f"Successfully created LLM: {llm.model}")

        # Show configuration
        print(f"\nConfiguration:")
        print(f"  Default Model: {get_config('DEFAULT_MODEL')}")
        print(f"  Temperature: {get_config('TEMPERATURE')}")
        print(f"  Max Iterations: {MAX_ITERATIONS}")
        print(f"  Show Decision Log: {SHOW_DECISION_LOG}")

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure:")
        print("1. You have a .env file (copy from .env.example)")
        print("2. ANTHROPIC_API_KEY is set in .env")
