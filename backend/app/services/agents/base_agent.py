"""
Base agent class for resume evaluation agents.
Provides common functionality for all specialized agents.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.ai_service import AIService
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all resume evaluation agents."""
    
    def __init__(self, agent_name: str, ai_service: Optional[AIService] = None):
        self.agent_name = agent_name
        self.ai_service = ai_service or AIService()
        self.logger = logging.getLogger(f"agent.{agent_name}")
    
    @abstractmethod
    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume content and return structured results.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, user preferences, etc.)
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    async def llm_call(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Make LLM call with retry logic and error handling.
        
        Args:
            prompt: The prompt to send to the LLM
            max_retries: Maximum number of retry attempts
            
        Returns:
            Parsed JSON response from LLM
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Making LLM call (attempt {attempt + 1}/{max_retries})")
                
                response = await self.ai_service.get_completion(
                    prompt=prompt,
                    temperature=0.1,
                    max_tokens=2000
                )
                
                # Debug: Log the actual response
                self.logger.info(f"LLM response for {self.agent_name}: {response[:200]}...")
                
                # Check if response is empty
                if not response or not response.strip():
                    self.logger.warning(f"Empty response from LLM for {self.agent_name}")
                    if attempt == max_retries - 1:
                        return self._get_fallback_response()
                    await asyncio.sleep(1)
                    continue
                
                # Parse JSON response
                result = json.loads(response)
                self.logger.info(f"LLM call successful for {self.agent_name}")
                return result
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                self.logger.warning(f"Response content: {response[:500]}...")
                if attempt == max_retries - 1:
                    return self._get_fallback_response()
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"LLM call failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return self._get_fallback_response()
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return self._get_fallback_response()
    
    def _get_fallback_response(self) -> Dict[str, Any]:
        """Return a fallback response when LLM calls fail."""
        self.logger.error(f"All LLM calls failed for {self.agent_name}, using fallback response")
        return {
            "error": f"{self.agent_name} analysis failed",
            "fallback": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": self.agent_name,
            "score": 0,
            "analysis_type": "fallback"
        }
    
    def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate that the agent result has the expected structure.
        Override in subclasses for specific validation.
        """
        return isinstance(result, dict) and not result.get("error", False)
    
    async def execute_with_timeout(self, resume_content: str, context: Dict[str, Any], timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Execute agent analysis with timeout protection.
        
        Args:
            resume_content: The resume text to analyze
            context: Additional context for analysis
            timeout_seconds: Maximum execution time in seconds
            
        Returns:
            Agent analysis results or timeout error
        """
        start_time = datetime.now(timezone.utc)
        try:
            result = await asyncio.wait_for(
                self.analyze(resume_content, context),
                timeout=timeout_seconds
            )
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000  # Convert to milliseconds
            result['execution_time_ms'] = int(execution_time)
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"Agent {self.agent_name} timed out after {timeout_seconds} seconds")
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return {
                "error": f"{self.agent_name} analysis timed out",
                "timeout": True,
                "execution_time_ms": int(execution_time),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Agent {self.agent_name} execution failed: {e}")
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            result = self._get_fallback_response()
            result['execution_time_ms'] = int(execution_time)
            return result
    
    def get_agent_metadata(self) -> Dict[str, Any]:
        """Get metadata about this agent."""
        return {
            "agent_name": self.agent_name,
            "version": "1.0.0",
            "capabilities": self.get_capabilities(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    def get_capabilities(self) -> list:
        """Return list of agent capabilities. Override in subclasses."""
        return ["resume_analysis"]
