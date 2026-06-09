"""Backward-compatible imports for the first MVP package.

New code should import from ``industries.registry`` directly.
"""

from __future__ import annotations

try:
    from industries.registry import INDUSTRIES, calculate_industry, get_default_input
except ModuleNotFoundError:
    from registry import INDUSTRIES, calculate_industry, get_default_input
