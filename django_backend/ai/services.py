# django_backend/ai/services.py
"""
AI Evaluation Services wrapper.
Leverages the Google Gemini REST API to conduct structured token evaluations,
mock interview question cycles, and counseling chats.
"""

import os
import json
import logging
import time
import hashlib
import requests
from django.conf import settings
from django.core.cache import cache
from .models import PromptTemplate
from .prompts import FALLBACK_PROMPTS

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Service adapter for the official Gemini API REST endpoint.
    Retrieves dynamic prompt templates from the DB and pipes them into Gemini.
    """
    
    @staticmethod
    def get_api_key():
        """
        Retrieves the Gemini API key from environment variables.
        """
        return os.environ.get("GEMINI_API_KEY")

    @staticmethod
    def get_prompt(name):
        """
        Fetches an active prompt template from the database, 
        or populates it from FALLBACK_PROMPTS if not yet registered.
        """
        try:
            template = PromptTemplate.objects.filter(name=name, is_active=True).first()
            if template:
                return {
                    'system': template.system_instruction,
                    'user': template.user_template
                }
        except Exception as e:
            logger.error(f"Failed to query SQL prompt store for {name}: {e}")

        # Fallback & Dynamic Bootstrap
        fallback = FALLBACK_PROMPTS.get(name)
        if fallback:
            try:
                # Bootstrap it silently for Admin editing ease
                PromptTemplate.objects.get_or_create(
                    name=name,
                    defaults={
                        'system_instruction': fallback['system_instruction'],
                        'user_template': fallback['user_template'],
                        'version': 1,
                        'is_active': True
                    }
                )
            except Exception as ex:
                logger.warning(f"Could not automatically cache fallback template {name}: {ex}")
            return {
                'system': fallback['system_instruction'],
                'user': fallback['user_template']
            }

        return {
            'system': "You are an intelligent placement assistant.",
            'user': "{content}"
        }

    @classmethod
    def call_gemini(cls, system_instruction, user_content, response_json=False):
        """
        Makes a secure, native HTTP REST request to the Gemini API.
        """
        api_key = cls.get_api_key()
        if not api_key:
            logger.warning("GEMINI_API_KEY environment variable is not configured. Running safe fallback response.")
            return cls._generate_mock_response(system_instruction, user_content, response_json)

        # Using the standard compliant microservice models
        model_name = getattr(settings, 'GEMINI_MODEL_NAME', 'gemini-2.5-flash')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [{"text": user_content}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "temperature": 0.2
            }
        }

        if response_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        headers = {"Content-Type": "application/json"}

        # Simple caching to reduce duplicate calls for identical prompts
        cache_timeout = getattr(settings, 'AI_RESPONSE_CACHE_TIMEOUT', 300)
        cache_key_raw = f"gemini::{model_name}::{'json' if response_json else 'text'}::{system_instruction}:::{user_content}"
        cache_key = hashlib.sha256(cache_key_raw.encode('utf-8')).hexdigest()
        try:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        except Exception:
            # Cache problems shouldn't stop the request; log and continue
            logger.debug("Cache unavailable or misconfigured; proceeding without cache.")

        # Retry with exponential backoff for transient HTTP errors
        retries = getattr(settings, 'AI_RETRY_COUNT', 3)
        backoff_base = getattr(settings, 'AI_RETRY_BACKOFF_BASE', 0.8)
        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=12)
                if response.status_code == 200:
                    result_json = response.json()
                    text_out = result_json['candidates'][0]['content']['parts'][0]['text']
                    try:
                        cache.set(cache_key, text_out, cache_timeout)
                    except Exception:
                        logger.debug("Failed to write Gemini response to cache.")
                    return text_out

                # For non-200s, log and decide whether to retry
                logger.warning(f"Gemini API returned status {response.status_code} on attempt {attempt}: {response.text}")
                last_exception = Exception(f"Status {response.status_code}")
            except Exception as e:
                logger.error(f"HTTP Connection to Gemini API attempt {attempt} failed: {e}")
                last_exception = e

            # Backoff before next attempt
            if attempt < retries:
                sleep_time = backoff_base * (2 ** (attempt - 1))
                time.sleep(sleep_time)

        # All retries failed — fall back to mock response
        logger.error(f"All {retries} Gemini API attempts failed. Falling back to mock response.")
        return cls._generate_mock_response(system_instruction, user_content, response_json)

    @classmethod
    def _generate_mock_response(cls, system_instruction, user_content, response_json):
        """
        Generates robust, realistic mock responses when offline or missing the API key,
        guaranteeing the platform's user interfaces remain fully interactive.
        """
        if not response_json:
            if "next logical interview question" in user_content.lower():
                return "Can you explain how you would handle database transaction failure and race conditions in a critical production environment?"
            return "Good day! I have evaluated your profile. Based on your current CGPA and skills, focus on expanding practical microservice experience with Docker and Django."

        # Mocks for JSON returns
        if "resume_analysis" in system_instruction.lower():
            return json.dumps({
                "resume_score": 82,
                "resume_summary": "Aspiring software professional possessing solid foundational coursework across computer architectures. Demonstrates hands-on knowledge in database schema design and basic scripting, but lacks cloud architecture experience.",
                "missing_skills": ["Docker", "Kubernetes", "AWS Cloud Services", "FastAPI Integration", "Redis Caching"],
                "improvement_tips": [
                    "Incorporate specific quantitative accomplishments (e.g. 'Improved query latency by 40%').",
                    "Add cloud orchestration deployment steps for your projects of record.",
                    "Include a dedicated section showcasing system engineering certifications."
                ]
            })

        if "cv strategist" in system_instruction.lower() or "resume_roadmap" in system_instruction.lower():
            return json.dumps({
                "weak_areas": ["Cloud deployment models", "Containerization & Orchestration", "Microservice performance optimization"],
                "recommendations": [
                    "Earn AWS Certified Solutions Architect credential.",
                    "Build and deploy a full-stack system in Docker from scratch.",
                    "Implement Redis cache clustering in any of your active portfolio items."
                ],
                "target_resume_suggestions": (
                    "### Updated Target Resume Profile Blueprint\n\n"
                    "#### **Executive Career Summary**\n"
                    "*Results-driven Software Engineer with documented expertise deploying high-performing REST APIs and Microservices within Docker containers. Experienced in optimizing MySQL schema pipelines and cloud system setups.* \n\n"
                    "#### **Target Skills Section**\n"
                    "- **Cloud**: AWS EC2, S3, RDS\n"
                    "- **Containers/DevOps**: Docker, Kubernetes, CI/CD Actions\n"
                    "- **Backend**: Python (Django, FastAPI), Redis"
                )
            })

        if "talent assessor" in system_instruction.lower() or "mock_interview_evaluation" in system_instruction.lower():
            return json.dumps({
                "technical_score": 78,
                "communication_score": 85,
                "suggestions": (
                    "### Technical Feedback Report\n"
                    "1. **Core Problem Solving**: Candidate answered structural algorithm challenges correctly, demonstrating solid syntax fluency.\n"
                    "2. **Distributed Systems**: Mention of ACID properties was excellent, but lacked caching layer explanations.\n"
                    "3. **Communication**: Clean, precise structure with robust technical phrasing."
                )
            })

        return "{}"

    @classmethod
    def analyze_resume(cls, resume_text):
        """
        Phase 2 adapter: parses and ranks raw resume characters.
        """
        pts = cls.get_prompt('resume_analysis')
        user_prompt = pts['user'].format(resume_text=resume_text)
        result = cls.call_gemini(pts['system'], user_prompt, response_json=True)
        try:
            return json.loads(result)
        except Exception:
            # Safe parsing recovery
            return json.loads(cls._generate_mock_response(pts['system'], user_prompt, response_json=True))

    @classmethod
    def summarize_resume(cls, resume_text):
        """
        Convenience helper that analyzes a resume and returns a short,
        human-readable summary string describing score, summary, missing skills
        and actionable tips.
        """
        analysis = cls.analyze_resume(resume_text)
        if not isinstance(analysis, dict):
            return str(analysis)

        parts = []
        score = analysis.get('resume_score')
        if score is not None:
            parts.append(f"Resume score: {score}")

        summary = analysis.get('resume_summary')
        if summary:
            parts.append(f"Summary: {summary}")

        missing = analysis.get('missing_skills') or []
        if missing:
            parts.append("Missing skills: " + ", ".join(missing))

        tips = analysis.get('improvement_tips') or []
        if tips:
            parts.append("Improvement tips:\n- " + "\n- ".join(tips))

        return "\n\n".join(parts)

    @classmethod
    def generate_roadmap(cls, trainee_profile, resume_text=""):
        """
        Phase 5 adapter: formats and tracks the target roadmap timeline.
        """
        pts = cls.get_prompt('resume_roadmap')
        user_prompt = pts['user'].format(
            candidate_name=trainee_profile.user.get_full_name() or trainee_profile.user.username,
            branch=trainee_profile.branch,
            cgpa=float(trainee_profile.cgpa),
            skills=", ".join(trainee_profile.skills) if isinstance(trainee_profile.skills, list) else str(trainee_profile.skills),
            resume_text=resume_text
        )
        result = cls.call_gemini(pts['system'], user_prompt, response_json=True)
        try:
            return json.loads(result)
        except Exception:
            return json.loads(cls._generate_mock_response(pts['system'], user_prompt, response_json=True))

    @classmethod
    def get_next_question(cls, role_title, job_desc, skills_list, dialog_history_str):
        """
        Phase 3 adaptive interviewer quest.
        """
        pts = cls.get_prompt('mock_interview_question')
        user_prompt = pts['user'].format(
            role_title=role_title,
            job_description=job_desc,
            skills=", ".join(skills_list) if isinstance(skills_list, list) else str(skills_list),
            history_dialogs=dialog_history_str
        )
        return cls.call_gemini(pts['system'], user_prompt, response_json=False)

    @classmethod
    def evaluate_interview(cls, role_title, dialogue_text):
        """
        Phase 3 evaluation compiler.
        """
        pts = cls.get_prompt('mock_interview_evaluation')
        user_prompt = pts['user'].format(
            role_title=role_title,
            dialogue_text=dialogue_text
        )
        result = cls.call_gemini(pts['system'], user_prompt, response_json=True)
        try:
            return json.loads(result)
        except Exception:
            return json.loads(cls._generate_mock_response(pts['system'], user_prompt, response_json=True))

    @classmethod
    def get_career_guidance(cls, trainee_profile, query, chat_history_str=""):
        """
        Phase 4 career conversation companion.
        """
        pts = cls.get_prompt('career_guidance')
        user_prompt = pts['user'].format(
            candidate_name=trainee_profile.user.get_full_name() or trainee_profile.user.username,
            branch=trainee_profile.branch,
            cgpa=float(trainee_profile.cgpa),
            skills=", ".join(trainee_profile.skills) if isinstance(trainee_profile.skills, list) else str(trainee_profile.skills),
            student_query=query,
            chat_history=chat_history_str
        )
        return cls.call_gemini(pts['system'], user_prompt, response_json=False)
