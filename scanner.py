"""AI scan engine — runs passive HTTP vulnerability checks against a target domain."""

import requests
from urllib.parse import urlparse, urljoin

SOC2_MAPPING = {
    "sqli":          ["CC6.1", "CC6.6"],
    "xss":           ["CC6.1", "CC6.6"],
    "misconfig":     ["CC6.3", "CC7.1"],
    "broken_auth":   ["CC6.1", "CC6.2"],
    "sensitive_data":["CC6.1", "CC6.7"],
    "cve":           ["CC7.1", "CC8.1"],
}

SEVERITY_WEIGHTS = {
    "critical":      30,
    "high":          15,
    "medium":         8,
    "low":            3,
    "informational":  0,
}

HEADERS_TIMEOUT = 10


def calculate_security_score(findings: list) -> int:
    """Compute 0–100 score; deduct points per finding by severity."""
    deduction = sum(SEVERITY_WEIGHTS.get(f.get("severity", "informational"), 0) for f in findings)
    return max(0, 100 - deduction)


def _fetch(url: str, **kwargs):
    """GET url and return (response, error_string). Never raises."""
    try:
        r = requests.get(url, timeout=HEADERS_TIMEOUT, allow_redirects=True, **kwargs)
        return r, None
    except requests.exceptions.SSLError as e:
        return None, f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        return None, f"Connection error: {e}"
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# Individual checks — each returns a list of finding dicts (may be empty)
# ---------------------------------------------------------------------------

def _check_https(domain_url: str) -> list:
    """Flag if the site is served over plain HTTP."""
    parsed = urlparse(domain_url)
    if parsed.scheme != "https":
        return [dict(
            title="Site not served over HTTPS",
            description=(
                "The site is accessible over plain HTTP, meaning traffic between "
                "the user and server is unencrypted and vulnerable to interception."
            ),
            severity="high",
            affected_url=domain_url,
            remediation_steps=(
                "1. Obtain an SSL/TLS certificate (free via Let's Encrypt).\n"
                "2. Configure your web server to redirect all HTTP traffic to HTTPS.\n"
                "3. Set the Strict-Transport-Security header."
            ),
            soc2_controls=SOC2_MAPPING["broken_auth"],
        )]
    return []


def _check_security_headers(url: str, resp) -> list:
    """Check for missing HTTP security headers."""
    findings = []
    required = {
        "Strict-Transport-Security": (
            "high",
            "HSTS header missing — browsers will not enforce HTTPS-only connections.",
            "Add: Strict-Transport-Security: max-age=31536000; includeSubDomains",
        ),
        "X-Content-Type-Options": (
            "medium",
            "X-Content-Type-Options header missing — browsers may MIME-sniff responses, enabling XSS attacks.",
            "Add: X-Content-Type-Options: nosniff",
        ),
        "X-Frame-Options": (
            "medium",
            "X-Frame-Options header missing — the site can be embedded in iframes, enabling clickjacking attacks.",
            "Add: X-Frame-Options: DENY  (or SAMEORIGIN if you embed your own content)",
        ),
        "Content-Security-Policy": (
            "medium",
            "Content-Security-Policy header missing — no restrictions on where scripts/styles can load from.",
            "Add a Content-Security-Policy header tailored to your site's asset origins.",
        ),
        "Referrer-Policy": (
            "low",
            "Referrer-Policy header missing — full URLs may leak to third-party sites via the Referer header.",
            "Add: Referrer-Policy: strict-origin-when-cross-origin",
        ),
        "Permissions-Policy": (
            "low",
            "Permissions-Policy header missing — browser features (camera, geolocation) are unrestricted.",
            "Add: Permissions-Policy: geolocation=(), microphone=(), camera=()",
        ),
    }
    for header, (severity, description, remediation) in required.items():
        if header not in resp.headers:
            findings.append(dict(
                title=f"Missing security header: {header}",
                description=description,
                severity=severity,
                affected_url=url,
                remediation_steps=remediation,
                soc2_controls=SOC2_MAPPING["misconfig"],
            ))
    return findings


def _check_cookie_flags(url: str, resp) -> list:
    """Check Set-Cookie headers for missing Secure / HttpOnly / SameSite flags."""
    findings = []
    for cookie in resp.cookies:
        issues = []
        if not cookie.secure:
            issues.append("Secure flag missing (cookie sent over plain HTTP)")
        if not cookie.has_nonstandard_attr("HttpOnly"):
            issues.append("HttpOnly flag missing (accessible to JavaScript)")
        if not cookie.has_nonstandard_attr("SameSite"):
            issues.append("SameSite flag missing (vulnerable to CSRF)")
        if issues:
            findings.append(dict(
                title=f"Insecure cookie: {cookie.name}",
                description=f"Cookie '{cookie.name}' has security issues: {'; '.join(issues)}.",
                severity="medium",
                affected_url=url,
                remediation_steps=(
                    f"Set the following attributes on cookie '{cookie.name}':\n"
                    "  Set-Cookie: name=value; Secure; HttpOnly; SameSite=Strict"
                ),
                soc2_controls=SOC2_MAPPING["broken_auth"],
            ))
    return findings


