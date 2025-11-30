"""
Agentic Resume Evaluator Service.
Uses multiple specialized agents for comprehensive resume analysis.
"""

import os
import uuid
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import fitz  # PyMuPDF for PDF processing
from docx import Document
import re

from app.core.ai_service import AIService
import logging
from app.schemas.resume import ResumeEvaluationResult, AIEvaluationPrompt
from app.models.resume import Resume, ResumeEvaluation
from app.models.agent_models import ResumeEvaluationSession, ResumeAgentResult, AgentPerformanceMetrics
from app.services.agents import ResumeEvaluationOrchestrator
from app.services.orchestrator_manager import orchestrator_manager
from app.services.profile_service import ProfileService
from app.db.session import get_db

logger = logging.getLogger(__name__)


class AgenticResumeEvaluatorService:
    """Service for AI-powered resume evaluation using multiple specialized agents."""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.orchestrator = orchestrator_manager.get_orchestrator(ai_service)
        self.max_resumes_per_user = 5
    
    async def extract_resume_text(self, file_path: str, file_type: str) -> str:
        """Extract text content from resume file"""
        try:
            if file_type.lower() in ['pdf', 'application/pdf']:
                return self._extract_pdf_text(file_path)
            elif file_type.lower() in ['docx', 'doc', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
                return self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            raise
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX text extraction failed: {e}")
            raise
    
    def _preprocess_resume_text(self, text: str) -> str:
        """Clean and preprocess resume text for AI analysis"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might confuse AI
        text = re.sub(r'[^\w\s\-\.\,\!\?\(\)\:\;]', '', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        return text.strip()
    
    async def evaluate_resume(self, resume_text: str, user_id: str, resume_id: str, 
                            target_role: Optional[str] = None,
                            target_seniority: Optional[str] = None) -> ResumeEvaluationResult:
        """Main method to evaluate resume using agentic workflow"""
        try:
            start_time = datetime.now(timezone.utc)
            evaluation_id = str(uuid.uuid4())

            # Preprocess text
            cleaned_text = self._preprocess_resume_text(resume_text)

            # Fetch user profile information for enhanced evaluation
            db = next(get_db())
            try:
                profile = ProfileService.get_profile_with_stats(db, user_id)
                if profile is None:
                    logger.info(f"No profile found for user {user_id}, using default values")
                else:
                    logger.debug(f"Successfully fetched profile for user {user_id}")
            except Exception as e:
                logger.warning(f"Could not fetch profile for user {user_id}: {e}")
                profile = None
            finally:
                db.close()

            # Prepare enhanced user context with profile data
            current_date = datetime.now(timezone.utc)
            user_context = {
                'user_id': user_id,
                'resume_id': resume_id,
                'evaluation_id': resume_id,  # Use resume_id for progress tracking
                'current_date': current_date.strftime('%B %Y'),  # e.g., "October 2025"
                'current_year': current_date.year,
                'target_roles': profile.get('target_job_titles', []) if profile else ([target_role] if target_role else []),
                'target_seniority': (profile.get('experience_level') if profile else None) or target_seniority or 'mid-level',
                'preferred_locations': profile.get('preferred_locations', []) if profile else [],
                'minimum_salary': profile.get('minimum_salary') if profile else None,
                'background_summary': profile.get('background_summary') if profile else None,
                'work_experiences': profile.get('work_experiences', []) if profile else [],
                'education_history': profile.get('education_history', []) if profile else [],
                'years_experience': self._estimate_experience_years(cleaned_text),
                'target_companies': ['maang', 'startups', 'enterprise']  # Default to all
            }
            
            # Execute agentic evaluation
            logger.debug(f"Starting agentic evaluation for resume {resume_id} with user context keys: {list(user_context.keys())}")
            try:
                evaluation_results = await self.orchestrator.evaluate_resume(cleaned_text, user_context)
                if evaluation_results is None:
                    raise ValueError("Orchestrator returned None results")
                logger.debug(f"Orchestrator completed successfully with overall score: {evaluation_results.get('overall_score', 'unknown')}")
            except Exception as e:
                logger.error(f"Orchestrator evaluation failed for resume {resume_id}: {e}")
                raise
            
            # Store evaluation session and agent results
            await self._store_evaluation_results(evaluation_results, user_id, resume_id)
            
            # Convert to legacy format for compatibility
            legacy_result = self._convert_to_legacy_format(evaluation_results)
            
            # Calculate processing time
            processing_time = int((datetime.now(timezone.utc) - start_time).total_seconds())
            legacy_result.processing_time = processing_time
            
            logger.info(f"Agentic resume evaluation completed in {processing_time}s with score {legacy_result.overall_score}")
            return legacy_result
            
        except Exception as e:
            logger.error(f"Agentic resume evaluation failed: {e}")
            raise
    
    def _estimate_experience_years(self, resume_text: str) -> int:
        """Estimate years of experience from resume text"""
        # Simple heuristic - look for years in experience section
        years_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|\bpresent\b|\bcurrent\b)'
        matches = re.findall(years_pattern, resume_text, re.IGNORECASE)
        
        if not matches:
            return 0
        
        # Calculate total years (simplified)
        total_years = 0
        current_year = datetime.now(timezone.utc).year
        
        for start_year, end_year in matches:
            try:
                start = int(start_year)
                if end_year.lower() in ['present', 'current']:
                    end = current_year
                else:
                    end = int(end_year)
                
                if start <= end:
                    total_years += (end - start)
            except ValueError:
                continue
        
        return min(total_years, 20)  # Cap at 20 years
    
    async def _store_evaluation_results(self, evaluation_results: Dict[str, Any], 
                                      user_id: str, resume_id: str) -> None:
        """Store evaluation results in database"""
        try:
            db = next(get_db())
            
            # Create evaluation session
            session = ResumeEvaluationSession(
                id=evaluation_results['evaluation_id'],
                user_id=user_id,
                resume_id=resume_id,
                evaluation_type='agentic',
                overall_score=evaluation_results['overall_score'],
                executive_summary=evaluation_results['summary'].get('executive_summary', ''),
                processing_time_seconds=evaluation_results['processing_time_seconds'],
                successful_agents=evaluation_results['metrics']['successful_agents'],
                total_agents=evaluation_results['metrics']['total_agents'],
                confidence_percentage=evaluation_results['metrics']['confidence_percentage'],
                evaluation_data=evaluation_results
            )
            
            db.add(session)
            
            # Store individual agent results
            for agent_name, agent_result in evaluation_results['agent_results'].items():
                agent_result_record = ResumeAgentResult(
                    id=str(uuid.uuid4()),
                    evaluation_id=evaluation_results['evaluation_id'],
                    agent_name=agent_name,
                    agent_results=agent_result,
                    execution_time_ms=agent_result.get('execution_time_ms'),
                    success=not agent_result.get('error', False) and not agent_result.get('fallback', False),
                    error_message=agent_result.get('error', '')
                )
                
                db.add(agent_result_record)
            
            # Update agent performance metrics
            await self._update_agent_performance_metrics(evaluation_results['agent_performance'])
            
            db.commit()
            logger.info(f"Stored evaluation results for session {evaluation_results['evaluation_id']}")
            
        except Exception as e:
            logger.error(f"Failed to store evaluation results: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    async def _update_agent_performance_metrics(self, agent_performance: Dict[str, Any]) -> None:
        """Update agent performance metrics"""
        try:
            db = next(get_db())
            
            for agent_name, performance in agent_performance.items():
                # Get or create metrics record
                metrics = db.query(AgentPerformanceMetrics).filter(
                    AgentPerformanceMetrics.agent_name == agent_name
                ).first()
                
                if not metrics:
                    metrics = AgentPerformanceMetrics(agent_name=agent_name)
                    db.add(metrics)
                
                # Update metrics
                metrics.total_executions = (metrics.total_executions or 0) + 1
                if performance['success']:
                    # Update success rate
                    current_successes = metrics.total_executions * (metrics.success_rate or 1.0)
                    metrics.success_rate = (current_successes + 1) / metrics.total_executions
                else:
                    # Decrease success rate
                    current_successes = metrics.total_executions * (metrics.success_rate or 1.0)
                    metrics.success_rate = current_successes / metrics.total_executions
                
                # Update execution time (simplified average)
                if performance.get('execution_time_ms'):
                    if metrics.avg_execution_time_ms is not None:
                        metrics.avg_execution_time_ms = (
                            metrics.avg_execution_time_ms + performance['execution_time_ms']
                        ) / 2
                    else:
                        metrics.avg_execution_time_ms = performance['execution_time_ms']
                
                metrics.last_execution = datetime.now(timezone.utc)
                metrics.last_updated = datetime.now(timezone.utc)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update agent performance metrics: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def _convert_to_legacy_format(self, evaluation_results: Dict[str, Any]) -> ResumeEvaluationResult:
        """Convert agentic results to legacy ResumeEvaluationResult format"""
        summary = evaluation_results.get('summary', {})
        agent_results = evaluation_results.get('agent_results', {})
        
        # Extract scores from individual agents
        ats_score = self._extract_agent_score(agent_results.get('ats', {}), 'ats_score', 0)
        experience_score = self._extract_agent_score(agent_results.get('experience', {}), 'experience_score', 0)
        skills_score = self._extract_agent_score(agent_results.get('skills', {}), 'skills_score', 0)
        format_score = self._extract_agent_score(agent_results.get('format', {}), 'format_score', 0)
        red_flag_score = self._extract_agent_score(agent_results.get('red_flags', {}), 'red_flag_score', 0)
        
        # Extract detailed analysis results for enhanced feedback
        detailed_analysis = agent_results.get('detailed_analysis', {})
        detailed_score_breakdown = detailed_analysis.get('score_breakdown', {})
        specific_fixes = detailed_analysis.get('specific_fixes', {})
        timeline_analysis = detailed_analysis.get('timeline_analysis', {})
        ats_issues = detailed_analysis.get('ats_issues', {})
        content_improvements = detailed_analysis.get('content_improvements', {})
        
        # Calculate weighted scores (matching legacy format)
        content_quality_score = int((experience_score + skills_score) / 2)
        quality_checks_score = int((format_score + max(0, 10 - red_flag_score)) / 2)
        
        # Extract strengths and improvements from detailed analysis
        strengths = detailed_analysis.get('strengths', summary.get('strengths', []))
        if isinstance(strengths, list) and strengths:
            strengths = [s.get('strength', str(s)) if isinstance(s, dict) else str(s) for s in strengths]
        else:
            strengths = ['Resume analysis completed']
        
        # Extract improvements from detailed analysis with specific fixes
        improvements = []
        
        # Add immediate fixes with specific examples
        immediate_fixes = specific_fixes.get('immediate_fixes', [])
        for item in immediate_fixes:
            if isinstance(item, dict):
                fix_text = f"{item.get('issue', '')} - {item.get('fix', '')}"
                if item.get('example'):
                    fix_text += f" (Example: {item.get('example')})"
                improvements.append(fix_text)
            else:
                improvements.append(str(item))
        
        # Add strategic improvements
        strategic_improvements = specific_fixes.get('strategic_improvements', [])
        for item in strategic_improvements:
            if isinstance(item, dict):
                improvement_text = f"{item.get('improvement', '')} - {item.get('action', '')}"
                if item.get('example'):
                    improvement_text += f" (Example: {item.get('example')})"
                improvements.append(improvement_text)
            else:
                improvements.append(str(item))
        
        # Fallback to summary if no detailed analysis
        if not improvements:
            critical_improvements = summary.get('critical_improvements', {})
            if isinstance(critical_improvements, dict):
                immediate_fixes = critical_improvements.get('immediate_fixes', [])
                strategic_improvements = critical_improvements.get('strategic_improvements', [])
                
                for item in immediate_fixes:
                    if isinstance(item, dict):
                        improvements.append(item.get('issue', str(item)))
                    else:
                        improvements.append(str(item))
                
                for item in strategic_improvements:
                    if isinstance(item, dict):
                        improvements.append(item.get('improvement', str(item)))
                    else:
                        improvements.append(str(item))
        
        # Extract ATS compatibility
        ats_compatibility = 'fair'
        if 'ats' in agent_results:
            ats_data = agent_results['ats']
            if isinstance(ats_data, dict) and 'ats_compatibility' in ats_data:
                ats_compatibility = ats_data['ats_compatibility']
        
        # Extract keyword analysis
        keyword_analysis = {'relevant': [], 'missing': [], 'score': 0}
        if 'ats' in agent_results and 'keyword_optimization' in agent_results['ats']:
            ko = agent_results['ats']['keyword_optimization']
            keyword_analysis = {
                'relevant': ko.get('missing_keywords', []),
                'missing': ko.get('missing_keywords', []),
                'score': ko.get('score', 0)
            }
        
        # Extract market positioning
        market_positioning = summary.get('market_positioning', {})
        company_fit = market_positioning.get('company_fit', {})
        
        return ResumeEvaluationResult(
            overall_score=evaluation_results.get('overall_score', 0),
            ats_compliance_score=ats_score,
            content_quality_score=content_quality_score,
            experience_points_score=experience_score,
            job_relevance_score=skills_score,
            quality_checks_score=quality_checks_score,
            strengths=strengths,
            improvements=improvements,
            detailed_feedback=detailed_analysis.get('executive_summary', summary.get('executive_summary', 'Resume evaluation completed')),
            ats_compatibility=ats_compatibility,
            keyword_analysis=keyword_analysis,
            critical_issues={
                'immediate_fixes': [
                    f"{item.get('issue', '')} - {item.get('fix', '')}" + 
                    (f" (Example: {item.get('example')})" if item.get('example') else "")
                    for item in specific_fixes.get('immediate_fixes', [])
                ] if specific_fixes.get('immediate_fixes') else [
                    item.get('issue', str(item)) if isinstance(item, dict) else str(item) 
                    for item in critical_improvements.get('immediate_fixes', [])
                ],
                'strategic_improvements': [
                    f"{item.get('improvement', '')} - {item.get('action', '')}" + 
                    (f" (Example: {item.get('example')})" if item.get('example') else "")
                    for item in specific_fixes.get('strategic_improvements', [])
                ] if specific_fixes.get('strategic_improvements') else [
                    item.get('improvement', str(item)) if isinstance(item, dict) else str(item) 
                    for item in critical_improvements.get('strategic_improvements', [])
                ],
                'nice_to_have': [
                    f"{item.get('enhancement', '')} - {item.get('action', '')}" + 
                    (f" (Example: {item.get('example')})" if item.get('example') else "")
                    for item in specific_fixes.get('nice_to_have', [])
                ] if specific_fixes.get('nice_to_have') else [
                    item.get('enhancement', str(item)) if isinstance(item, dict) else str(item) 
                    for item in critical_improvements.get('nice_to_have', [])
                ],
                'timeline_issues': [
                    f"{item.get('issue', '')} - Current: {item.get('current', '')} → Should be: {item.get('should_be', '')}"
                    for item in timeline_analysis.get('issues_found', [])
                ],
                'ats_critical_fixes': [
                    f"{item.get('issue', '')} - {item.get('fix', '')}" + 
                    (f" (Example: {item.get('example')})" if item.get('example') else "")
                    for item in ats_issues.get('critical_fixes', [])
                ]
            },
            market_positioning={
                'current_level': detailed_analysis.get('market_positioning', {}).get('competitive_level', market_positioning.get('competitive_level', 'Unknown')),
                'salary_range': detailed_analysis.get('market_positioning', {}).get('salary_range', market_positioning.get('salary_range', 'To be determined')),
                'target_roles': detailed_analysis.get('market_positioning', {}).get('target_roles', market_positioning.get('target_roles', ['General roles'])),
                'company_fit': {
                    'maang_companies': company_fit.get('maang', {}).get('score', 5),
                    'startups': company_fit.get('startups', {}).get('score', 5),
                    'enterprise': company_fit.get('enterprise', {}).get('score', 5)
                },
                'differentiation_factors': detailed_analysis.get('market_positioning', {}).get('differentiation_factors', []),
                'market_competitiveness': detailed_analysis.get('market_positioning', {}).get('market_competitiveness', 'medium')
            },
            evaluated_at=datetime.now(timezone.utc),
            ai_model_version='agentic-multi-agent',
            processing_time=0  # Will be set by caller
        )
    
    def _extract_agent_score(self, agent_result: Dict[str, Any], score_field: str, default: int) -> int:
        """Extract score from agent result"""
        if not isinstance(agent_result, dict):
            return default
        
        score = agent_result.get(score_field, default)
        if isinstance(score, (int, float)):
            return int(score)
        
        return default
    
    async def validate_resume_storage_limit(self, user_id: str, current_count: int) -> bool:
        """Check if user can upload more resumes"""
        return current_count < self.max_resumes_per_user
    
    async def cleanup_old_resumes(self, user_id: str, keep_count: int = None) -> List[str]:
        """Remove old resumes to maintain storage limit"""
        if keep_count is None:
            keep_count = self.max_resumes_per_user
        
        try:
            db = next(get_db())
            
            # Get user's resumes ordered by upload date
            resumes = db.query(Resume).filter(
                Resume.user_id == user_id
            ).order_by(Resume.uploaded_at.desc()).all()
            
            if len(resumes) <= keep_count:
                return []
            
            # Get resumes to delete
            resumes_to_delete = resumes[keep_count:]
            resume_ids_to_delete = [r.id for r in resumes_to_delete]
            
            # Delete associated evaluation sessions and agent results
            for resume in resumes_to_delete:
                # Delete agent results
                db.query(ResumeAgentResult).join(ResumeEvaluationSession).filter(
                    ResumeEvaluationSession.resume_id == resume.id
                ).delete(synchronize_session=False)
                
                # Delete evaluation sessions
                db.query(ResumeEvaluationSession).filter(
                    ResumeEvaluationSession.resume_id == resume.id
                ).delete()
                
                # Delete resume evaluations
                db.query(ResumeEvaluation).filter(
                    ResumeEvaluation.resume_id == resume.id
                ).delete()
            
            # Delete resumes
            db.query(Resume).filter(Resume.id.in_(resume_ids_to_delete)).delete()
            
            db.commit()
            logger.info(f"Cleaned up {len(resume_ids_to_delete)} old resumes for user {user_id}")
            
            return resume_ids_to_delete
            
        except Exception as e:
            logger.error(f"Failed to cleanup old resumes: {e}")
            db.rollback()
            return []
        finally:
            db.close()
    
    async def get_agent_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        try:
            db = next(get_db())
            
            metrics = db.query(AgentPerformanceMetrics).all()
            
            return {
                agent.agent_name: {
                    'total_executions': agent.total_executions,
                    'success_rate': agent.success_rate,
                    'avg_execution_time_ms': agent.avg_execution_time_ms,
                    'last_execution': agent.last_execution.isoformat() if agent.last_execution else None,
                    'last_updated': agent.last_updated.isoformat()
                }
                for agent in metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent performance metrics: {e}")
            return {}
        finally:
            db.close()
    
    async def get_evaluation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get evaluation history for a user"""
        try:
            db = next(get_db())
            
            sessions = db.query(ResumeEvaluationSession).filter(
                ResumeEvaluationSession.user_id == user_id
            ).order_by(ResumeEvaluationSession.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'evaluation_id': session.id,
                    'resume_id': session.resume_id,
                    'overall_score': session.overall_score,
                    'executive_summary': session.executive_summary,
                    'processing_time_seconds': session.processing_time_seconds,
                    'successful_agents': session.successful_agents,
                    'total_agents': session.total_agents,
                    'confidence_percentage': session.confidence_percentage,
                    'created_at': session.created_at.isoformat()
                }
                for session in sessions
            ]
            
        except Exception as e:
            logger.error(f"Failed to get evaluation history: {e}")
            return []
        finally:
            db.close()
