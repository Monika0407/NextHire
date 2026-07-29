# NextHire – Django Backend Architecture & Database Design
This document provides the comprehensive design specs, entity-relationship schemas, custom roles, and execution patterns for the **NextHire Django-MySQL Backend** deployment.

---

## 1. Project Directory Structure
Below is the full, clean layout of the Django project workspace. Each application is logically isolated to separate concerns, maintaining strict **cohesive MVT (Model-View-Template)** modules.

```text
nexthire/                       # Root Project Directory
│
├── manage.py                   # Django CLI gateway
│
├── nexthire/                   # Core Configuration Directory
│   ├── __init__.py
│   ├── settings.py             # Global DB, Apps, Auth, & Middleware Configs
│   ├── urls.py                 # Root URL router
│   └── wsgi.py / asgi.py
│
├── accounts/                   # Authentication & Role-Based Access Isolation
│   ├── models.py               # Custom User, Profile, Role models
│   ├── views.py                # Dashboard redirections, dual auth verification
│   ├── forms.py                # Custom registration and state forms
│   └── urls.py                 # Auth router (/accounts/login, signup, etc.)
│
├── students/                   # Candidate Services & Portals
│   ├── models.py               # Academic transcripts & portfolio data
│   ├── views.py                # Student analytical desk, submission forms
│   └── urls.py                 # /students/profile, /students/dashboard
│
├── recruiters/                 # Corporate Recruitment Desks
│   ├── models.py               # Enterprise Partner Profile, limits
│   ├── views.py                # Candidate lists, selection pipelines
│   └── urls.py                 # /recruiters/dashboard, /recruiters/company
│
├── jobs/                       # Job Management System
│   ├── models.py               # Job postings, salary boundaries, tags
│   ├── views.py                # Active hiring feeds, filter endpoints
│   └── urls.py                 # /jobs/create, /jobs/<id>/details
│
├── applications/               # Placement Pipeline Engine
│   ├── models.py               # Job applications, tracking transitions
│   ├── views.py                # Bulk status changers, status histories
│   └── urls.py                 # /applications/apply, /applications/<id>/status
│
├── interviews/                 # Corporate Assessment Scheduler
│   ├── models.py               # Timestamps, zoom/meet links, results feedback
│   ├── views.py                # Interview dashboard, feedback submittals
│   └── urls.py                 # /interviews/schedule, /interviews/<id>/feedback
│
├── analytics/                  # Statistical aggregates
│   ├── models.py               # Trend tracking snapshots
│   ├── views.py                # Placed percentages, salary averages, MCA ratios
│   └── urls.py                 # /analytics/summary-metrics
│
├── reports/                    # Statutory Verification Records & PDF Engine
│   ├── models.py               # Analytical report compilation records
│   ├── views.py                # CSV exports, PDF report compile streams
│   └── urls.py                 # /reports/placement-audit/export
│
├── resume/                     # Document storage
│   ├── models.py               # Resume files record index
│   ├── views.py                # Text content extractors, upload receivers
│   └── urls.py                 # /resume/upload
│
├── prediction/                 # Candidate Placement Readiness ML Stub
│   ├── models.py               # CGPA, Skill, and Attendance score indexes
│   ├── views.py                # Random forest/Mock scoring pipelines
│   └── urls.py                 # /prediction/score
│
├── ai/                         # Gemini Artificial Intelligence integration
│   ├── models.py               # Query tokens and response caching
│   ├── views.py                # Resume screening metrics, mockup AI interviews
│   └── urls.py                 # /ai/mock-interview-evaluation
│
├── notifications/              # Real-time event streams & email dispatchers
│   ├── models.py               # In-app notifications status
│   ├── views.py                # Dispatch handlers for SMS, SMTP mailers
│   └── urls.py                 # /notifications/dismiss
│
└── templates/                  # Base MVT HTML templates (Django templating)
    ├── base.html               # Global UI wrapper layout
    ├── accounts/               # Auth layouts (login.html, register.html)
    ├── students/               # Student views (dashboard, profile)
    ├── recruiters/             # Recruiter views (dashboard, posting)
    └── admin_custom/           # Tailored administrative cockpit
```

