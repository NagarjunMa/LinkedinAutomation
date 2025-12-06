"""
Test fixtures for resume evaluation testing.
Comprehensive collection of resume samples for testing multi-agent evaluation system.
"""

from typing import Dict, Any


class TestResumeFixtures:
    """Collection of test resume content for evaluation testing."""

    @staticmethod
    def get_harvard_compliant_resume() -> str:
        """
        Harvard Career Services compliant resume sample.
        Follows all Harvard standards: no personal pronouns, active voice, quantified achievements.
        """
        return """
        SARAH ELIZABETH CHEN
        Software Engineer
        sarah.e.chen@email.com | (617) 555-0123 | Boston, MA 02138
        LinkedIn: linkedin.com/in/sarahchen | GitHub: github.com/sarahchen

        EDUCATION
        Harvard University, Cambridge, MA
        Bachelor of Arts in Computer Science, magna cum laude | GPA: 3.8/4.0 | May 2023
        Relevant Coursework: Algorithms, Data Structures, Machine Learning, Software Engineering

        TECHNICAL SKILLS
        Languages: Python, JavaScript, Java, TypeScript, SQL, C++
        Frameworks: React, Node.js, Django, Flask, Spring Boot
        Tools: AWS, Docker, Kubernetes, Git, PostgreSQL, MongoDB

        PROFESSIONAL EXPERIENCE
        Software Engineer | TechCorp Industries | Boston, MA | June 2023 - Present
        • Developed scalable microservices architecture serving 2M+ daily active users
        • Reduced system latency by 40% through database query optimization and caching implementation
        • Built automated CI/CD pipeline reducing deployment time from 2 hours to 15 minutes
        • Collaborated with cross-functional team of 8 engineers to deliver 15+ features quarterly
        • Mentored 3 junior developers on coding best practices and system design principles

        Software Engineering Intern | StartupCo | Cambridge, MA | June 2022 - August 2022
        • Architected real-time data processing system handling 100K+ transactions per hour
        • Implemented machine learning recommendation engine increasing user engagement by 25%
        • Designed RESTful APIs consumed by mobile and web applications
        • Reduced bug occurrence by 60% through comprehensive unit and integration testing

        Research Assistant | Harvard Computer Science Department | Cambridge, MA | September 2021 - May 2023
        • Conducted research on distributed systems optimization under Professor Johnson
        • Published paper "Efficient Load Balancing in Cloud Computing" in IEEE Conference Proceedings
        • Developed simulation software achieving 30% improvement in resource allocation efficiency
        • Presented findings at 3 academic conferences reaching 500+ industry professionals

        PROJECTS
        TaskFlow Pro - Full-Stack Task Management Application | 2023
        • Built React/Node.js application with 1,000+ active users within first month
        • Integrated payment processing system handling $10K+ monthly transactions
        • Achieved 99.9% uptime through AWS auto-scaling and load balancing

        AlgoViz - Algorithm Visualization Platform | 2022
        • Created educational platform used by 500+ computer science students
        • Implemented 15+ sorting and graph algorithms with interactive visualizations
        • Reduced learning time by 35% based on user feedback surveys

        LEADERSHIP & ACTIVITIES
        Harvard Computer Science Society | President | September 2022 - May 2023
        • Led organization of 50+ members organizing 12 technical workshops annually
        • Increased membership by 40% through strategic outreach and programming initiatives
        • Coordinated industry networking events connecting students with 25+ tech companies
        """

    @staticmethod
    def get_harvard_violation_resume() -> str:
        """
        Resume with multiple Harvard Career Services violations.
        Contains personal pronouns, passive voice, vague descriptions for testing.
        """
        return """
        John Smith
        I am a Software Developer
        johnsmith@email.com | 555-123-4567

        ABOUT ME
        I'm a passionate software developer with experience in web development.
        My goal is to work for a tech company where I can grow my skills.

        EDUCATION
        State University - Computer Science Degree (2020)
        I graduated with decent grades and learned programming languages.

        EXPERIENCE
        Software Developer at TechCorp (2020-2023)
        • I worked on various projects for the company
        • My responsibilities included coding and debugging
        • I was involved in team meetings and discussions
        • The projects were completed by our team successfully
        • We used modern technologies that were provided by management

        Intern at StartupCo (Summer 2019)
        • I helped with the development of their website
        • My tasks were assigned by my supervisor
        • The codebase was maintained by me during my internship
        • I learned a lot about web development through this experience

        SKILLS
        I know Python, JavaScript, HTML, CSS
        I'm familiar with databases and frameworks
        I can work with Git and other tools
        I have some experience with cloud platforms

        PROJECTS
        Personal Website
        I built my own website using HTML and CSS. It was a good learning experience for me.

        Todo App
        My team created a todo application. I was responsible for the frontend development.
        """

    @staticmethod
    def get_ats_optimized_resume() -> str:
        """
        ATS-optimized resume with proper formatting and keywords.
        Tests ATS compatibility agent functionality.
        """
        return """
        MICHAEL RODRIGUEZ
        Senior Software Engineer
        michael.rodriguez@email.com | (555) 987-6543 | San Francisco, CA 94105

        TECHNICAL SKILLS
        Programming Languages: Python, Java, JavaScript, TypeScript, C#, Go
        Web Technologies: React, Angular, Vue.js, Node.js, Express.js, Django, Flask
        Cloud Platforms: Amazon Web Services (AWS), Microsoft Azure, Google Cloud Platform
        Databases: PostgreSQL, MySQL, MongoDB, Redis, Cassandra
        DevOps Tools: Docker, Kubernetes, Jenkins, GitLab CI, Terraform
        Version Control: Git, GitHub, GitLab, Bitbucket

        PROFESSIONAL EXPERIENCE

        Senior Software Engineer | Google | Mountain View, CA | 2021 - Present
        • Architected microservices infrastructure supporting 10M+ concurrent users
        • Optimized search algorithms achieving 50% improvement in query response time
        • Led technical design reviews for 20+ engineering projects across 5 teams
        • Implemented automated testing framework reducing production bugs by 70%
        • Mentored 8 junior engineers on software development best practices

        Software Engineer | Facebook (Meta) | Menlo Park, CA | 2019 - 2021
        • Developed real-time messaging features used by 100M+ monthly active users
        • Built distributed caching system improving application performance by 35%
        • Collaborated with product managers to define technical requirements
        • Participated in code reviews ensuring high code quality standards

        Software Developer | Microsoft | Redmond, WA | 2017 - 2019
        • Created Azure cloud services handling 1TB+ daily data processing
        • Developed REST APIs serving 500K+ requests per minute
        • Implemented security protocols meeting SOC 2 compliance requirements
        • Contributed to open-source projects with 10K+ GitHub stars

        EDUCATION
        Stanford University | Stanford, CA
        Master of Science in Computer Science | 2017
        Specialization: Artificial Intelligence and Machine Learning

        University of California, Berkeley | Berkeley, CA
        Bachelor of Science in Computer Science | 2015
        Magna Cum Laude, GPA: 3.9/4.0

        CERTIFICATIONS
        • AWS Certified Solutions Architect - Professional (2023)
        • Certified Kubernetes Administrator (CKA) (2022)
        • Google Cloud Professional Developer (2021)

        ACHIEVEMENTS
        • Published 5 technical papers in IEEE Software Engineering journals
        • Speaker at 10+ industry conferences including DockerCon and KubeCon
        • Patent holder for "Distributed Cache Optimization Algorithm" (US Patent #11,234,567)
        """

    @staticmethod
    def get_format_issues_resume() -> str:
        """
        Resume with formatting issues to test FormatStructureAgent.
        Contains inconsistent formatting, poor section organization.
        """
        return """
john doe
software engineer
john@email.com
phone: 123-456-7890

education
university of technology - computer science (2020)

work experience:
TechCompany Inc.
Software Developer (2020-2023)
-worked on web applications
-used python and javascript
-fixed bugs and added features

internship
Summer Intern at StartupCo (2019)
• helped with development tasks
• learned new technologies
• worked on team projects

Skills:
python, javascript, html, css, react, node.js, sql, git

projects
1. Weather App - built using react and api integration
2. E-commerce Site - full stack application with payment processing
3. blog platform - content management system

other stuff:
hobbies include reading and gaming
references available upon request
        """

    @staticmethod
    def get_skills_mismatch_resume() -> str:
        """
        Resume with skills mismatch for testing SkillsAssessmentAgent.
        Contains outdated technologies and irrelevant skills.
        """
        return """
        ROBERT WILSON
        Software Developer
        robert.wilson@email.com | (555) 234-5678

        EDUCATION
        Community College - Associate Degree in Computer Science | 2015

        TECHNICAL SKILLS
        Programming Languages: Visual Basic, Pascal, COBOL, Fortran
        Web Technologies: HTML, CSS, jQuery, PHP 4
        Databases: Microsoft Access, FoxPro
        Operating Systems: Windows 95, Windows XP
        Development Tools: Dreamweaver, FrontPage
        Other: Microsoft Office, Typing (60 WPM)

        WORK EXPERIENCE
        IT Support Technician | Small Business Corp | 2015 - Present
        • Fixed computer hardware issues
        • Installed software on office computers
        • Maintained company printers and fax machines
        • Created simple websites using HTML and CSS
        • Managed email accounts for 20 employees

        Computer Repair Technician | Local Computer Shop | 2013 - 2015
        • Diagnosed hardware problems
        • Replaced computer components
        • Cleaned virus infections
        • Set up home networks
        • Provided technical support to customers

        PERSONAL PROJECTS
        Company Website | 2018
        Built basic website for local restaurant using HTML and CSS.
        Added contact form using PHP for customer inquiries.

        Excel Automation | 2017
        Created macros in Excel to automate data entry tasks.
        Reduced manual work time by organizing spreadsheet formulas.
        """

    @staticmethod
    def get_red_flag_resume() -> str:
        """
        Resume with red flags for testing RedFlagDetectionAgent.
        Contains employment gaps, job hopping, inconsistencies.
        """
        return """
        ALEX THOMPSON
        Senior Software Architect
        alex.thompson@email.com | (555) 345-6789

        OBJECTIVE
        Seeking a challenging position as a CTO or VP of Engineering
        to leverage my extensive 15+ years of experience.

        EDUCATION
        Harvard University - PhD in Computer Science | 1995
        MIT - Master's in Software Engineering | 1993
        Stanford University - Bachelor's in Computer Science | 1991

        WORK EXPERIENCE

        CTO | StartupXYZ | San Francisco, CA | 2023 - 2023
        • Led engineering team of 100+ developers
        • Scaled platform to serve 50M+ users
        • Reduced infrastructure costs by 90%
        • Increased company valuation to $10B

        Senior Architect | TechGiant Corp | Seattle, WA | 2022 - 2022
        • Designed enterprise architecture for Fortune 500 clients
        • Managed technical teams across 15 countries
        • Delivered $100M+ projects on time and under budget

        Lead Engineer | CloudCorp | Austin, TX | 2021 - 2021
        • Built distributed systems handling petabytes of data
        • Optimized algorithms achieving 1000% performance improvement
        • Led migration of legacy systems to cloud-native architecture

        Software Developer | WebSolutions Inc | New York, NY | 2015 - 2020
        • Developed web applications using various technologies
        • Worked on multiple client projects
        • Gained experience in full-stack development

        [Employment Gap: 2010 - 2015]

        Senior Developer | OldTech Systems | Boston, MA | 2005 - 2010
        • Maintained legacy COBOL applications
        • Worked on Y2K compliance projects
        • Updated mainframe systems

        TECHNICAL SKILLS
        Expert in all programming languages and frameworks
        Advanced knowledge of quantum computing and AI
        Certified in 50+ cloud platforms and technologies
        Inventor of proprietary algorithms (patents pending)

        ACHIEVEMENTS
        • Published 100+ research papers in top-tier journals
        • Keynote speaker at major conferences worldwide
        • Recognized as "Developer of the Year" by IEEE (2019)
        • Created programming language adopted by Google and Microsoft
        """

    @staticmethod
    def get_user_context_software_engineer() -> Dict[str, Any]:
        """Standard user context for software engineer role testing."""
        return {
            'user_id': 'test-user-123',
            'evaluation_id': 'eval-456',
            'target_roles': ['Software Engineer', 'Backend Developer', 'Full Stack Developer'],
            'target_seniority': 'mid_level',
            'current_date': 'October 2024',
            'current_year': 2024,
            'years_experience': 4,
            'target_companies': ['maang', 'startups', 'enterprise'],
            'location_preference': 'San Francisco, CA',
            'salary_expectation': '$120,000 - $150,000',
            'visa_status': 'US Citizen',
            'remote_preference': 'hybrid',
            'industries': ['technology', 'fintech', 'healthtech']
        }

    @staticmethod
    def get_user_context_senior_role() -> Dict[str, Any]:
        """User context for senior-level position testing."""
        return {
            'user_id': 'senior-test-456',
            'evaluation_id': 'eval-789',
            'target_roles': ['Senior Software Engineer', 'Tech Lead', 'Principal Engineer'],
            'target_seniority': 'senior',
            'current_date': 'October 2024',
            'current_year': 2024,
            'years_experience': 8,
            'target_companies': ['maang', 'unicorn_startups'],
            'location_preference': 'New York, NY',
            'salary_expectation': '$180,000 - $250,000',
            'visa_status': 'H1B',
            'remote_preference': 'remote_only',
            'industries': ['fintech', 'crypto', 'ai_ml']
        }

    @staticmethod
    def get_user_context_entry_level() -> Dict[str, Any]:
        """User context for entry-level position testing."""
        return {
            'user_id': 'entry-test-789',
            'evaluation_id': 'eval-012',
            'target_roles': ['Junior Software Engineer', 'Software Developer I', 'Associate Developer'],
            'target_seniority': 'entry_level',
            'current_date': 'October 2024',
            'current_year': 2024,
            'years_experience': 1,
            'target_companies': ['startups', 'mid_size', 'consultancies'],
            'location_preference': 'Austin, TX',
            'salary_expectation': '$70,000 - $95,000',
            'visa_status': 'Student (OPT)',
            'remote_preference': 'office_preferred',
            'industries': ['technology', 'gaming', 'e_commerce']
        }

    @classmethod
    def get_all_test_cases(cls) -> Dict[str, Dict[str, Any]]:
        """Get all test cases with resumes and contexts."""
        return {
            'harvard_compliant': {
                'resume': cls.get_harvard_compliant_resume(),
                'context': cls.get_user_context_software_engineer(),
                'expected_scores': {
                    'harvard_compliance': 95,  # Should score very high
                    'ats': 85,
                    'format': 90,
                    'experience': 85
                },
                'description': 'Harvard Career Services compliant resume'
            },
            'harvard_violations': {
                'resume': cls.get_harvard_violation_resume(),
                'context': cls.get_user_context_entry_level(),
                'expected_scores': {
                    'harvard_compliance': 25,  # Should score very low
                    'ats': 40,
                    'format': 35,
                    'red_flags': 8  # High red flag count
                },
                'description': 'Resume with multiple Harvard violations'
            },
            'ats_optimized': {
                'resume': cls.get_ats_optimized_resume(),
                'context': cls.get_user_context_senior_role(),
                'expected_scores': {
                    'ats': 95,  # Should score very high
                    'skills': 90,
                    'experience': 85,
                    'harvard_compliance': 80
                },
                'description': 'ATS-optimized resume with proper keywords'
            },
            'format_issues': {
                'resume': cls.get_format_issues_resume(),
                'context': cls.get_user_context_entry_level(),
                'expected_scores': {
                    'format': 30,  # Should score very low
                    'ats': 35,
                    'harvard_compliance': 40,
                    'red_flags': 6
                },
                'description': 'Resume with significant formatting issues'
            },
            'skills_mismatch': {
                'resume': cls.get_skills_mismatch_resume(),
                'context': cls.get_user_context_software_engineer(),
                'expected_scores': {
                    'skills': 20,  # Should score very low
                    'experience': 40,
                    'company_fit': 25,
                    'harvard_compliance': 70
                },
                'description': 'Resume with outdated and irrelevant skills'
            },
            'red_flag_heavy': {
                'resume': cls.get_red_flag_resume(),
                'context': cls.get_user_context_senior_role(),
                'expected_scores': {
                    'red_flags': 15,  # High red flag score (negative impact)
                    'experience': 30,
                    'skills': 40,
                    'harvard_compliance': 60
                },
                'description': 'Resume with multiple red flags and inconsistencies'
            }
        }

    @staticmethod
    def get_harvard_test_samples() -> Dict[str, Dict[str, Any]]:
        """Specific test samples for Harvard Compliance Agent testing."""
        return {
            'personal_pronouns': {
                'text': "I am a software developer. My experience includes working with Python. I have led multiple teams.",
                'expected_violations': ['personal_pronouns'],
                'violation_count': 6  # I, My, I, with, I, teams
            },
            'passive_voice': {
                'text': "The project was completed by the team. Tasks were assigned by management. Code was reviewed by senior developers.",
                'expected_violations': ['passive_voice'],
                'violation_count': 3
            },
            'weak_action_verbs': {
                'text': "Responsible for database management. Involved in code reviews. Participated in team meetings.",
                'expected_violations': ['weak_action_verbs'],
                'violation_count': 3
            },
            'abbreviations': {
                'text': "Worked w/ APIs & DBs. Developed SW using ML & AI tech. Collaborated w/ PM & QA teams.",
                'expected_violations': ['abbreviations'],
                'violation_count': 8  # w/, &, DBs, SW, ML, AI, w/, PM, QA
            },
            'vague_descriptions': {
                'text': "Worked on various projects. Helped with different tasks. Contributed to team success.",
                'expected_violations': ['vague_descriptions'],
                'violation_count': 3
            },
            'clean_harvard_text': {
                'text': "Developed scalable microservices architecture. Led cross-functional team of 8 engineers. Reduced system latency by 40%.",
                'expected_violations': [],
                'violation_count': 0
            }
        }