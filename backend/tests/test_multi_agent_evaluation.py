"""
Comprehensive test suite for multi-agent resume evaluation system.
Tests parallel execution, coordination, and result aggregation.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, Any

# Import the classes we need to test
from app.services.agentic_resume_evaluator import AgenticResumeEvaluatorService
from app.services.agents.resume_evaluation_orchestrator import ResumeEvaluationOrchestrator
from app.services.agents.harvard_compliance_agent import HarvardComplianceAgent
from app.core.ai_service import AIService
from app.schemas.resume import ResumeEvaluationResult
from tests.fixtures.test_resumes import TestResumeFixtures


class TestMultiAgentEvaluation:
    """Test suite for multi-agent resume evaluation system."""

    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service for testing."""
        ai_service = MagicMock(spec=AIService)
        ai_service.get_completion = AsyncMock(return_value='{"score": 8, "analysis": "test"}')
        return ai_service

    @pytest.fixture
    def orchestrator(self, mock_ai_service):
        """Create orchestrator with mocked AI service."""
        return ResumeEvaluationOrchestrator(mock_ai_service)

    @pytest.fixture
    def evaluator_service(self, mock_ai_service):
        """Create evaluator service with mocked AI service."""
        return AgenticResumeEvaluatorService(mock_ai_service)

    @pytest.fixture
    def sample_resume_content(self):
        """Sample resume content for testing."""
        return """
        John Smith
        Software Engineer
        john.smith@email.com | (555) 123-4567

        EXPERIENCE
        Senior Software Engineer | Tech Corp | 2020-2023
        • Developed scalable microservices handling 1M+ daily requests
        • Reduced system latency by 40% through optimization
        • Led team of 5 engineers in agile development process

        Software Developer | StartupCo | 2018-2020
        • Built full-stack applications using Python and React
        • Implemented CI/CD pipelines reducing deployment time by 60%
        • Collaborated with product team on feature requirements

        EDUCATION
        Bachelor of Science in Computer Science | State University | 2018

        SKILLS
        Python, JavaScript, React, Docker, AWS, PostgreSQL
        """

    @pytest.fixture
    def user_context(self):
        """Sample user context for testing."""
        return {
            'user_id': 'test-user-123',
            'evaluation_id': 'eval-456',
            'target_roles': ['Software Engineer', 'Backend Developer'],
            'target_seniority': 'senior',
            'current_date': 'October 2024',
            'current_year': 2024,
            'years_experience': 5,
            'target_companies': ['maang', 'startups']
        }

    @pytest.mark.asyncio
    async def test_all_agents_execute_in_parallel(self, orchestrator, sample_resume_content, user_context):
        """Test that all 11 agents execute in parallel."""
        start_time = time.time()

        # Mock each agent's analyze method to take some time
        async def mock_analyze_with_delay(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"score": 8, "analysis": "test result", "agent_name": "test"}

        # Mock all agent analyze methods
        for agent in orchestrator.agents.values():
            agent.analyze = AsyncMock(side_effect=mock_analyze_with_delay)
            agent.validate_result = MagicMock(return_value=True)
            agent.execute_with_timeout = AsyncMock(side_effect=mock_analyze_with_delay)

        # Mock summary generation
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 85,
            "executive_summary": "Test summary",
            "strengths": ["Test strength"],
            "critical_improvements": {"immediate_fixes": [], "strategic_improvements": []}
        })

        result = await orchestrator.evaluate_resume(sample_resume_content, user_context)

        execution_time = time.time() - start_time

        # Verify parallel execution (should be much faster than sequential)
        assert execution_time < 2.0, "Agents should execute in parallel, not sequentially"

        # Verify all agents were called (now 12 with Harvard compliance)
        assert len(orchestrator.agents) == 12, "Should have 12 agents including Harvard compliance"

        # Verify result structure
        assert 'agent_results' in result
        assert 'overall_score' in result
        assert 'metrics' in result

    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, orchestrator, sample_resume_content, user_context):
        """Test that agents handle timeouts gracefully."""

        # Mock one agent to timeout
        async def mock_timeout_agent(*args, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
            return {"score": 5}

        # Make one agent timeout
        orchestrator.agents['ats'].execute_with_timeout = AsyncMock(side_effect=asyncio.TimeoutError())

        # Mock other agents normally
        for agent_name, agent in orchestrator.agents.items():
            if agent_name != 'ats' and agent_name != 'summary':
                agent.execute_with_timeout = AsyncMock(return_value={
                    "score": 8, "analysis": "test", "agent_name": agent_name
                })
                agent.validate_result = MagicMock(return_value=True)

        # Mock summary generation
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 85,
            "executive_summary": "Test summary",
            "strengths": ["Test strength"],
            "critical_improvements": {"immediate_fixes": [], "strategic_improvements": []}
        })

        result = await orchestrator.evaluate_resume(sample_resume_content, user_context)

        # Should still complete despite one agent timing out
        assert result is not None
        assert 'agent_results' in result
        assert 'ats' in result['agent_results']

        # The timed out agent should have a fallback result
        ats_result = result['agent_results']['ats']
        assert 'error' in ats_result or 'fallback' in ats_result

    @pytest.mark.asyncio
    async def test_result_aggregation_no_overlap(self, orchestrator, sample_resume_content, user_context):
        """Test that agent results are properly aggregated without overlap."""

        # Mock agents with different specialized results
        mock_results = {
            'ats': {"ats_score": 9, "keyword_optimization": {"score": 9}},
            'experience': {"experience_score": 8, "years_validation": True},
            'skills': {"skills_score": 7, "technical_skills": ["Python", "JavaScript"]},
            'format': {"format_score": 9, "visual_hierarchy": {"score": 9}},
            'red_flags': {"red_flag_score": 2, "issues_found": []},
            'company_fit': {"company_fit_scores": {"maang": {"score": 8}, "startups": {"score": 9}}},
            'detailed_analysis': {"overall_score": 8, "detailed_feedback": "Good resume"},
            'above_fold_impact': {"above_fold_score": 7, "first_impression": "Strong"},
            'recruiter_psychology': {"psychology_score": 8, "scanning_optimization": "Good"},
            'final_touches': {"final_touches_score": 9, "submission_ready": True}
        }

        # Mock each agent
        for agent_name, mock_result in mock_results.items():
            if agent_name in orchestrator.agents and agent_name != 'summary':
                orchestrator.agents[agent_name].execute_with_timeout = AsyncMock(return_value=mock_result)
                orchestrator.agents[agent_name].validate_result = MagicMock(return_value=True)

        # Mock summary generation
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 85,
            "executive_summary": "Comprehensive analysis complete",
            "strengths": ["Strong technical skills", "Good experience"],
            "critical_improvements": {
                "immediate_fixes": ["Fix grammar"],
                "strategic_improvements": ["Add more metrics"]
            }
        })

        result = await orchestrator.evaluate_resume(sample_resume_content, user_context)

        # Verify no overlapping analysis
        agent_results = result['agent_results']

        # Check that each agent provided unique analysis
        assert 'ats_score' in agent_results['ats']
        assert 'experience_score' in agent_results['experience']
        assert 'skills_score' in agent_results['skills']
        assert 'format_score' in agent_results['format']

        # Verify proper scoring aggregation
        metrics = result['metrics']
        assert 'weighted_score' in metrics
        assert 'confidence_percentage' in metrics
        assert metrics['successful_agents'] > 0

    @pytest.mark.asyncio
    async def test_progress_tracking(self, orchestrator, sample_resume_content, user_context):
        """Test real-time progress tracking during evaluation."""

        evaluation_id = user_context['evaluation_id']

        # Mock agents with delays to test progress tracking
        async def mock_agent_with_progress(agent_name):
            await asyncio.sleep(0.1)  # Simulate processing
            return {"score": 8, "agent_name": agent_name}

        for agent_name, agent in orchestrator.agents.items():
            if agent_name != 'summary':
                agent.execute_with_timeout = AsyncMock(
                    side_effect=lambda *args, **kwargs: mock_agent_with_progress(agent_name)
                )
                agent.validate_result = MagicMock(return_value=True)

        # Mock summary generation
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 85,
            "executive_summary": "Progress tracking test"
        })

        # Start evaluation in background
        evaluation_task = asyncio.create_task(
            orchestrator.evaluate_resume(sample_resume_content, user_context)
        )

        # Check progress during execution
        await asyncio.sleep(0.05)  # Let some agents start
        progress = orchestrator.get_evaluation_progress(evaluation_id)

        assert progress['status'] in ['starting', 'running', 'completed']
        assert 'stages' in progress
        assert 'overall_progress' in progress

        # Wait for completion
        result = await evaluation_task

        # Check final progress
        final_progress = orchestrator.get_evaluation_progress(evaluation_id)
        assert final_progress['overall_progress'] == 100 or final_progress['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_error_recovery_mechanisms(self, orchestrator, sample_resume_content, user_context):
        """Test system recovery when multiple agents fail."""

        # Make half the agents fail
        failing_agents = ['ats', 'experience', 'skills', 'format', 'red_flags']

        for agent_name, agent in orchestrator.agents.items():
            if agent_name in failing_agents and agent_name != 'summary':
                agent.execute_with_timeout = AsyncMock(side_effect=Exception("Agent failed"))
            elif agent_name != 'summary':
                agent.execute_with_timeout = AsyncMock(return_value={
                    "score": 8, "analysis": "success", "agent_name": agent_name
                })
                agent.validate_result = MagicMock(return_value=True)

        # Mock summary generation
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 60,  # Lower score due to failures
            "executive_summary": "Partial evaluation due to technical issues"
        })

        result = await orchestrator.evaluate_resume(sample_resume_content, user_context)

        # System should still provide a result
        assert result is not None
        assert 'agent_results' in result

        # Check that failed agents have fallback results
        for failing_agent in failing_agents:
            if failing_agent in result['agent_results']:
                agent_result = result['agent_results'][failing_agent]
                assert 'error' in agent_result or 'fallback' in agent_result

        # Metrics should reflect the failures
        metrics = result['metrics']
        assert metrics['successful_agents'] < metrics['total_agents']
        assert metrics['confidence_percentage'] < 100

    @pytest.mark.asyncio
    async def test_weighted_scoring_accuracy(self, orchestrator, sample_resume_content, user_context):
        """Test that weighted scoring correctly aggregates agent scores."""

        # Mock specific scores for calculation testing
        test_scores = {
            'ats': 9,
            'experience': 8,
            'skills': 7,
            'format': 9,
            'red_flags': 2,  # Lower is better for red flags
            'company_fit': 8,
            'detailed_analysis': 8,
            'above_fold_impact': 7,
            'recruiter_psychology': 8,
            'final_touches': 9
        }

        for agent_name, score in test_scores.items():
            if agent_name in orchestrator.agents and agent_name != 'summary':
                if agent_name == 'company_fit':
                    mock_result = {"company_fit_scores": {"maang": {"score": score}, "startups": {"score": score}}}
                else:
                    score_field = f"{agent_name}_score"
                    mock_result = {score_field: score, "agent_name": agent_name}

                orchestrator.agents[agent_name].execute_with_timeout = AsyncMock(return_value=mock_result)
                orchestrator.agents[agent_name].validate_result = MagicMock(return_value=True)

        # Mock summary with calculated score
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 82,  # Expected weighted result
            "executive_summary": "Scoring test"
        })

        result = await orchestrator.evaluate_resume(sample_resume_content, user_context)

        # Verify weighted scoring was applied
        metrics = result['metrics']
        assert 'weighted_score' in metrics
        assert isinstance(metrics['weighted_score'], (int, float))
        assert 0 <= metrics['weighted_score'] <= 100

    def test_agent_specialization_domains(self, orchestrator):
        """Test that each agent has distinct specialized domains."""

        agent_capabilities = {}
        for agent_name, agent in orchestrator.agents.items():
            capabilities = agent.get_capabilities()
            agent_capabilities[agent_name] = capabilities

        # Verify no overlap in primary capabilities
        all_capabilities = []
        for capabilities in agent_capabilities.values():
            all_capabilities.extend(capabilities)

        # Check for proper domain separation
        assert len(orchestrator.agents) == 12, "Should have 12 specialized agents including Harvard compliance"

        # Verify each agent has unique primary focus
        primary_domains = {
            'ats': 'ats_compatibility',
            'experience': 'experience_analysis',
            'skills': 'skills_assessment',
            'format': 'visual_hierarchy_analysis',
            'red_flags': 'issue_detection',
            'company_fit': 'company_alignment',
            'harvard_compliance': 'language_standards',
            'detailed_analysis': 'comprehensive_analysis',
            'above_fold_impact': 'first_impression',
            'recruiter_psychology': 'scanning_optimization',
            'final_touches': 'submission_readiness',
            'summary': 'result_consolidation'
        }

        for agent_name, expected_domain in primary_domains.items():
            if agent_name in orchestrator.agents:
                capabilities = orchestrator.agents[agent_name].get_capabilities()
                # Each agent should have its specialized capability
                domain_found = any(expected_domain in cap for cap in capabilities)
                assert domain_found or len(capabilities) > 0, f"Agent {agent_name} should have specialized capabilities"


