from scanner import calculate_security_score


def test_score_no_findings():
    assert calculate_security_score([]) == 100


def test_score_one_critical():
    findings = [{"severity": "critical"}]
    assert calculate_security_score(findings) == 70


def test_score_capped_at_zero():
    findings = [{"severity": "critical"}] * 10
    assert calculate_security_score(findings) == 0
