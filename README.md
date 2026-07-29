<div align="center">
  <h1>NextHire</h1>
  <p>A comprehensive Django-based Recruitment and Placement Management Platform.</p>
</div>

## 📌 About NextHire

NextHire is an end-to-end recruitment and placement portal designed to bridge the gap between students, educational institutions (Admins/Trainers), and corporate recruiters. Built on **Django**, it provides customized dashboards, application tracking, machine learning-based readiness predictions, and AI-powered resume screening.

## 🚀 Key Features

*   **Role-Based Dashboards:** Dedicated interfaces for **Students/Trainees**, **Recruiters**, and **Admins**.
*   **Job & Application Pipeline:** Recruiters can post jobs; students can apply. Track application statuses through an intuitive pipeline.
*   **AI Integration:**
    *   **Resume Screening:** Extract insights and evaluate resumes using AI.
    *   **Mock Interviews:** Automated guidance and scoring to help candidates prepare.
*   **Placement Readiness ML:** Predictive analytics scoring candidate readiness based on CGPA, skills, and assessment metrics.
*   **Interview Scheduling:** Built-in scheduling for corporate assessments and feedback tracking.
*   **Analytics & Reports:** Statistical snapshots, placement percentages, and comprehensive PDF/CSV export capabilities.

## 🏗️ Project Architecture

NextHire is built using a cohesive MVT (Model-View-Template) architecture, cleanly separated into the following core modules:

*   `accounts/` - Custom User, Profile, and Role-Based Access Control.
*   `students/` & `trainees/` - Candidate Services, academic transcripts, and portfolios.
*   `recruiters/` - Corporate Recruitment Desks, candidate lists.
*   `jobs/` - Active hiring feeds and job management.
*   `applications/` - Placement Pipeline Engine.
*   `interviews/` - Assessment scheduling and feedback.
*   `analytics/` & `reports/` - Real-time metrics and compliance exports.
*   `prediction/` - ML stub for Candidate Placement Readiness.
*   `ai/` - Artificial Intelligence integrations.
*   `notifications/` - Event streams and alerts.

## 🛠️ Local Development Setup

Follow these steps to run the NextHire backend locally on your machine.

### Prerequisites
*   Python 3.9+
*   Virtual Environment (`venv`)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Monika0407/NextHire.git
   cd nxthire
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On Mac/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   *(Ensure you install the required packages using pip once requirements are specified)*

4. **Environment Variables:**
   *   Copy `.env.example` to `.env`.
   *   Configure your keys and environment secrets inside `.env`.

5. **Run Database Migrations:**
   ```bash
   cd django_backend
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a Superuser (Admin):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   The application will be accessible at `http://127.0.0.1:8000/`.

## 🔒 Project Rules
*   **Running the Server:** Always run the Django server from the `django_backend` directory only.