---

## 2. Database Design & Entity Relationship Diagram (ERD)

### ASCII ER Diagram

```text
    +-----------------------------------------------------+
    |                        USER                         |
    |  - id (PK)                                          |
    |  - username (UQ)                                    |
    |  - email                                            |
    |  - role (ADMIN, STUDENT, RECRUITER)                 |
    +------------------------------+----------------------+
                                   |
         +-------------------------+-------------------------+
         | 1:1                                               | 1:1
  +------v------+                                     +------v------+
  |   STUDENT   |                                     |  RECRUITER  |
  |  - id (PK)  |                                     |  - id (PK)  |
  |  - user (FK)|                                     |  - user (FK)|
  |  - cgpa     |                                     |  - company  |
  |  - course   |                                     |  - address  |
  +----+---+----+                                     +------+------+
       |   |                                                 |
   1:N |   | 1:1                                             | 1:N
       |   +---------------+                                 |
       |                   |                                 |
+------v-----+       +-----v------+                          |
| AUDIO/RES  |       | PREDICTION |                          |
|  - id (PK) |       |  - id (PK) |                          |
|  - std (FK)|       |  - std (FK)|                          |
|  - path    |       |  - index   |                          |
+------------+       +------------+                          |
                                                             |
                            +--------------------------------+
                            | 1:N
                     +------v----+
                     |    JOB    |
                     |  - id (PK)|
                     |  - rec(FK)|
                     |  - title  |
                     +----+------+
                          |
                      1:1 | (Through Application FK)
                          |
                     +----v------+
                     |APPLICATION|
                     |  - id (PK)| <-------------------+
                     |  - std(FK)|                     |
                     |  - job(FK)|                     | 1:1
                     |  - status |                     |
                     +-----------+                     |
                                                 +-----+-----+
                                                 | INTERVIEW |
                                                 | - id (PK) |
                                                 | - app (FK)|
                                                 | - date    |
                                                 +-----------+
```

### Table Schemas and Relationships

1. **User (auth.User)**: Overridden or extended via profile linking. Defines credentials and administrative capabilities.
2. **Student**: Mapped 1-to-1 to User. Contains specialized fields (`usn`, `cgpa`, `skills`, `course`).
3. **Recruiter**: Mapped 1-to-1 to User. Represents corporate profile data (`company_name`, `license_id`, `verification_status`).
4. **Job**: Mapped Many-to-1 to Recruiter. Contains title, CTC boundaries, requirements, and minimum CGPA threshold criteria.
5. **Application**: Unique composite indices or foreign keys binding Student (Many-to-1) and Job (Many-to-1) with current tracking statuses.
6. **Interview**: Mapped 1-to-1 (or Many-to-1 for multi-rounds) to Job Application. Details slot timestamps, interviewer notes, and feed URLs.
7. **Resume**: Mapped Many-to-1 to Student. Holds filepath pointers, upload date, and raw skills content.
8. **Prediction**: Mapped 1-to-1 to Student. Stores model logs predicting corporate selection probability based on historical indicators.
9. **Notification**: Mapped Many-to-1 to User. Logs real-time user-facing announcements, flags, and dispatch status (SMS/Email sent).

---

## 3. Recommended Migration Order
To guarantee integrity and avoid unresolved relational dependencies (`DependencyError`), execute migrations in the following chronological sequence:

1. **`accounts`**: Core user profiles, roles definitions (`Admin`, `Student`, `Recruiter`).
2. **`students`**: Academic transcript schemas dependent on `accounts.User`.
3. **`recruiters`**: Corporate registries dependent on `accounts.User`.
4. **`jobs`**: Job postings dependent on `recruiters.Recruiter`.
5. **`applications`**: Binding join table dependent on both `students.Student` and `jobs.Job`.
6. **`interviews`**: Event coordinates dependent on `applications.Application`.
7. **`resume`**: Attached candidates documentation mapping back to `students.Student`.
8. **`prediction`**: Selection analytics tied to `students.Student`.
9. **`notifications`**: Targeted broadcast alerts dependent on central `accounts.User`.
