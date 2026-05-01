import sys
import json
from app.db.sync_session import SyncSessionLocal
from app.models.entities import UserProfile
from app.core.encryption import encrypt_value

with SyncSessionLocal() as db:
    user = db.query(UserProfile).filter(UserProfile.email == "john@example.com").first()
    if not user:
        print("User not found.")
        sys.exit(1)

    experience_blocks = {
        "education": [
            {
                "school": "State University",
                "dates": "Sep. 2017 -- May 2021",
                "degree": "Bachelor of Science in Computer Science",
                "location": "City, State"
            }
        ],
        "coursework": [
            "Data Structures",
            "Software Methodology",
            "Algorithms Analysis",
            "Database Management",
            "Artificial Intelligence",
            "Internet Technology",
            "Systems Programming",
            "Computer Architecture"
        ],
        "experience": [
            {
                "company": "Electronics Company",
                "dates": "May 2020 -- August 2020",
                "title": "Software Engineer Intern",
                "location": "City, State",
                "bullets": [
                    "Developed a service to automatically perform a set of unit tests daily on a product in development in order to decrease time needed for team members to identify and fix bugs/issues.",
                    "Incorporated scripts using Python and PowerShell to aggregate XML test results into an organized format and to load the latest build code onto the hardware, so that daily testing can be performed.",
                    "Utilized Jenkins to provide a continuous integration service in order to automate the entire process of loading the latest build code and test files, running the tests, and generating a report of the results once per day.",
                    "Explored ways to visualize and send a daily report of test results to team members using HTML, Javascript, and CSS."
                ]
            },
            {
                "company": "Startup, Inc",
                "dates": "May 2019 -- August 2019",
                "title": "Front End Developer Intern",
                "location": "City, State",
                "bullets": [
                    "Assisted in development of the front end of a mobile application for iOS/Android using Dart and the Flutter framework.",
                    "Worked with Google Firebase to manage user inputted data across multiple platforms including web and mobile apps.",
                    "Collaborated with team members using version control systems such as Git to organize modifications and assign tasks.",
                    "Utilized Android Studio as a development environment in order to visualize the application in both iOS and Android."
                ]
            }
        ],
        "projects": [
            {
                "name": "Gym Reservation Bot",
                "tech": "Python, Selenium, Google Cloud Console",
                "date": "January 2021",
                "bullets": [
                    "Developed an automatic bot using Python and Google Cloud Console to register myself for a timeslot at my school gym.",
                    "Implemented Selenium to create an instance of Chrome in order to interact with the correct elements of the web page.",
                    "Created a Linux virtual machine to run on Google Cloud so that the program is able to run everyday from the cloud.",
                    "Used Cron to schedule the program to execute automatically at 11 AM every morning so a reservation is made for me."
                ]
            },
            {
                "name": "Ticket Price Calculator App",
                "tech": "Java, Android Studio",
                "date": "November 2020",
                "bullets": [
                    "Created an Android application using Java and Android Studio to calculate ticket prices for trips to museums in NYC.",
                    "Processed user inputted information in the back-end of the app to return a subtotal price based on the tickets selected.",
                    "Utilized the layout editor to create a UI for the application in order to allow different scenes to interact with each other."
                ]
            },
            {
                "name": "Transaction Management GUI",
                "tech": "Java, Eclipse, JavaFX",
                "date": "October 2020",
                "bullets": [
                    "Designed a sample banking transaction system using Java to simulate the common functions of using a bank account.",
                    "Used JavaFX to create a GUI that supports actions such as creating an account, deposit, withdraw, list all acounts, etc.",
                    "Implemented object-oriented programming practices such as inheritance to create different account types and databases."
                ]
            }
        ],
        "leadership": [
            {
                "org": "Fraternity",
                "dates": "Spring 2020 -- Present",
                "title": "President",
                "location": "University Name",
                "bullets": [
                    "Achieved a 4 star fraternity ranking by the Office of Fraternity and Sorority Affairs (highest possible ranking).",
                    "Managed executive board of 5 members and ran weekly meetings to oversee progress in essential parts of the chapter.",
                    "Led chapter of 30+ members to work towards goals that improve and promote community service, academics, and unity."
                ]
            }
        ],
        "linkedin": "https://linkedin.com/in/username",
        "github": "https://github.com/username"
    }

    skills_matrix = {
        "languages": ["Python", "Java", "C", "HTML/CSS", "JavaScript", "SQL"],
        "tools": ["VS Code", "Eclipse", "Google Cloud Platform", "Android Studio"],
        "frameworks": ["Linux", "Jenkins", "GitHub", "JUnit", "WordPress"]
    }

    user.experience_blocks = experience_blocks
    user.skills_matrix = skills_matrix
    user.phone = encrypt_value("123-456-7890")
    user.name = "John Doe"

    db.commit()
    print("User updated successfully.")
