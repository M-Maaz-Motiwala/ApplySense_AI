import asyncio
from app.db.sync_session import SyncSessionLocal
from app.models.entities import UserProfile, Job
from app.services.langgraph.resume_graph import resume_graph
import json
from app.core.encryption import decrypt_value

with SyncSessionLocal() as db:
    user = db.query(UserProfile).filter(UserProfile.email == "john@example.com").first()
    job = db.query(Job).first()

    decrypted_phone = decrypt_value(user.phone) if user.phone else ""

    resume_state = resume_graph.invoke(
        {
            "user_profile": {
                "name": user.name,
                "email": user.email,
                "phone": decrypted_phone,
                "location": user.location or "",
                "linkedin": user.experience_blocks.get("linkedin", ""),
                "github": user.experience_blocks.get("github", ""),
                "experience_blocks": user.experience_blocks,
                "skills_matrix": user.skills_matrix,
            },
            "job_description": job.raw_text_jd,
        }
    )

    print("--- Optimized JSON ---")
    print(json.dumps(resume_state["optimized_json"], indent=2))
