"""
Singleton manager for sharing orchestrator instances across the application.
This ensures progress tracking works across different API endpoints.
"""

from typing import Optional
from app.core.ai_service import AIService
from app.services.agents.resume_evaluation_orchestrator import ResumeEvaluationOrchestrator


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
            if ai_service is None:
                ai_service = AIService()
            self._orchestrator = ResumeEvaluationOrchestrator(ai_service)
        return self._orchestrator

    def clear_orchestrator(self) -> None:
        """Clear the orchestrator instance (for testing)."""
        self._orchestrator = None


# Global instance
orchestrator_manager = OrchestratorManager()