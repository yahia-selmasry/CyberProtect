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

---

## CyberProtect Tables

## athletes
| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key (auto-increment) |
| name | String(255) | Athlete display name |
| grade | Integer | Grade level, nullable |
| specialty | Text | Event specialty, nullable |
| athletic_net_id | Text | AthleticNet external ID, nullable |

## results
| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key (auto-increment) |
| athlete_id | Integer | FK → athletes |
| meet_name | String(255) | Meet name, nullable |
| meet_date | Date | Date of meet/practice, nullable |
| event | String(100) | Event name (e.g. "Mile", "5K") |
| time_seconds | Float (REAL) | Finish time in total seconds |
| session_type | Enum | meet, practice |
| split_400 | Float | 400m split in seconds, nullable |
| split_800 | Float | 800m split in seconds, nullable |
| split_1200 | Float | 1200m split in seconds, nullable |
| notes | Text | Free-form notes, nullable |
| is_personal_best | Boolean | True if fastest for athlete+event; default false |

## track_users
| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key (auto-increment) |
| username | String(255) | Unique |
| password_hash | String(255) | werkzeug hash |
| role | Enum | athlete, coach |
| athlete_id | Integer | FK → athletes, nullable (null for coaches) |
