#!/usr/bin/env python
"""
Launcher script for the Streamlit Learning Lab.

This script handles the proper path setup and launches
the Streamlit application.

Usage (from multi_agent_system directory):
    ..\\venv\\Scripts\\python.exe run_streamlit.py

Or with activated venv:
    python run_streamlit.py
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    # Get the directory containing this script
    script_dir = Path(__file__).parent.absolute()

    # Path to the Streamlit app
    app_path = script_dir / "streamlit_app" / "app.py"

    if not app_path.exists():
        print(f"Error: Could not find app.py at {app_path}")
        sys.exit(1)

    # Get the virtual environment path
    venv_dir = script_dir.parent / "venv"

    if sys.platform == "win32":
        streamlit_exe = venv_dir / "Scripts" / "streamlit.exe"
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        streamlit_exe = venv_dir / "bin" / "streamlit"
        python_exe = venv_dir / "bin" / "python"

    # Determine which method to use
    if streamlit_exe.exists():
        # Use streamlit directly
        cmd = [str(streamlit_exe), "run", str(app_path)]
    elif python_exe.exists():
        # Use python -m streamlit
        cmd = [str(python_exe), "-m", "streamlit", "run", str(app_path)]
    else:
        # Fall back to system streamlit
        cmd = ["streamlit", "run", str(app_path)]

    print("=" * 60)
    print("  Multi-Agent Orchestration Learning Lab")
    print("=" * 60)
    print(f"  Launching Streamlit app...")
    print(f"  App path: {app_path}")
    print(f"  Command: {' '.join(cmd)}")
    print()
    print("  The app will open in your default browser.")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 60)
    print()

    # Change to the multi_agent_system directory for proper imports
    os.chdir(script_dir)

    # Run streamlit
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
