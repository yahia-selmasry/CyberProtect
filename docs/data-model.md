# CyberProtect — Data Model Reference

## businesses
| Field | Type | Notes |
|---|---|---|
| id | String(36) UUID | Primary key |
| name | String(255) | Business display name |
| created_at | DateTime | Auto-set |
| subscription_status | Enum | active, trialing, cancelled, past_due |
| subscription_plan | String | Default: v1_standard |

## accounts
| Field | Type | Notes |
|---|---|---|
| id | String(36) UUID | Primary key |
| business_id | String(36) | FK → businesses |
| name | String(255) | Account display name |
| domain_url | String(2048) | URL being scanned |
| scan_schedule_day | Integer | Day of month (1–28) |
| created_at | DateTime | Auto-set |
| credentials_stored | Boolean | Default false |
| credentials_encrypted | Text | AES-256 Fernet, nullable |

## users
| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key (auto-increment) |
| email | String(255) | Unique |
| phone_number | String(20) | For SMS, nullable |
| password_hash | String(255) | werkzeug bcrypt |
| created_at | DateTime | Auto-set |
| sms_notifications_enabled | Boolean | Default true |

## account_memberships
| Field | Type | Notes |
|---|---|---|
| id | String(36) UUID | Primary key |
| account_id | String(36) | FK → accounts |
| user_id | Integer | FK → users |
| role | Enum | owner, member |
| invited_at | DateTime | Auto-set |
| revoked_at | DateTime | Nullable — set on revocation |

## scans
| Field | Type | Notes |
|---|---|---|
| id | String(36) UUID | Primary key |
| account_id | String(36) | FK → accounts |
| scheduled_at | DateTime | When scan was due |
| started_at | DateTime | Nullable |
| completed_at | DateTime | Nullable until complete |
| status | Enum | scheduled, running, completed, failed |
| security_score | Integer | 0–100, nullable until complete |
| triggered_by | Enum | scheduled, manual |

## findings
| Field | Type | Notes |
|---|---|---|
| id | String(36) UUID | Primary key |
| scan_id | String(36) | FK → scans |
| title | String(255) | Short name |
| description | Text | Plain-English explanation |
| severity | Enum | critical, high, medium, low, informational |
| affected_url | String(2048) | Specific endpoint |
| remediation_steps | Text | Step-by-step fix |
| soc2_controls | JSON | Array e.g. ["CC6.1", "CC7.2"] |
| status | Enum | open, acknowledged, resolved |
| first_seen_scan_id | String(36) | FK → scans |
| resolved_scan_id | String(36) | FK → scans, nullable |

## notifications
| Field | Type | Notes |
|---|---|---|
| id | String(36) UUID | Primary key |
| scan_id | String(36) | FK → scans |
| user_id | Integer | FK → users |
| channel | Enum | email, sms, in_app |
| sent_at | DateTime | Auto-set |
| status | Enum | sent, failed, delivered |
