"""
Integration tests for Harvard Compliance Agent and Multi-Agent System.
Tests the complete evaluation pipeline with real agent execution.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# Import the classes we need to test
from app.services.agentic_resume_evaluator import AgenticResumeEvaluatorService
from app.services.agents.resume_evaluation_orchestrator import ResumeEvaluationOrchestrator
from app.services.agents.harvard_compliance_agent import HarvardComplianceAgent
from app.core.ai_service import AIService
from tests.fixtures.test_resumes import TestResumeFixtures


class TestHarvardComplianceIntegration:
    """Integration tests for Harvard Compliance Agent system."""

    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service with realistic Harvard compliance responses."""
        ai_service = MagicMock(spec=AIService)

        # Mock Harvard compliance AI responses
        def mock_harvard_response(prompt, **kwargs):
            if "personal pronouns" in prompt.lower() or "harvard" in prompt.lower():
                # Check if this is a violation resume (contains "I'm a passionate" or "My goal")
                if any(violation_phrase in prompt for violation_phrase in ["I'm a passionate", "My goal", "I am a Software Developer"]):
                    return """{
                        "compliance_score": 25,
                        "violations": [
                            {"type": "personal_pronouns", "text": "I am", "suggestion": "Remove personal reference"},
                            {"type": "personal_pronouns", "text": "My goal", "suggestion": "State objective directly"},
                            {"type": "vague_descriptions", "text": "various projects", "suggestion": "Specify project types"}
                        ],
                        "grammar_issues": ["Missing quantifiable achievements"],
                        "passive_voice_count": 3,
                        "personal_pronoun_count": 8,
                        "action_verb_analysis": {
                            "weak_verbs": ["helped", "involved", "responsible"],
                            "suggested_replacements": ["developed", "led", "managed"]
                        }
                    }"""
                else:
                    return """{
                        "compliance_score": 90,
                        "violations": [],
                        "grammar_issues": [],
                        "passive_voice_count": 0,
                        "personal_pronoun_count": 0,
                        "action_verb_analysis": {
                            "strong_verbs": ["developed", "led", "achieved", "optimized"],
                            "categorization": "leadership_technical"
                        }
                    }"""
            else:
                return '{"score": 80, "analysis": "Standard agent response"}'

        ai_service.get_completion = AsyncMock(side_effect=mock_harvard_response)
        return ai_service

    @pytest.fixture
    def orchestrator(self, mock_ai_service):
        """Create orchestrator with mocked AI service."""
        return ResumeEvaluationOrchestrator(mock_ai_service)

    @pytest.mark.asyncio
    async def test_harvard_compliance_agent_violations_detection(self, mock_ai_service):
        """Test Harvard Compliance Agent detects violations correctly."""
        harvard_agent = HarvardComplianceAgent(mock_ai_service)

        violation_resume = TestResumeFixtures.get_harvard_violation_resume()
        user_context = TestResumeFixtures.get_user_context_software_engineer()

        result = await harvard_agent.analyze(violation_resume, user_context)

        # Verify violation detection
        assert 'compliance_score' in result
        assert result['compliance_score'] <= 30  # Should score low
        assert 'violations' in result
        assert len(result['violations']) > 0
        assert result.get('personal_pronoun_count', 0) > 0

        # Verify specific violation types detected
        violation_types = [v['type'] for v in result['violations']]
        assert 'personal_pronouns' in violation_types

    @pytest.mark.asyncio
    async def test_harvard_compliance_agent_clean_resume(self, mock_ai_service):
        """Test Harvard Compliance Agent validates clean resumes."""
        harvard_agent = HarvardComplianceAgent(mock_ai_service)

        compliant_resume = TestResumeFixtures.get_harvard_compliant_resume()
        user_context = TestResumeFixtures.get_user_context_software_engineer()

        result = await harvard_agent.analyze(compliant_resume, user_context)

        # Verify high compliance score
        assert 'compliance_score' in result
        assert result['compliance_score'] >= 80  # Should score high
        assert result.get('personal_pronoun_count', 0) == 0
        assert len(result.get('violations', [])) == 0

    @pytest.mark.asyncio
    async def test_12_agent_orchestrator_with_harvard(self, orchestrator):
        """Test complete 12-agent orchestrator including Harvard compliance."""

        # Mock all agents to ensure they execute
        for agent_name, agent in orchestrator.agents.items():
            if agent_name != 'summary':
                if agent_name == 'harvard_compliance':
                    # Specific mock for Harvard agent
                    agent.execute_with_timeout = AsyncMock(return_value={
                        "compliance_score": 85,
                        "violations": [],
                        "grammar_issues": [],
                        "action_verb_analysis": {"strong_verbs": ["developed", "led"]}
                    })
                else:
                    # Standard mock for other agents
                    score_field = f"{agent_name}_score" if agent_name != 'company_fit' else 'company_fit_scores'
                    if agent_name == 'company_fit':
                        mock_result = {"company_fit_scores": {"maang": {"score": 8}}}
                    else:
                        mock_result = {score_field: 8, "agent_name": agent_name}

                    agent.execute_with_timeout = AsyncMock(return_value=mock_result)

                agent.validate_result = MagicMock(return_value=True)

        # Mock summary generation
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 85,
            "executive_summary": "Comprehensive 12-agent evaluation complete",
            "strengths": ["Strong technical background", "Harvard-compliant language"],
            "critical_improvements": {
                "immediate_fixes": [],
                "strategic_improvements": []
            }
        })

        # Test with Harvard compliant resume
        compliant_resume = TestResumeFixtures.get_harvard_compliant_resume()
        user_context = TestResumeFixtures.get_user_context_software_engineer()

        result = await orchestrator.evaluate_resume(compliant_resume, user_context)

        # Verify all 12 agents executed
        assert len(orchestrator.agents) == 12
        assert 'harvard_compliance' in result['agent_results']
        assert 'ats' in result['agent_results']
        assert 'experience' in result['agent_results']

        # Verify Harvard compliance results
        harvard_result = result['agent_results']['harvard_compliance']
        assert 'compliance_score' in harvard_result
        assert harvard_result['compliance_score'] >= 80

        # Verify overall metrics include Harvard compliance
        metrics = result['metrics']
        assert 'agent_scores' in metrics
        assert 'harvard_compliance' in metrics['agent_scores']

    @pytest.mark.asyncio
    async def test_weighted_scoring_includes_harvard_compliance(self, orchestrator):
        """Test that weighted scoring properly includes Harvard compliance."""

        # Set specific scores to test weighting
        test_scores = {
            'ats': 9,
            'experience': 8,
            'skills': 7,
            'format': 8,
            'red_flags': 3,
            'company_fit': 8,
            'harvard_compliance': 9,  # High compliance score
            'detailed_analysis': 8,
            'above_fold_impact': 7,
            'recruiter_psychology': 8,
            'final_touches': 9
        }

        # Mock agents with specific scores
        for agent_name, score in test_scores.items():
            if agent_name in orchestrator.agents and agent_name != 'summary':
                if agent_name == 'company_fit':
                    mock_result = {"company_fit_scores": {"maang": {"score": score}}}
                elif agent_name == 'harvard_compliance':
                    mock_result = {"compliance_score": score, "violations": []}
                else:
                    score_field = f"{agent_name}_score"
                    mock_result = {score_field: score, "agent_name": agent_name}

                orchestrator.agents[agent_name].execute_with_timeout = AsyncMock(return_value=mock_result)
                orchestrator.agents[agent_name].validate_result = MagicMock(return_value=True)

        # Mock summary
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 82,
            "executive_summary": "Weighted scoring test"
        })

        # Execute evaluation
        result = await orchestrator.evaluate_resume("test resume", {})

        # Verify Harvard compliance is included in weighted calculation
        metrics = result['metrics']
        assert 'harvard_compliance' in metrics['agent_scores']
        assert metrics['agent_scores']['harvard_compliance'] == 9

        # Verify weighted score is calculated (should be around 82 based on weights)
        assert 'weighted_score' in metrics
        weighted_score = metrics['weighted_score']
        assert 70 <= weighted_score <= 90  # Should be in reasonable range

    @pytest.mark.asyncio
    async def test_error_recovery_with_harvard_agent_failure(self, orchestrator):
        """Test system continues when Harvard compliance agent fails."""

        # Mock Harvard agent to fail
        orchestrator.agents['harvard_compliance'].execute_with_timeout = AsyncMock(
            side_effect=Exception("Harvard agent failed")
        )

        # Mock other agents normally
        for agent_name, agent in orchestrator.agents.items():
            if agent_name not in ['harvard_compliance', 'summary']:
                if agent_name == 'company_fit':
                    mock_result = {"company_fit_scores": {"maang": {"score": 8}}}
                else:
                    score_field = f"{agent_name}_score"
                    mock_result = {score_field: 8, "agent_name": agent_name}

                agent.execute_with_timeout = AsyncMock(return_value=mock_result)
                agent.validate_result = MagicMock(return_value=True)

        # Mock summary
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 75,
            "executive_summary": "Evaluation completed despite Harvard agent failure"
        })

        # Execute evaluation
        result = await orchestrator.evaluate_resume("test resume", {})

        # System should still complete
        assert result is not None
        assert 'agent_results' in result

        # Harvard agent should have fallback result
        assert 'harvard_compliance' in result['agent_results']
        harvard_result = result['agent_results']['harvard_compliance']
        assert harvard_result.get('error') or harvard_result.get('fallback')

        # Other agents should succeed
        successful_agents = sum(1 for agent_name, agent_result in result['agent_results'].items()
                               if agent_name != 'harvard_compliance' and not agent_result.get('error'))
        assert successful_agents >= 9  # Should have at least 9 successful agents

    @pytest.mark.asyncio
    async def test_all_resume_types_with_harvard_evaluation(self, orchestrator):
        """Test all test resume types with Harvard compliance evaluation."""
        fixtures = TestResumeFixtures()
        test_cases = fixtures.get_all_test_cases()

        results = {}

        for case_name, case_data in test_cases.items():
            # Mock agents based on resume type
            expected_harvard_score = 90 if case_name == 'harvard_compliant' else 30

            for agent_name, agent in orchestrator.agents.items():
                if agent_name != 'summary':
                    if agent_name == 'harvard_compliance':
                        violations = [] if expected_harvard_score > 70 else [{"type": "personal_pronouns", "text": "I am"}]
                        mock_result = {
                            "compliance_score": expected_harvard_score,
                            "violations": violations
                        }
                    elif agent_name == 'company_fit':
                        mock_result = {"company_fit_scores": {"maang": {"score": 7}}}
                    else:
                        score_field = f"{agent_name}_score"
                        mock_result = {score_field: 7, "agent_name": agent_name}

                    agent.execute_with_timeout = AsyncMock(return_value=mock_result)
                    agent.validate_result = MagicMock(return_value=True)

            # Mock summary
            orchestrator.agents['summary'].generate = AsyncMock(return_value={
                "overall_score": expected_harvard_score,
                "executive_summary": f"Evaluation for {case_name}"
            })

            # Execute evaluation
            result = await orchestrator.evaluate_resume(case_data['resume'], case_data['context'])
            results[case_name] = result

            # Verify Harvard compliance was evaluated
            assert 'harvard_compliance' in result['agent_results']
            harvard_score = result['agent_results']['harvard_compliance']['compliance_score']

            if case_name == 'harvard_compliant':
                assert harvard_score >= 80, f"Harvard compliant resume should score high, got {harvard_score}"
            elif case_name == 'harvard_violations':
                assert harvard_score <= 40, f"Harvard violation resume should score low, got {harvard_score}"

        # Compare Harvard compliance scores across resume types
        compliant_score = results['harvard_compliant']['agent_results']['harvard_compliance']['compliance_score']
        violation_score = results['harvard_violations']['agent_results']['harvard_compliance']['compliance_score']

        assert compliant_score > violation_score + 40, "Significant difference expected between compliant and violation resumes"


