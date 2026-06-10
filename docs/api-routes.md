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

## Track Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| GET/POST | /track/login | — | Login for athletes and coaches (username + password) |
| GET | /track/logout | login required | Log out current track user |
| GET/POST | /track/register | — | Register a new athlete or coach account |

## Time Entry
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /add | login required | Render the add time entry form |
| POST | /add | login required | Validate and save a new result; redirects to /athlete/<id> |
| GET | /team | coach only | List all athletes |
| GET | /athlete/<id> | login required; athlete sees own only, coach sees any | Athlete dashboard: all results table + Chart.js performance chart |
| GET | /athlete/<id>/chart-data?event=<event> | login required; athlete sees own only | JSON: `{"labels": [...], "times": [...]}` for the given event |
| GET | /athlete/<id>/compare?event=<event> | login required; athlete sees own only | Meet vs practice comparison chart and summary stats |
