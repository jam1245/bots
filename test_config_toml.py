"""
Simple test script to verify TOML configuration loading
without requiring all dependencies
"""
import sys
import tomllib
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load the config.toml file
config_path = Path(__file__).parent / "config.toml"

print(f"Testing TOML configuration loading...")
print(f"Config file: {config_path}")
print(f"File exists: {config_path.exists()}\n")

if config_path.exists():
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    print("✅ Successfully loaded config.toml\n")
    print("Configuration contents:")
    print("=" * 60)

    # Display Anthropic config (masking API key)
    if "anthropic" in config:
        api_key = config["anthropic"].get("api_key", "")
        masked_key = api_key[:15] + "..." + api_key[-10:] if len(api_key) > 25 else "***"
        print(f"\n[anthropic]")
        print(f"  api_key = {masked_key}")

    # Display settings
    if "settings" in config:
        print(f"\n[settings]")
        for key, value in config["settings"].items():
            print(f"  {key} = {value}")

    # Display features
    if "features" in config:
        print(f"\n[features]")
        for key, value in config["features"].items():
            print(f"  {key} = {value}")

    print("\n" + "=" * 60)

    # Test accessing nested values (like the config.py does)
    print("\n✅ Testing config access patterns:")
    api_key = config.get("anthropic", {}).get("api_key")
    print(f"  - API key found: {api_key is not None and len(api_key) > 0}")

    default_model = config.get("settings", {}).get("default_model")
    print(f"  - Default model: {default_model}")

    temperature = config.get("settings", {}).get("temperature")
    print(f"  - Temperature: {temperature}")

    max_iterations = config.get("features", {}).get("max_iterations")
    print(f"  - Max iterations: {max_iterations}")

    show_decision_log = config.get("features", {}).get("show_decision_log")
    print(f"  - Show decision log: {show_decision_log} (type: {type(show_decision_log).__name__})")

    print("\n✅ All configuration values loaded successfully!")
    print("\n💡 The config.toml file is working correctly.")
    print("   When you install dependencies (pip install -r multi_agent_system/requirements.txt),")
    print("   the system will automatically use these values.")

else:
    print("❌ config.toml not found!")
    print(f"   Expected location: {config_path}")
