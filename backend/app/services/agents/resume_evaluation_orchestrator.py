"""
Resume Evaluation Orchestrator.
Coordinates multiple specialized agents for comprehensive resume analysis.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.ai_service import AIService
from .base_agent import BaseAgent
from .ats_compatibility_agent import ATSCompatibilityAgent
from .experience_analysis_agent import ExperienceAnalysisAgent
from .skills_assessment_agent import SkillsAssessmentAgent
from .format_structure_agent import FormatStructureAgent
from .red_flag_detection_agent import RedFlagDetectionAgent
from .company_fit_agent import CompanyFitAgent
from .summary_generator_agent import SummaryGeneratorAgent
from .detailed_analysis_agent import DetailedAnalysisAgent


class ResumeEvaluationOrchestrator:
    """Orchestrates multiple agents for comprehensive resume evaluation."""
    
    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service or AIService()
        self.logger = logging.getLogger(__name__)
        
        # Initialize all agents
        self.agents = {
            'ats': ATSCompatibilityAgent(self.ai_service),
            'experience': ExperienceAnalysisAgent(self.ai_service),
            'skills': SkillsAssessmentAgent(self.ai_service),
            'format': FormatStructureAgent(self.ai_service),
            'red_flags': RedFlagDetectionAgent(self.ai_service),
            'company_fit': CompanyFitAgent(self.ai_service),
            'detailed_analysis': DetailedAnalysisAgent(self.ai_service),
            'summary': SummaryGeneratorAgent(self.ai_service)
        }
        
        # Agent execution configuration
        self.agent_timeouts = {
            'ats': 30,
            'experience': 45,
            'skills': 30,
            'format': 25,
            'red_flags': 35,
            'company_fit': 40,
            'detailed_analysis': 90,
            'summary': 60
        }
        
        # Agent weights for overall score calculation
        self.agent_weights = {
            'ats': 0.15,
            'experience': 0.35,
            'skills': 0.15,
            'format': 0.10,
            'red_flags': -0.20,  # Negative weight for penalties
            'company_fit': 0.10,
            'detailed_analysis': 0.20  # High weight for detailed analysis
        }
    
    async def evaluate_resume(self, resume_content: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comprehensive resume evaluation using multiple agents.
        
        Args:
            resume_content: The resume text to analyze
            user_context: User context including target roles, preferences, etc.
            
        Returns:
            Comprehensive evaluation results
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info(f"Starting resume evaluation for user {user_context.get('user_id', 'unknown')}")
        
        try:
            # Step 1: Execute analysis agents in parallel
            analysis_results = await self._execute_analysis_agents(resume_content, user_context)
            
            # Step 2: Generate comprehensive summary
            summary_result = await self._generate_summary(analysis_results, user_context)
            
            # Step 3: Calculate overall metrics
            evaluation_metrics = self._calculate_evaluation_metrics(analysis_results, summary_result)
            
            # Step 4: Compile final results
            final_results = {
                'evaluation_id': user_context.get('evaluation_id'),
                'user_id': user_context.get('user_id'),
                'overall_score': summary_result.get('overall_score', 0),
                'executive_summary': summary_result.get('executive_summary', ''),
                'agent_results': analysis_results,
                'summary': summary_result,
                'metrics': evaluation_metrics,
                'evaluation_timestamp': datetime.now(timezone.utc).isoformat(),
                'processing_time_seconds': (datetime.now(timezone.utc) - start_time).total_seconds(),
                'agent_performance': self._get_agent_performance_metrics(analysis_results)
            }
            
            self.logger.info(f"Resume evaluation completed in {final_results['processing_time_seconds']:.2f} seconds")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Resume evaluation failed: {e}")
            return self._get_fallback_evaluation(user_context, str(e))
    
    async def _execute_analysis_agents(self, resume_content: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all analysis agents in parallel with timeout protection."""
        analysis_agents = {k: v for k, v in self.agents.items() if k != 'summary'}
        
        # Create tasks for parallel execution
        tasks = []
        for agent_name, agent in analysis_agents.items():
            task = self._execute_agent_with_timeout(
                agent, resume_content, user_context, self.agent_timeouts[agent_name]
            )
            tasks.append((agent_name, task))
        
        # Execute all agents in parallel
        results = {}
        completed_tasks = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # Process results
        for i, (agent_name, task) in enumerate(tasks):
            result = completed_tasks[i]
            if isinstance(result, Exception):
                self.logger.error(f"Agent {agent_name} failed: {result}")
                results[agent_name] = self._get_agent_fallback_result(agent_name, str(result))
            else:
                results[agent_name] = result
        
        return results
    
    async def _execute_agent_with_timeout(self, agent: BaseAgent, resume_content: str, 
                                        user_context: Dict[str, Any], timeout_seconds: int) -> Dict[str, Any]:
        """Execute a single agent with timeout protection."""
        try:
            result = await asyncio.wait_for(
                agent.execute_with_timeout(resume_content, user_context, timeout_seconds),
                timeout=timeout_seconds
            )
            
            # Validate result
            if agent.validate_result(result):
                return result
            else:
                self.logger.warning(f"Agent {agent.agent_name} returned invalid result")
                return self._get_agent_fallback_result(agent.agent_name, "Invalid result structure")
                
        except asyncio.TimeoutError:
            self.logger.error(f"Agent {agent.agent_name} timed out after {timeout_seconds} seconds")
            return self._get_agent_fallback_result(agent.agent_name, "Timeout")
        except Exception as e:
            self.logger.error(f"Agent {agent.agent_name} execution failed: {e}")
            return self._get_agent_fallback_result(agent.agent_name, str(e))
    
    async def _generate_summary(self, analysis_results: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary using the summary agent."""
        try:
            summary_agent = self.agents['summary']
            result = await asyncio.wait_for(
                summary_agent.generate(analysis_results, user_context),
                timeout=self.agent_timeouts['summary']
            )
            
            if summary_agent.validate_result(result):
                return result
            else:
                return self._get_summary_fallback_result(analysis_results)
                
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return self._get_summary_fallback_result(analysis_results)
    
    def _calculate_evaluation_metrics(self, analysis_results: Dict[str, Any], summary_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall evaluation metrics."""
        try:
            # Calculate weighted score from individual agent scores
            weighted_score = 0
            total_weight = 0
            
            for agent_name, weight in self.agent_weights.items():
                if agent_name in analysis_results:
                    agent_score = self._extract_agent_score(analysis_results[agent_name], agent_name)
                    if agent_score is not None:
                        weighted_score += agent_score * weight
                        total_weight += abs(weight)
            
            # Normalize score
            if total_weight > 0:
                normalized_score = (weighted_score / total_weight) * 100
            else:
                normalized_score = 0
            
            # Calculate confidence based on successful agent executions
            successful_agents = sum(1 for result in analysis_results.values() 
                                 if not result.get('error', False) and not result.get('fallback', False))
            total_agents = len(analysis_results)
            confidence = (successful_agents / total_agents) * 100 if total_agents > 0 else 0
            
            return {
                'weighted_score': round(normalized_score, 1),
                'confidence_percentage': round(confidence, 1),
                'successful_agents': successful_agents,
                'total_agents': total_agents,
                'agent_scores': {
                    agent_name: self._extract_agent_score(result, agent_name)
                    for agent_name, result in analysis_results.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating evaluation metrics: {e}")
            return {
                'weighted_score': 0,
                'confidence_percentage': 0,
                'successful_agents': 0,
                'total_agents': len(analysis_results),
                'error': str(e)
            }
    
    def _extract_agent_score(self, agent_result: Dict[str, Any], agent_name: str) -> Optional[float]:
        """Extract score from agent result."""
        score_fields = {
            'ats': 'ats_score',
            'experience': 'experience_score',
            'skills': 'skills_score',
            'format': 'format_score',
            'red_flags': 'red_flag_score',
            'company_fit': 'company_fit_scores',
            'detailed_analysis': 'overall_score'
        }
        
        score_field = score_fields.get(agent_name)
        if score_field and score_field in agent_result:
            score = agent_result[score_field]
            if isinstance(score, dict) and 'maang' in score:
                # Company fit agent returns multiple scores, use average
                scores = [v.get('score', 0) for v in score.values() if isinstance(v, dict) and 'score' in v]
                return sum(scores) / len(scores) if scores else 0
            elif isinstance(score, (int, float)):
                return float(score)
        
        return None
    
    def _get_agent_fallback_result(self, agent_name: str, error_message: str) -> Dict[str, Any]:
        """Get fallback result for failed agent."""
        return {
            'agent_name': agent_name,
            'error': error_message,
            'fallback': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'score': 0
        }
    
    def _get_summary_fallback_result(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback summary when summary agent fails."""
        return {
            'overall_score': 50,  # Neutral score
            'executive_summary': 'Resume evaluation completed with partial results due to technical issues.',
            'strengths': ['Analysis completed with available data'],
            'critical_improvements': {
                'immediate_fixes': ['Resume evaluation system needs attention'],
                'strategic_improvements': [],
                'nice_to_have': []
            },
            'market_positioning': {
                'competitive_level': 'Unknown',
                'salary_range': 'To be determined',
                'target_roles': ['General roles'],
                'company_fit': {'best_fit': 'mixed', 'fit_explanation': 'Analysis incomplete'}
            },
            'fallback': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_fallback_evaluation(self, user_context: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Get fallback evaluation when entire process fails."""
        return {
            'evaluation_id': user_context.get('evaluation_id'),
            'user_id': user_context.get('user_id'),
            'overall_score': 0,
            'executive_summary': f'Resume evaluation failed: {error_message}',
            'agent_results': {},
            'summary': self._get_summary_fallback_result({}),
            'metrics': {
                'weighted_score': 0,
                'confidence_percentage': 0,
                'successful_agents': 0,
                'total_agents': 0,
                'error': error_message
            },
            'evaluation_timestamp': datetime.now(timezone.utc).isoformat(),
            'processing_time_seconds': 0,
            'agent_performance': {},
            'error': error_message,
            'fallback': True
        }
    
    def _get_agent_performance_metrics(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance metrics for all agents."""
        performance = {}
        for agent_name, result in analysis_results.items():
            performance[agent_name] = {
                'success': not result.get('error', False) and not result.get('fallback', False),
                'has_timeout': result.get('timeout', False),
                'has_error': result.get('error', False),
                'is_fallback': result.get('fallback', False),
                'score': self._extract_agent_score(result, agent_name)
            }
        return performance
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            agent_name: {
                'name': agent.agent_name,
                'capabilities': agent.get_capabilities(),
                'metadata': agent.get_agent_metadata()
            }
            for agent_name, agent in self.agents.items()
        }
