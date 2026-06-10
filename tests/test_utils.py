import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scanner import calculate_security_score
from utils import seconds_to_display, display_to_seconds


def test_score_no_findings():
    assert calculate_security_score([]) == 100


def test_score_one_critical():
    findings = [{"severity": "critical"}]
    assert calculate_security_score(findings) == 70


def test_score_capped_at_zero():
    findings = [{"severity": "critical"}] * 10
    assert calculate_security_score(findings) == 0


def test_seconds_to_display():
    assert seconds_to_display(272.1) == "4:32.10"


def test_display_to_seconds():
    assert display_to_seconds("4:32.10") == 272.1


def test_round_trip_60():
    assert display_to_seconds(seconds_to_display(60.0)) == 60.0


def test_round_trip_272():
    assert display_to_seconds(seconds_to_display(272.1)) == 272.1


def test_round_trip_3600():
    assert display_to_seconds(seconds_to_display(3600.0)) == 3600.0
