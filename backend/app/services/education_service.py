"""
Education Service

Business logic for managing educational information and AI-powered analysis.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, datetime
import logging

from app.models.education import EducationRecord, Certification, OnlineCourse, AcademicProject
from app.schemas.education import (
    EducationRecordCreate,
    EducationRecordUpdate,
    EducationRecordResponse,
    CertificationCreate,
    CertificationResponse,
    OnlineCourseCreate,
    OnlineCourseResponse,
    AcademicProjectCreate,
    AcademicProjectResponse,
    EducationalProfileResponse,
    EducationJobMatchAnalysis
)
from app.core.ai_service import ai_service
from app.core.enhanced_logging import log_openai_request, log_openai_error

logger = logging.getLogger(__name__)


class EducationService:
    """Service for managing educational information and AI analysis"""

    def __init__(self, db: Session):
        self.db = db

    # Education Records CRUD
    def create_education_record(self, user_id: str, education_data: EducationRecordCreate) -> EducationRecordResponse:
        """Create a new education record"""
        try:
            education_record = EducationRecord(
                user_id=user_id,
                **education_data.dict()
            )

            # Calculate relevance score using AI
            if education_data.field_of_study and education_data.coursework:
                education_record.relevance_score = self._calculate_education_relevance(education_data)

            # Extract skills using AI
            if education_data.coursework or education_data.academic_projects:
                education_record.skills_extracted = self._extract_skills_from_education(education_data)

            self.db.add(education_record)
            self.db.commit()
            self.db.refresh(education_record)

            return EducationRecordResponse.from_orm(education_record)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create education record: {str(e)}")
            raise

    def get_education_records(
        self,
        user_id: str,
        is_current: Optional[bool] = None,
        degree_type: Optional[str] = None,
        field_of_study: Optional[str] = None
    ) -> List[EducationRecordResponse]:
        """Get education records with optional filtering"""
        query = self.db.query(EducationRecord).filter(EducationRecord.user_id == user_id)

        if is_current is not None:
            query = query.filter(EducationRecord.is_current == is_current)

        if degree_type:
            query = query.filter(EducationRecord.degree_type == degree_type)

        if field_of_study:
            query = query.filter(EducationRecord.field_of_study.ilike(f"%{field_of_study}%"))

        records = query.order_by(EducationRecord.start_date.desc()).all()
        return [EducationRecordResponse.from_orm(record) for record in records]

    def get_education_record_by_id(self, user_id: str, record_id: str) -> Optional[EducationRecordResponse]:
        """Get a specific education record"""
        record = self.db.query(EducationRecord).filter(
            and_(
                EducationRecord.user_id == user_id,
                EducationRecord.id == record_id
            )
        ).first()

        return EducationRecordResponse.from_orm(record) if record else None

    def update_education_record(
        self,
        user_id: str,
        record_id: str,
        education_data: EducationRecordUpdate
    ) -> Optional[EducationRecordResponse]:
        """Update an education record"""
        record = self.db.query(EducationRecord).filter(
            and_(
                EducationRecord.user_id == user_id,
                EducationRecord.id == record_id
            )
        ).first()

        if not record:
            return None

        try:
            # Update fields
            update_data = education_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(record, field, value)

            record.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(record)

            return EducationRecordResponse.from_orm(record)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update education record: {str(e)}")
            raise

    def delete_education_record(self, user_id: str, record_id: str) -> bool:
        """Delete an education record"""
        record = self.db.query(EducationRecord).filter(
            and_(
                EducationRecord.user_id == user_id,
                EducationRecord.id == record_id
            )
        ).first()

        if not record:
            return False

        try:
            self.db.delete(record)
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete education record: {str(e)}")
            raise

    # Certification CRUD
    def create_certification(self, user_id: str, cert_data: CertificationCreate) -> CertificationResponse:
        """Create a new certification"""
        try:
            certification = Certification(
                user_id=user_id,
                **cert_data.dict()
            )

            # Calculate market demand and salary impact using AI
            certification.market_demand_score = self._calculate_certification_market_demand(cert_data)
            certification.salary_impact_score = self._calculate_certification_salary_impact(cert_data)

            self.db.add(certification)
            self.db.commit()
            self.db.refresh(certification)

            return CertificationResponse.from_orm(certification)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create certification: {str(e)}")
            raise

    def get_certifications(
        self,
        user_id: str,
        is_active: Optional[bool] = True,
        certification_type: Optional[str] = None
    ) -> List[CertificationResponse]:
        """Get certifications with optional filtering"""
        query = self.db.query(Certification).filter(Certification.user_id == user_id)

        if is_active is not None:
            query = query.filter(Certification.is_active == is_active)

        if certification_type:
            query = query.filter(Certification.certification_type == certification_type)

        certifications = query.order_by(Certification.issue_date.desc()).all()
        return [CertificationResponse.from_orm(cert) for cert in certifications]

    # Online Course CRUD
    def create_online_course(self, user_id: str, course_data: OnlineCourseCreate) -> OnlineCourseResponse:
        """Create a new online course record"""
        try:
            course = OnlineCourse(
                user_id=user_id,
                **course_data.dict()
            )

            # Calculate relevance score
            course.relevance_score = self._calculate_course_relevance(course_data)

            self.db.add(course)
            self.db.commit()
            self.db.refresh(course)

            return OnlineCourseResponse.from_orm(course)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create online course: {str(e)}")
            raise

    def get_online_courses(
        self,
        user_id: str,
        is_completed: Optional[bool] = None,
        provider: Optional[str] = None
    ) -> List[OnlineCourseResponse]:
        """Get online courses with optional filtering"""
        query = self.db.query(OnlineCourse).filter(OnlineCourse.user_id == user_id)

        if is_completed is not None:
            query = query.filter(OnlineCourse.is_completed == is_completed)

        if provider:
            query = query.filter(OnlineCourse.provider.ilike(f"%{provider}%"))

        courses = query.order_by(OnlineCourse.start_date.desc()).all()
        return [OnlineCourseResponse.from_orm(course) for course in courses]

    # Academic Project CRUD
    def create_academic_project(self, user_id: str, project_data: AcademicProjectCreate) -> AcademicProjectResponse:
        """Create a new academic project"""
        try:
            project = AcademicProject(
                user_id=user_id,
                **project_data.dict()
            )

            # Calculate complexity score using AI
            project.complexity_score = self._calculate_project_complexity(project_data)

            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)

            return AcademicProjectResponse.from_orm(project)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create academic project: {str(e)}")
            raise

    def get_academic_projects(
        self,
        user_id: str,
        project_type: Optional[str] = None
    ) -> List[AcademicProjectResponse]:
        """Get academic projects with optional filtering"""
        query = self.db.query(AcademicProject).filter(AcademicProject.user_id == user_id)

        if project_type:
            query = query.filter(AcademicProject.project_type == project_type)

        projects = query.order_by(AcademicProject.start_date.desc()).all()
        return [AcademicProjectResponse.from_orm(project) for project in projects]

    # Comprehensive analysis
    def get_comprehensive_educational_profile(self, user_id: str) -> EducationalProfileResponse:
        """Get complete educational profile with AI-calculated scores"""
        education_records = self.get_education_records(user_id)
        certifications = self.get_certifications(user_id)
        online_courses = self.get_online_courses(user_id)
        academic_projects = self.get_academic_projects(user_id)

        # Calculate overall scores
        overall_education_score = self._calculate_overall_education_score(
            education_records, certifications, online_courses, academic_projects
        )

        return EducationalProfileResponse(
            education_records=education_records,
            certifications=certifications,
            online_courses=online_courses,
            academic_projects=academic_projects,
            overall_education_score=overall_education_score,
            skill_coverage_score=self._calculate_skill_coverage_score(
                education_records, certifications, online_courses
            ),
            market_alignment_score=self._calculate_market_alignment_score(
                education_records, certifications
            )
        )

    def analyze_education_job_match(
        self,
        user_id: str,
        job_title: str,
        job_description: str,
        job_requirements: str
    ) -> EducationJobMatchAnalysis:
        """Analyze how well user's education matches a job using AI"""
        try:
            # Get user's educational profile
            profile = self.get_comprehensive_educational_profile(user_id)

            # Use AI to analyze the match
            analysis = self._ai_analyze_education_job_match(
                profile, job_title, job_description, job_requirements
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze education job match: {str(e)}")
            # Return fallback analysis
            return EducationJobMatchAnalysis(
                education_match_score=50.0,
                degree_relevance_score=50.0,
                skills_match_score=50.0,
                experience_level_match=50.0,
                certification_bonus=0.0,
                institution_prestige_factor=1.0,
                recommendations=["Unable to analyze due to system error"],
                skill_gaps=["Analysis unavailable"],
                recommended_certifications=[]
            )

    # Private helper methods
    def _calculate_education_relevance(self, education_data: EducationRecordCreate) -> float:
        """Calculate relevance score for education record using AI"""
        try:
            # Simple scoring based on field of study and coursework
            base_score = 50.0

            # Tech-related fields get higher scores
            tech_fields = ["computer science", "software", "engineering", "technology", "data science"]
            if any(field in education_data.field_of_study.lower() for field in tech_fields):
                base_score += 20.0

            # More coursework increases relevance
            if education_data.coursework and len(education_data.coursework) > 5:
                base_score += 10.0

            return min(base_score, 100.0)

        except Exception as e:
            logger.warning(f"Failed to calculate education relevance: {str(e)}")
            return 50.0

    def _extract_skills_from_education(self, education_data: EducationRecordCreate) -> List[str]:
        """Extract skills from education data using AI"""
        try:
            skills = []

            # Extract from coursework
            if education_data.coursework:
                skills.extend(education_data.programming_languages_learned or [])
                skills.extend(education_data.frameworks_learned or [])
                skills.extend(education_data.tools_learned or [])

            # Extract from field of study
            field_skills = {
                "computer science": ["Programming", "Algorithms", "Data Structures"],
                "data science": ["Python", "Statistics", "Machine Learning"],
                "business": ["Management", "Analysis", "Strategy"],
                "engineering": ["Problem Solving", "Design", "Project Management"]
            }

            for field, field_skills_list in field_skills.items():
                if field in education_data.field_of_study.lower():
                    skills.extend(field_skills_list)

            return list(set(skills))  # Remove duplicates

        except Exception as e:
            logger.warning(f"Failed to extract skills from education: {str(e)}")
            return []

    def _calculate_certification_market_demand(self, cert_data: CertificationCreate) -> float:
        """Calculate market demand score for certification"""
        # High-demand certifications
        high_demand_certs = [
            "aws", "azure", "google cloud", "kubernetes", "docker",
            "pmp", "scrum", "agile", "cissp", "ceh", "python", "java"
        ]

        cert_name_lower = cert_data.name.lower()
        for high_demand in high_demand_certs:
            if high_demand in cert_name_lower:
                return 80.0

        return 60.0

    def _calculate_certification_salary_impact(self, cert_data: CertificationCreate) -> float:
        """Calculate salary impact score for certification"""
        # High-impact certifications for salary
        high_impact_certs = [
            "aws solutions architect", "azure architect", "google cloud architect",
            "pmp", "cissp", "ceh", "kubernetes", "docker"
        ]

        cert_name_lower = cert_data.name.lower()
        for high_impact in high_impact_certs:
            if high_impact in cert_name_lower:
                return 85.0

        return 65.0

    def _calculate_course_relevance(self, course_data: OnlineCourseCreate) -> float:
        """Calculate relevance score for online course"""
        base_score = 60.0

        # Tech courses are generally more relevant for our job matching
        tech_keywords = ["programming", "software", "web development", "data science", "machine learning"]
        if any(keyword in course_data.course_name.lower() for keyword in tech_keywords):
            base_score += 20.0

        # Popular providers get bonus points
        popular_providers = ["coursera", "udemy", "pluralsight", "edx", "udacity"]
        if course_data.provider.lower() in popular_providers:
            base_score += 10.0

        return min(base_score, 100.0)

    def _calculate_project_complexity(self, project_data: AcademicProjectCreate) -> float:
        """Calculate complexity score for academic project"""
        complexity_score = 50.0

        # More technologies used = higher complexity
        if project_data.technologies_used and len(project_data.technologies_used) > 3:
            complexity_score += 20.0

        # GitHub presence indicates serious project
        if project_data.github_url:
            complexity_score += 15.0

        # Demo URL indicates completed, deployable project
        if project_data.demo_url:
            complexity_score += 15.0

        return min(complexity_score, 100.0)

    def _calculate_overall_education_score(
        self,
        education_records: List[EducationRecordResponse],
        certifications: List[CertificationResponse],
        online_courses: List[OnlineCourseResponse],
        academic_projects: List[AcademicProjectResponse]
    ) -> float:
        """Calculate overall education score"""
        score = 0.0

        # Weight formal education heavily
        if education_records:
            formal_score = sum(record.relevance_score or 50 for record in education_records) / len(education_records)
            score += formal_score * 0.5

        # Certifications add significant value
        if certifications:
            cert_score = sum(cert.market_demand_score or 60 for cert in certifications) / len(certifications)
            score += cert_score * 0.3

        # Online courses and projects add additional value
        if online_courses:
            course_score = sum(course.relevance_score or 60 for course in online_courses) / len(online_courses)
            score += course_score * 0.1

        if academic_projects:
            project_score = sum(project.complexity_score or 50 for project in academic_projects) / len(academic_projects)
            score += project_score * 0.1

        return min(score, 100.0)

    def _calculate_skill_coverage_score(
        self,
        education_records: List[EducationRecordResponse],
        certifications: List[CertificationResponse],
        online_courses: List[OnlineCourseResponse]
    ) -> float:
        """Calculate skill coverage score based on education"""
        all_skills = set()

        # Collect skills from all sources
        for record in education_records:
            all_skills.update(record.technical_skills_gained or [])

        for cert in certifications:
            all_skills.update(cert.skills_validated or [])

        for course in online_courses:
            all_skills.update(course.skills_learned or [])

        # Score based on number and diversity of skills
        if len(all_skills) >= 15:
            return 90.0
        elif len(all_skills) >= 10:
            return 80.0
        elif len(all_skills) >= 5:
            return 70.0
        else:
            return 60.0

    def _calculate_market_alignment_score(
        self,
        education_records: List[EducationRecordResponse],
        certifications: List[CertificationResponse]
    ) -> float:
        """Calculate market alignment score"""
        score = 70.0  # Base score

        # Recent education gets bonus
        recent_education = any(
            record.graduation_date and record.graduation_date.year >= 2020
            for record in education_records
        )
        if recent_education:
            score += 15.0

        # Active certifications get bonus
        active_certs = len([cert for cert in certifications if cert.is_active])
        if active_certs >= 3:
            score += 15.0
        elif active_certs >= 1:
            score += 10.0

        return min(score, 100.0)

    async def _ai_analyze_education_job_match(
        self,
        profile: EducationalProfileResponse,
        job_title: str,
        job_description: str,
        job_requirements: str
    ) -> EducationJobMatchAnalysis:
        """Use AI to analyze education-job match"""
        try:
            prompt = f"""
            Analyze how well this educational profile matches the job requirements.

            Educational Profile:
            - Education Records: {len(profile.education_records)} degrees/programs
            - Certifications: {len(profile.certifications)} certifications
            - Online Courses: {len(profile.online_courses)} courses
            - Projects: {len(profile.academic_projects)} academic projects

            Job Details:
            Title: {job_title}
            Description: {job_description[:500]}
            Requirements: {job_requirements[:500]}

            Provide analysis in JSON format:
            {{
                "education_match_score": 0-100,
                "degree_relevance_score": 0-100,
                "skills_match_score": 0-100,
                "experience_level_match": 0-100,
                "certification_bonus": 0-20,
                "recommendations": ["recommendation1", "recommendation2"],
                "skill_gaps": ["gap1", "gap2"],
                "recommended_certifications": ["cert1", "cert2"]
            }}
            """

            response = await ai_service.get_completion(prompt, temperature=0.2)
            import json
            analysis_data = json.loads(response)

            return EducationJobMatchAnalysis(
                education_match_score=analysis_data.get("education_match_score", 70.0),
                degree_relevance_score=analysis_data.get("degree_relevance_score", 70.0),
                skills_match_score=analysis_data.get("skills_match_score", 70.0),
                experience_level_match=analysis_data.get("experience_level_match", 70.0),
                certification_bonus=analysis_data.get("certification_bonus", 0.0),
                institution_prestige_factor=1.0,
                recommendations=analysis_data.get("recommendations", []),
                skill_gaps=analysis_data.get("skill_gaps", []),
                recommended_certifications=analysis_data.get("recommended_certifications", [])
            )

        except Exception as e:
            log_openai_error("education_job_match_analysis", e)
            # Return fallback analysis
            return EducationJobMatchAnalysis(
                education_match_score=70.0,
                degree_relevance_score=70.0,
                skills_match_score=70.0,
                experience_level_match=70.0,
                certification_bonus=5.0,
                institution_prestige_factor=1.0,
                recommendations=["Continue developing technical skills", "Consider relevant certifications"],
                skill_gaps=["Analysis unavailable due to AI service error"],
                recommended_certifications=["Industry-relevant certifications recommended"]
            )