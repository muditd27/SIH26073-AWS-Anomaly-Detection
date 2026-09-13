"""
SkyGuard AI — Powered by Nexora
Main Entrypoint for Streamlit Application
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
streamlit_dir = root_dir / "streamlit_app"

if str(streamlit_dir) not in sys.path:
    sys.path.insert(0, str(streamlit_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from streamlit_app.app import main

if __name__ == "__main__":
    main()