def _check_directory_listing(base_url: str) -> list:
    """Check common paths for open directory listing."""
    findings = []
    paths = ["/uploads/", "/files/", "/backup/", "/logs/", "/static/"]
    for path in paths:
        url = urljoin(base_url, path)
        resp, err = _fetch(url)
        if err or resp is None:
            continue
        text = resp.text.lower()
        if resp.status_code == 200 and ("index of" in text or "directory listing" in text):
            findings.append(dict(
                title=f"Open directory listing at {path}",
                description=(
                    f"The directory {path} is publicly browsable, exposing file names "
                    "and potentially sensitive data to anyone who visits the URL."
                ),
                severity="high",
                affected_url=url,
                remediation_steps=(
                    f"1. Disable directory listing in your web server config for {path}.\n"
                    "2. In Apache: add 'Options -Indexes' to .htaccess or httpd.conf.\n"
                    "3. In Nginx: ensure 'autoindex off;' is set."
                ),
                soc2_controls=SOC2_MAPPING["sensitive_data"],
            ))
    return findings


def _check_exposed_paths(base_url: str) -> list:
    """Check for commonly exposed sensitive endpoints."""
    findings = []
    sensitive = [
        ("/.env",            "critical", "Exposed .env file — may contain database passwords, API keys, and secrets."),
        ("/.git/config",     "critical", "Exposed .git directory — source code and commit history may be accessible."),
        ("/wp-login.php",    "medium",   "WordPress admin login exposed — a common brute-force target."),
        ("/admin",           "medium",   "Admin panel exposed at /admin — ensure it requires strong authentication."),
        ("/phpmyadmin",      "high",     "phpMyAdmin exposed — direct database access interface reachable from the internet."),
        ("/server-status",   "medium",   "Apache server-status page exposed — reveals internal server metrics."),
        ("/robots.txt",      "informational", "robots.txt found — review for paths that reveal internal structure."),
    ]
    for path, severity, description in sensitive:
        url = urljoin(base_url, path)
        resp, err = _fetch(url)
        if err or resp is None:
            continue
        if resp.status_code == 200:
            findings.append(dict(
                title=f"Sensitive path accessible: {path}",
                description=description,
                severity=severity,
                affected_url=url,
                remediation_steps=(
                    f"1. Restrict access to {path} via your web server configuration.\n"
                    "2. Remove or relocate the file if it should not be publicly accessible.\n"
                    "3. Review what is exposed and rotate any leaked credentials immediately."
                ),
                soc2_controls=SOC2_MAPPING["sensitive_data"],
            ))
    return findings


def _check_error_disclosure(base_url: str) -> list:
    """Request a nonexistent path and check if the error page leaks stack traces."""
    url = urljoin(base_url, "/this-path-does-not-exist-cyberprotect-probe")
    resp, err = _fetch(url)
    if err or resp is None:
        return []
    text = resp.text.lower()
    leak_signals = ["traceback", "stack trace", "exception", "syntax error", "at line", "debug", "sqlalchemy", "django"]
    leaking = [s for s in leak_signals if s in text]
    if leaking:
        return [dict(
            title="Detailed error messages exposed",
            description=(
                "The server returns verbose error pages that reveal internal implementation "
                f"details (detected: {', '.join(leaking)}). Attackers can use this to map "
                "the technology stack and find exploitable weaknesses."
            ),
            severity="medium",
            affected_url=url,
            remediation_steps=(
                "1. Set DEBUG=False (or equivalent) in your production configuration.\n"
                "2. Configure a generic 404/500 error page that does not reveal stack traces.\n"
                "3. Log detailed errors server-side only — never send them to the browser."
            ),
            soc2_controls=SOC2_MAPPING["sensitive_data"],
        )]
    return []


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_scan(domain_url: str, credentials=None) -> dict:
    """Execute passive HTTP checks against domain_url; return structured findings."""
    parsed = urlparse(domain_url)
    if not parsed.scheme:
        domain_url = "https://" + domain_url

    findings = []

    findings += _check_https(domain_url)

    resp, err = _fetch(domain_url)
    if err or resp is None:
        findings.append(dict(
            title="Site unreachable",
            description=f"CyberProtect could not connect to {domain_url}: {err}",
            severity="critical",
            affected_url=domain_url,
            remediation_steps="Verify the domain is correct and the site is publicly accessible.",
            soc2_controls=SOC2_MAPPING["misconfig"],
        ))
        return {"findings": findings, "security_score": 0}

    findings += _check_security_headers(domain_url, resp)
    findings += _check_cookie_flags(domain_url, resp)
    findings += _check_directory_listing(domain_url)
    findings += _check_exposed_paths(domain_url)
    findings += _check_error_disclosure(domain_url)

    score = calculate_security_score(findings)
    return {"findings": findings, "security_score": score}
