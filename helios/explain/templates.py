"""
Explanation templates for HELIOS ETF FLOW.

Templates for generating human-readable explanations of sector
allocation states and their drivers.

GUARDRAIL: Explanations describe WHERE capital flows.
They do NOT recommend actions.
"""

from helios.core.types import AllocationState

# Per-state headline templates
STATE_TEMPLATES: dict[AllocationState, str] = {
    AllocationState.OVERWEIGHT: (
        "Strong positive net inflows and sustained outperformance versus SPY."
    ),
    AllocationState.ACCUMULATING: (
        "Net inflows accelerating with above-average relative performance."
    ),
    AllocationState.NEUTRAL: (
        "Balanced capital flows and performance roughly in line with SPY."
    ),
    AllocationState.DECREASING: (
        "Net outflows building with below-average relative performance."
    ),
    AllocationState.UNDERWEIGHT: (
        "Significant net outflows and sustained underperformance versus SPY."
    ),
}

# Per-driver directional templates
DRIVER_TEMPLATES: dict[str, dict[str, str]] = {
    "AP": {
        "elevated": "Strong net capital inflows detected",
        "depressed": "Significant net capital outflows detected",
        "neutral": "Capital flows are balanced",
    },
    "RS": {
        "elevated": "Outperforming SPY on a relative basis",
        "depressed": "Underperforming SPY on a relative basis",
        "neutral": "Performance in line with SPY",
    },
}

# Baseline status templates
STATUS_TEMPLATES: dict[str, str] = {
    "COMPLETE": "",
    "PARTIAL": "Some features excluded due to insufficient baseline history.",
    "INSUFFICIENT": "Insufficient data for reliable calculation.",
}
