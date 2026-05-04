import sys
import json
from app.db.sync_session import SyncSessionLocal
from app.models.entities import UserProfile, UserRole
from app.core.encryption import encrypt_value
from app.core.security import hash_password

with SyncSessionLocal() as db:
    user = db.query(UserProfile).filter(UserProfile.email == "john@example.com").first()
    if not user:
        user = UserProfile(
            name="John Doe",
            email="john@example.com",
            hashed_password=hash_password("password123"),
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    experience_blocks = {
        "education": [
            {
                "school": "FAST-NUCES Karachi",
                "dates": "2019 -- 2023",
                "degree": "Bachelor of Science in Computer Science",
                "location": "Karachi, Pakistan"
            }
        ],
        "experience": [
            {
                "company": "Local Software House Ltd",
                "role": "Junior QA Engineer",
                "dates": "Aug. 2023 -- Present",
                "location": "Karachi, Pakistan",
                "bullets": [
                    "Performed manual regression testing for fintech mobile applications, identifying 50+ critical bugs.",
                    "Developed automated UI tests using Selenium and Python, increasing test coverage by 30%.",
                    "Collaborated with developers to reproduce and resolve bugs found during UAT phase."
                ]
            },
            {
                "company": "Tech Solutions",
                "role": "QA Intern",
                "dates": "May 2022 -- Aug. 2022",
                "location": "Karachi, Pakistan",
                "bullets": [
                    "Drafted comprehensive test plans and test cases for e-commerce platforms.",
                    "Assisted in load testing using JMeter and analyzed performance bottlenecks."
                ]
            }
        ],
        "projects": [
            {
                "name": "E-Commerce Automation Framework",
                "dates": "2023",
                "bullets": [
                    "Built a custom automation framework using Pytest and Selenium WebDriver.",
                    "Integrated automated reports using Allure."
                ]
            }
        ]
    }

    skills_matrix = {
        "languages": ["Python", "Java", "SQL"],
        "tools": ["Selenium", "Postman", "JMeter", "JIRA", "Git"],
        "frameworks": ["Pytest", "TestNG", "Jenkins"]
    }

    user.experience_blocks = experience_blocks
    user.skills_matrix = skills_matrix
    user.phone = encrypt_value("+92-300-1234567")
    user.name = "John Doe"
    user.location = "Karachi, Pakistan"
    user.experience_years = 1.0
    user.desired_roles = ["QA Engineer", "Junior SDET", "Automation Tester"]
    user.desired_domains = ["Fintech", "E-commerce", "Banking"]

    db.commit()
    print("User John Doe seeded successfully.")
