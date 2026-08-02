"""Minimal Sphinx configuration for TheBitLab technical documentation."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

project = "TheBitLab"
copyright = "2026, TheBitPoets"
author = "TheBitPoets"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
source_suffix = {".rst": "restructuredtext"}
master_doc = "index"
exclude_patterns = ["_build"]
autodoc_typehints = "description"
autodoc_mock_imports = ["google", "google.auth", "google.oauth2"]
html_theme = "alabaster"
