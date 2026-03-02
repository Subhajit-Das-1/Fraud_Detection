"""
Risk Scorer — Combines rule-based and ML scores into a final risk assessment.
Formula: final_score = (rule_score × 0.5) + (ml_score × 0.5)
"""


def compute_final_score(rule_score: float, ml_score: float) -> tuple[float, str]:
    """
    Compute final risk score and classify risk level.

    Returns:
        (final_score, risk_level)
    """
    final_score = (rule_score * 0.5) + (ml_score * 0.5)
    final_score = max(0, min(100, final_score))

    if final_score >= 61:
        risk_level = "High"
    elif final_score >= 31:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return round(final_score, 2), risk_level
