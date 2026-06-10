# CyberProtect — API Routes

## Auth
| Method | Path | Description |
|---|---|---|
| GET/POST | /login | User login |
| GET/POST | /register | New user registration |
| GET | /logout | Log out current user |

## Dashboard
| Method | Path | Description |
|---|---|---|
| GET | / | Account list for current user |

## Scans
| Method | Path | Description |
|---|---|---|
| GET | /accounts/<id>/scans | List all scans for account |
| POST | /accounts/<id>/scans/trigger | Manually trigger a scan |

## Findings
| Method | Path | Description |
|---|---|---|
| GET | /accounts/<id>/scans/<id>/findings | View findings for a scan |

## Team
| Method | Path | Description |
|---|---|---|
| GET | /accounts/<id>/team | View/manage team members (owner only) |
| POST | /accounts/<id>/team/invite | Invite a member by email (owner only) |
| POST | /accounts/<id>/team/<mid>/revoke | Revoke member access immediately (owner only) |

## Export
| Method | Path | Description |
|---|---|---|
| GET | /accounts/<id>/scans/<id>/export.pdf | Export scan report as PDF |
