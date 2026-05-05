import math
import re
from collections import Counter
from typing import Any

import numpy as np

from app.models import Job, UserProfile

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9+#.]+")


class MatchScoringEngine:
    def _tokenize(self, text: str) -> list[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text)]

    def _skill_overlap_score(self, user_skills: set[str], job_skills: set[str]) -> float:
        if not job_skills:
            return 0.5  # Neutral score if job description has no extracted skills
        overlap = user_skills.intersection(job_skills)
        return len(overlap) / max(len(job_skills), 1)

    def _experience_alignment_score(self, user_years: float | None, job_desc: str) -> float:
        if user_years is None:
            return 0.7  # Neutral-positive if user hasn't set years
        match = re.search(r"(\d+)\+?\s*years", job_desc.lower())
        if not match:
            return 0.8  # Assume fit if no strict years mentioned
        required = float(match.group(1))
        if required <= 0:
            return 1.0
        return min(user_years / required, 1.0)

    def _to_vector(self, text: str, dimension: int = 256) -> np.ndarray:
        vec = np.zeros(dimension, dtype=float)
        counts = Counter(self._tokenize(text))
        for token, count in counts.items():
            vec[hash(token) % dimension] += float(count)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def _semantic_similarity_score(self, user_text: str, job_text: str) -> float:
        user_vec = self._to_vector(user_text)
        job_vec = self._to_vector(job_text)
        sim = float(np.dot(user_vec, job_vec))
        return max(0.0, min(1.0, sim))

    async def calculate(self, user: UserProfile, job: Job) -> dict[str, Any]:
        user_skills = set(
            skill.lower()
            for skill in (user.skills_matrix.get("skills", []) if isinstance(user.skills_matrix, dict) else [])
        )
        jd_skills = set(skill.lower() for skill in job.parsed_requirements.get("skills", []))

        skill_overlap = self._skill_overlap_score(user_skills, jd_skills)
        exp_alignment = self._experience_alignment_score(user.experience_years, job.raw_text_jd)
        semantic_similarity = self._semantic_similarity_score(
            f"{user.desired_roles} {user.desired_domains} {user.experience_blocks}",
            job.raw_text_jd,
        )

        weighted = 100.0 * ((0.45 * skill_overlap) + (0.25 * exp_alignment) + (0.30 * semantic_similarity))
        score = round(min(max(weighted, 0.0), 100.0), 2)

        reason = (
            f"Skill overlap {math.floor(skill_overlap * 100)}%, "
            f"experience alignment {math.floor(exp_alignment * 100)}%, "
            f"semantic similarity {math.floor(semantic_similarity * 100)}%."
        )
        return {"score": score, "reason": reason}


match_scoring_engine = MatchScoringEngine()