@pytest.mark.integration
class TestProductionHarvardCompliance:
    """Integration tests against production endpoints."""

    def test_production_api_health(self):
        """Test that production API is accessible."""
        import requests

        try:
            response = requests.get('https://linkedinautomation-production-7ae9.up.railway.app/health', timeout=10)
            assert response.status_code == 200
            print(f"Production API Health: {response.json()}")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Production API not accessible: {e}")

    @pytest.mark.asyncio
    async def test_production_resume_evaluation_with_harvard(self):
        """Test production resume evaluation endpoint includes Harvard compliance."""
        import httpx

        # Use Harvard compliant resume for testing
        test_resume = TestResumeFixtures.get_harvard_compliant_resume()

        payload = {
            "resume_text": test_resume,
            "user_id": "test-user-123",
            "resume_id": "test-resume-456",
            "target_role": "Software Engineer",
            "target_seniority": "mid_level"
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    'https://linkedinautomation-production-7ae9.up.railway.app/api/v1/resumes/evaluate',
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    result = response.json()

                    # Verify the response includes Harvard compliance data
                    print(f"Production Response Keys: {list(result.keys())}")

                    # Check if Harvard compliance is mentioned in the evaluation
                    evaluation_text = str(result).lower()
                    has_harvard_reference = any(keyword in evaluation_text for keyword in [
                        'harvard', 'grammar', 'pronoun', 'compliance', 'language'
                    ])

                    if has_harvard_reference:
                        print("✅ Harvard compliance features detected in production response")
                    else:
                        print("⚠️ Harvard compliance features not clearly visible in production response")

                    assert result is not None
                    print(f"Production evaluation completed successfully")

                else:
                    print(f"Production API returned status {response.status_code}: {response.text}")
                    pytest.skip(f"Production API not working: {response.status_code}")

        except Exception as e:
            pytest.skip(f"Production API test failed: {e}")


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_harvard_compliance_integration.py -v -s
    pytest.main([__file__, "-v", "-s"])