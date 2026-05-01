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
                "school": "Tech Institute of AI",
                "dates": "Sep. 2015 -- May 2019",
                "degree": "Master of Science in Machine Learning",
                "location": "Seattle, WA"
            }
        ],
        "coursework": [
            "Deep Learning",
            "Natural Language Processing",
            "Distributed Systems",
            "Advanced User Interfaces",
            "Mobile App Architecture"
        ],
        "experience": [
            {
                "company": "NextGen AI Corp",
                "dates": "Jan 2021 -- Present",
                "title": "Machine Learning Engineer",
                "location": "San Francisco, CA",
                "bullets": [
                    "Designed and trained large-scale transformer models using PyTorch for natural language generation tasks.",
                    "Implemented distributed training pipelines across multi-GPU clusters, reducing training time by 40%.",
                    "Deployed ML models to production using Docker and Kubernetes, ensuring high availability and low latency."
                ]
            },
            {
                "company": "Creative Web Solutions",
                "dates": "Jun 2019 -- Dec 2020",
                "title": "Frontend React Developer",
                "location": "Austin, TX",
                "bullets": [
                    "Built responsive, dynamic web applications using React and TypeScript for various e-commerce clients.",
                    "Collaborated with UX designers to implement accessible components and optimize website loading speeds.",
                    "Managed application state using Redux and interacted with RESTful backend services."
                ]
            },
            {
                "company": "Appify Mobile Startup",
                "dates": "May 2018 -- Aug 2018",
                "title": "iOS Developer Intern",
                "location": "Remote",
                "bullets": [
                    "Developed a native iOS application using Swift and UIKit for tracking daily fitness activities.",
                    "Integrated CoreLocation and HealthKit frameworks to provide accurate tracking data.",
                    "Published the application to the Apple App Store, achieving over 10,000 downloads in the first month."
                ]
            },
            {
                "company": "University AI Research Lab",
                "dates": "Jan 2018 -- May 2019",
                "title": "Undergraduate Research Assistant",
                "location": "Seattle, WA",
                "bullets": [
                    "Conducted extensive research on transformer architectures for NLP applications under Dr. Alan Turing.",
                    "Co-authored a paper on distributed training optimizations for large language models, published at NeurIPS.",
                    "Implemented experimental PyTorch pipelines that achieved a 15% reduction in memory overhead during training."
                ]
            }
        ],
        "projects": [
            {
                "name": "Custom Language Model",
                "tech": "PyTorch, HuggingFace, Transformers",
                "date": "March 2023",
                "bullets": [
                    "Fine-tuned a pre-trained transformer model on a specialized domain dataset to improve text summarization.",
                    "Evaluated model performance using BLEU and ROUGE scores, outperforming baseline models."
                ]
            },
            {
                "name": "E-Commerce Dashboard",
                "tech": "React, TailwindCSS, TypeScript",
                "date": "July 2020",
                "bullets": [
                    "Created an interactive dashboard for vendors to visualize sales metrics and customer demographics.",
                    "Implemented complex data visualizations using D3.js and Recharts."
                ]
            }
        ],
        "linkedin": "https://linkedin.com/in/janesmith",
        "github": "https://github.com/janesmith"
    }

    skills_matrix = {
        "languages": ["Python", "TypeScript", "JavaScript", "Swift", "C++"],
        "tools": ["Git", "Docker", "Kubernetes", "Jupyter", "AWS"],
        "frameworks": ["PyTorch", "React", "Transformers", "Node.js"]
    }

    user.experience_blocks = experience_blocks
    user.skills_matrix = skills_matrix
    user.phone = encrypt_value("987-654-3210")
    user.name = "Jane Smith"
    user.location = "Seattle, WA"

    db.commit()
    print("User Jane Smith seeded successfully.")
