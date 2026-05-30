import sys
import json
from app.db.sync_session import SyncSessionLocal
from app.models.entities import UserProfile, UserRole
from app.core.encryption import encrypt_value
from app.core.security import hash_password

with SyncSessionLocal() as db:
    user = db.query(UserProfile).filter(UserProfile.email == "jane@example.com").first()
    if not user:
        user = UserProfile(
            name="Jane Smith",
            email="jane@example.com",
            hashed_password=hash_password("password123"),
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    experience_blocks = {
        "education": [
            {
                "school": "Stanford University",
                "dates": "2014 -- 2016",
                "degree": "Master of Science in Artificial Intelligence",
                "location": "Stanford, CA"
            }
        ],
        "experience": [
            {
                "company": "Tech Giants Corp (Cloud AI)",
                "role": "Tech Lead / Senior ML Engineer",
                "dates": "Jan. 2020 -- Present",
                "location": "Seattle, WA",
                "bullets": [
                    "Led a team of 10 engineers in developing and deploying large-scale LLM architectures, reducing inference latency by 45%.",
                    "Architected the company's core AI infrastructure using Kubernetes and Ray, supporting 100M+ daily requests.",
                    "Designed advanced RAG systems for healthcare data processing, ensuring HIPAA compliance and 98% retrieval accuracy."
                ]
            },
            {
                "company": "AI Innovation Labs",
                "role": "Machine Learning Engineer",
                "dates": "Jun. 2016 -- Dec. 2019",
                "location": "San Francisco, CA",
                "bullets": [
                    "Developed computer vision models for medical imaging, improving early cancer detection rates by 20%.",
                    "Optimized distributed training pipelines for deep neural networks using PyTorch and Horovod."
                ]
            }
        ],
        "projects": [
            {
                "name": "OpenSourceGPT Contributor",
                "dates": "2022 -- Present",
                "bullets": [
                    "Contributor to core optimization layers in open-source LLM frameworks.",
                    "Published 3 peer-reviewed papers on efficient fine-tuning techniques."
                ]
            }
        ]
    }

    skills_matrix = {
        "languages": ["Python", "C++", "CUDA", "SQL"],
        "tools": ["AWS", "GCP", "Kubernetes", "Ray", "Docker", "Git"],
        "frameworks": ["PyTorch", "TensorFlow", "Transformers", "LangChain", "HuggingFace"]
    }

    user.experience_blocks = experience_blocks
    user.skills_matrix = skills_matrix
    user.phone = encrypt_value("206-555-0199")
    user.name = "Jane Smith"
    user.location = "Seattle, WA"
    user.experience_years = 8.0
    user.desired_roles = ["Senior Machine Learning Engineer", "AI Architect", "ML Team Lead"]
    user.desired_domains = ["Healthcare", "Artificial Intelligence", "Cloud"]

    db.commit()
    print("User Jane Smith seeded successfully.")
