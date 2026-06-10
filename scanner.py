"""AI scan engine — runs vulnerability checks against a target domain."""


SOC2_MAPPING = {
    "sqli": ["CC6.1", "CC6.6"],
    "xss": ["CC6.1", "CC6.6"],
    "misconfig": ["CC6.3", "CC7.1"],
    "broken_auth": ["CC6.1", "CC6.2"],
    "sensitive_data": ["CC6.1", "CC6.7"],
    "cve": ["CC7.1", "CC8.1"],
}

SEVERITY_WEIGHTS = {
    "critical": 30,
    "high": 15,
    "medium": 8,
    "low": 3,
    "informational": 0,
}


def calculate_security_score(findings: list) -> int:
    """Compute 0–100 score; deduct points per finding by severity."""
    deduction = sum(SEVERITY_WEIGHTS.get(f.get("severity", "informational"), 0) for f in findings)
    return max(0, 100 - deduction)


def run_scan(domain_url: str, credentials=None) -> dict:
    """Execute a scan against domain_url; return structured findings dict.

    In V1 this is a stub — replace with real scanner integration.
    Returns {"findings": [...], "security_score": int}
    """
    findings = []
    score = calculate_security_score(findings)
    return {"findings": findings, "security_score": score}