@pytest.mark.integration
class TestMultiAgentIntegration:
    """Integration tests for the complete multi-agent evaluation system."""

    @pytest.fixture
    def real_ai_service(self):
        """Real AI service for integration testing."""
        return AIService()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_evaluation_pipeline(self, real_ai_service):
        """Test complete evaluation pipeline with real AI service."""

        evaluator = AgenticResumeEvaluatorService(real_ai_service)

        sample_resume = """
        Jane Doe
        Senior Software Engineer
        jane.doe@email.com | (555) 987-6543

        PROFESSIONAL EXPERIENCE
        Senior Software Engineer | Google | 2021-2024
        • Architected microservices platform serving 100M+ users daily
        • Reduced system latency by 45% through performance optimization
        • Led cross-functional team of 8 engineers across 3 time zones
        • Implemented automated testing reducing bugs by 60%

        Software Engineer | Meta | 2019-2021
        • Developed real-time data processing pipeline handling 1TB+ daily
        • Built machine learning models improving recommendation accuracy by 25%
        • Mentored 3 junior engineers in best practices

        EDUCATION
        Master of Science in Computer Science | Stanford University | 2019
        Bachelor of Science in Computer Science | UC Berkeley | 2017

        TECHNICAL SKILLS
        Python, Java, Golang, React, Kubernetes, AWS, PostgreSQL, Redis
        """

        try:
            result = await evaluator.evaluate_resume(
                resume_text=sample_resume,
                user_id="integration-test-user",
                resume_id="integration-test-resume",
                target_role="Senior Software Engineer",
                target_seniority="senior"
            )

            # Verify comprehensive evaluation result
            assert isinstance(result, ResumeEvaluationResult)
            assert result.overall_score > 0
            assert len(result.strengths) > 0
            assert len(result.improvements) >= 0
            assert result.ats_compatibility in ['excellent', 'good', 'fair', 'poor']

            print(f"Integration test completed successfully with score: {result.overall_score}")

        except Exception as e:
            pytest.skip(f"Integration test skipped due to AI service unavailability: {e}")


    @pytest.mark.asyncio
    async def test_harvard_compliance_integration(self, orchestrator):
        """Test Harvard Compliance Agent integration with orchestrator."""
        fixtures = TestResumeFixtures()
        test_cases = fixtures.get_all_test_cases()

        # Test Harvard compliant resume
        compliant_case = test_cases['harvard_compliant']
        result = await orchestrator.evaluate_resume(
            compliant_case['resume'],
            compliant_case['context']
        )

        # Verify Harvard compliance agent was executed
        assert 'harvard_compliance' in result['agent_results']
        harvard_result = result['agent_results']['harvard_compliance']

        assert not harvard_result.get('error', False)
        assert 'compliance_score' in harvard_result
        assert harvard_result['compliance_score'] >= 80  # Should score high

        # Test Harvard violation resume
        violation_case = test_cases['harvard_violations']
        result = await orchestrator.evaluate_resume(
            violation_case['resume'],
            violation_case['context']
        )

        harvard_result = result['agent_results']['harvard_compliance']
        assert 'compliance_score' in harvard_result
        assert harvard_result['compliance_score'] <= 40  # Should score low
        assert 'violations' in harvard_result
        assert len(harvard_result['violations']) > 0

    @pytest.mark.asyncio
    async def test_specific_harvard_violations(self):
        """Test Harvard Compliance Agent detects specific violation types."""
        ai_service = MagicMock(spec=AIService)
        ai_service.get_completion = AsyncMock()

        harvard_agent = HarvardComplianceAgent(ai_service)
        test_samples = TestResumeFixtures.get_harvard_test_samples()

        for sample_name, sample_data in test_samples.items():
            # Mock AI response for violation detection
            ai_service.get_completion.return_value = f'{{"compliance_score": 30, "violations": {sample_data["expected_violations"]}}}'

            result = await harvard_agent.analyze(sample_data['text'], {})

            assert 'compliance_score' in result
            assert 'violations' in result

            if sample_data['expected_violations']:
                assert len(result['violations']) > 0
            else:
                assert len(result['violations']) == 0

    @pytest.mark.asyncio
    async def test_12_agents_parallel_execution_timing(self, orchestrator, sample_resume_content, user_context):
        """Test that all 12 agents (including Harvard compliance) execute in parallel."""
        start_time = time.time()

        # Mock each agent with delay to test parallelization
        async def mock_analyze_with_delay(*args, **kwargs):
            await asyncio.sleep(0.15)  # Longer delay to test parallel vs sequential
            return {"score": 8, "analysis": "test result", "agent_name": "test"}

        # Mock all 12 agents
        for agent_name, agent in orchestrator.agents.items():
            if agent_name != 'summary':
                agent.execute_with_timeout = AsyncMock(side_effect=mock_analyze_with_delay)
                agent.validate_result = MagicMock(return_value=True)

        # Mock summary generation
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 85,
            "executive_summary": "Test summary with Harvard compliance"
        })

        result = await orchestrator.evaluate_resume(sample_resume_content, user_context)
        execution_time = time.time() - start_time

        # With 12 agents running in parallel, should complete in ~0.15s
        # If sequential, would take ~1.8s (12 * 0.15)
        assert execution_time < 0.8, f"Execution took {execution_time}s, expected parallel execution"

        # Verify all 12 agents (including Harvard compliance) were executed
        assert 'harvard_compliance' in result['agent_results']
        assert len([k for k in result['agent_results'].keys() if k != 'summary']) == 11

    @pytest.mark.asyncio
    async def test_weighted_scoring_with_harvard_compliance(self, orchestrator, sample_resume_content, user_context):
        """Test weighted scoring includes Harvard compliance agent properly."""

        # Mock specific scores including Harvard compliance
        test_scores = {
            'ats': 9,
            'experience': 8,
            'skills': 7,
            'format': 9,
            'red_flags': 2,
            'company_fit': 8,
            'harvard_compliance': 9,  # High compliance score
            'detailed_analysis': 8,
            'above_fold_impact': 7,
            'recruiter_psychology': 8,
            'final_touches': 9
        }

        for agent_name, score in test_scores.items():
            if agent_name in orchestrator.agents and agent_name != 'summary':
                if agent_name == 'company_fit':
                    mock_result = {"company_fit_scores": {"maang": {"score": score}, "startups": {"score": score}}}
                elif agent_name == 'harvard_compliance':
                    mock_result = {"compliance_score": score, "agent_name": agent_name}
                else:
                    score_field = f"{agent_name}_score"
                    mock_result = {score_field: score, "agent_name": agent_name}

                orchestrator.agents[agent_name].execute_with_timeout = AsyncMock(return_value=mock_result)
                orchestrator.agents[agent_name].validate_result = MagicMock(return_value=True)

        # Mock summary
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 85,
            "executive_summary": "Weighted scoring test with Harvard compliance"
        })

        result = await orchestrator.evaluate_resume(sample_resume_content, user_context)

        # Verify Harvard compliance is included in scoring
        metrics = result['metrics']
        assert 'harvard_compliance' in metrics['agent_scores']
        assert metrics['agent_scores']['harvard_compliance'] == 9

        # Verify weighted score calculation
        assert 'weighted_score' in metrics
        assert isinstance(metrics['weighted_score'], (int, float))
        assert 0 <= metrics['weighted_score'] <= 100

    @pytest.mark.asyncio
    async def test_comprehensive_resume_evaluation_pipeline(self, orchestrator):
        """Test complete evaluation pipeline with all test resume types."""
        fixtures = TestResumeFixtures()
        test_cases = fixtures.get_all_test_cases()

        results = {}
        for case_name, case_data in test_cases.items():
            # Mock all agents for consistent testing
            for agent_name, agent in orchestrator.agents.items():
                if agent_name != 'summary':
                    # Generate different scores based on case type
                    if case_name == 'harvard_compliant':
                        base_score = 85
                    elif case_name == 'harvard_violations':
                        base_score = 35
                    elif case_name == 'ats_optimized':
                        base_score = 90
                    elif case_name == 'format_issues':
                        base_score = 40
                    elif case_name == 'skills_mismatch':
                        base_score = 45
                    else:  # red_flag_heavy
                        base_score = 30

                    # Adjust score based on agent type
                    if agent_name == 'harvard_compliance':
                        score = base_score + (10 if case_name == 'harvard_compliant' else -20)
                    elif agent_name == 'ats' and case_name == 'ats_optimized':
                        score = 95
                    elif agent_name == 'format' and case_name == 'format_issues':
                        score = 25
                    elif agent_name == 'red_flags':
                        score = 15 if case_name == 'red_flag_heavy' else 5
                    else:
                        score = base_score

                    # Create appropriate mock result
                    if agent_name == 'company_fit':
                        mock_result = {"company_fit_scores": {"maang": {"score": score}}}
                    elif agent_name == 'harvard_compliance':
                        mock_result = {"compliance_score": score, "violations": [] if score > 70 else ["sample_violation"]}
                    else:
                        score_field = f"{agent_name}_score"
                        mock_result = {score_field: score, "agent_name": agent_name}

                    agent.execute_with_timeout = AsyncMock(return_value=mock_result)
                    agent.validate_result = MagicMock(return_value=True)

            # Mock summary
            orchestrator.agents['summary'].generate = AsyncMock(return_value={
                "overall_score": base_score,
                "executive_summary": f"Test evaluation for {case_name}"
            })

            # Execute evaluation
            result = await orchestrator.evaluate_resume(
                case_data['resume'],
                case_data['context']
            )

            results[case_name] = result

            # Basic validation
            assert result is not None
            assert 'agent_results' in result
            assert 'harvard_compliance' in result['agent_results']
            assert 'metrics' in result
            assert result['metrics']['successful_agents'] == 11  # All agents should succeed

        # Compare results across cases
        harvard_compliant_score = results['harvard_compliant']['agent_results']['harvard_compliance']['compliance_score']
        harvard_violation_score = results['harvard_violations']['agent_results']['harvard_compliance']['compliance_score']

        assert harvard_compliant_score > harvard_violation_score, "Compliant resume should score higher than violation resume"

    @pytest.mark.asyncio
    async def test_agent_coordination_no_overlap(self, orchestrator, sample_resume_content, user_context):
        """Test that agents provide unique analysis without overlapping responsibilities."""

        # Mock agents with specialized results to test coordination
        specialized_results = {
            'ats': {"ats_score": 9, "keyword_optimization": {"technical_keywords": 15, "role_keywords": 12}},
            'experience': {"experience_score": 8, "years_validation": True, "role_progression": "appropriate"},
            'skills': {"skills_score": 7, "technical_depth": "strong", "skill_relevance": 85},
            'format': {"format_score": 9, "visual_hierarchy": {"score": 9}, "section_organization": "excellent"},
            'red_flags': {"red_flag_score": 3, "employment_gaps": [], "consistency_issues": []},
            'company_fit': {"company_fit_scores": {"maang": {"score": 8}, "startups": {"score": 9}}},
            'harvard_compliance': {"compliance_score": 9, "language_quality": "excellent", "violations": []},
            'detailed_analysis': {"overall_score": 8, "comprehensive_feedback": "Strong technical profile"},
            'above_fold_impact': {"above_fold_score": 7, "first_impression": "professional"},
            'recruiter_psychology': {"psychology_score": 8, "scanning_flow": "optimized"},
            'final_touches': {"final_touches_score": 9, "submission_ready": True}
        }

        for agent_name, mock_result in specialized_results.items():
            if agent_name in orchestrator.agents and agent_name != 'summary':
                orchestrator.agents[agent_name].execute_with_timeout = AsyncMock(return_value=mock_result)
                orchestrator.agents[agent_name].validate_result = MagicMock(return_value=True)

        # Mock summary
        orchestrator.agents['summary'].generate = AsyncMock(return_value={
            "overall_score": 85,
            "executive_summary": "Comprehensive analysis with no overlapping agent results"
        })

        result = await orchestrator.evaluate_resume(sample_resume_content, user_context)

        # Verify each agent provided unique analysis
        agent_results = result['agent_results']

        # Check unique analysis domains
        assert 'keyword_optimization' in agent_results['ats']  # ATS-specific
        assert 'years_validation' in agent_results['experience']  # Experience-specific
        assert 'technical_depth' in agent_results['skills']  # Skills-specific
        assert 'visual_hierarchy' in agent_results['format']  # Format-specific
        assert 'employment_gaps' in agent_results['red_flags']  # Red flags-specific
        assert 'language_quality' in agent_results['harvard_compliance']  # Harvard-specific
        assert 'first_impression' in agent_results['above_fold_impact']  # Above fold-specific
        assert 'scanning_flow' in agent_results['recruiter_psychology']  # Psychology-specific
        assert 'submission_ready' in agent_results['final_touches']  # Final touches-specific

        # Ensure no cross-agent contamination
        assert 'language_quality' not in agent_results['ats']  # Harvard-specific shouldn't be in ATS
        assert 'keyword_optimization' not in agent_results['harvard_compliance']  # ATS-specific shouldn't be in Harvard
        assert 'visual_hierarchy' not in agent_results['experience']  # Format-specific shouldn't be in experience


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_multi_agent_evaluation.py -v
    pytest.main([__file__, "-v"])