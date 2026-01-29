"""
Singleton manager for sharing orchestrator instances across the application.
This ensures progress tracking works across different API endpoints.
"""

from typing import Optional, Dict, Any
from app.core.ai_service import AIService


class ResumeEvaluationOrchestrator:
    """
    Mock orchestrator to replace the legacy multi-agent orchestrator.
    This ensures that calls to get_evaluation_progress don't crash the application
    now that we've moved to the ConsolidatedResumeEvaluator.
    """
    
    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service

    def get_evaluation_progress(self, resume_id: str) -> Dict[str, Any]:
        """
        Return mock progress since granular agent tracking is deprecated.
        The UI handles 'evaluating' vs 'completed' based on DB status.
        """
        return {
            "current_step": "consolidated_evaluation",
            "total_steps": 1,
            "completed_steps": 0,
            "percentage": 50,
            "status": "in_progress",
            "message": "AI is analyzing your resume..."
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Return active status for the consolidated agent."""
        return {
            "consolidated_evaluator": {
                "status": "active",
                "model": "gpt-4o-mini",
                "capabilities": ["comprehensive_analysis"]
            }
        }


class OrchestratorManager:
    """Singleton manager for orchestrator instances."""

    _instance: Optional['OrchestratorManager'] = None
    _orchestrator: Optional[ResumeEvaluationOrchestrator] = None

    def __new__(cls) -> 'OrchestratorManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_orchestrator(self, ai_service: Optional[AIService] = None) -> ResumeEvaluationOrchestrator:
        """Get or create the shared orchestrator instance."""
        if self._orchestrator is None:
            self._orchestrator = ResumeEvaluationOrchestrator(ai_service)
        return self._orchestrator

    def clear_orchestrator(self) -> None:
        """Clear the orchestrator instance (for testing)."""
        self._orchestrator = None


# Global instance
orchestrator_manager = OrchestratorManager()