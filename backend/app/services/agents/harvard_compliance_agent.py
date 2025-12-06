"""
Harvard Language Compliance Agent for resume evaluation.
Validates resumes against Harvard Career Services standards for language, grammar, and structure.
"""

import re
import json
from typing import Dict, Any, List, Tuple
from .base_agent import BaseAgent


class HarvardComplianceAgent(BaseAgent):
    """Agent specialized in Harvard Career Services language compliance validation."""

    def __init__(self, ai_service=None):
        super().__init__("HarvardComplianceAgent", ai_service)

        # Harvard-approved action verbs by category
        self.action_verbs = {
            'leadership': [
                'accomplished', 'achieved', 'administered', 'analyzed', 'assigned', 'attained',
                'chaired', 'consolidated', 'contracted', 'coordinated', 'delegated', 'developed',
                'directed', 'earned', 'evaluated', 'executed', 'handled', 'headed', 'impacted',
                'improved', 'increased', 'led', 'mastered', 'orchestrated', 'organized', 'oversaw',
                'planned', 'predicted', 'prioritized', 'produced', 'proved', 'recommended',
                'regulated', 'reorganized', 'reviewed', 'scheduled', 'spearheaded', 'strengthened',
                'supervised', 'surpassed'
            ],
            'communication': [
                'addressed', 'arbitrated', 'arranged', 'authored', 'collaborated', 'convinced',
                'corresponded', 'delivered', 'developed', 'directed', 'documented', 'drafted',
                'edited', 'energized', 'enlisted', 'formulated', 'influenced', 'interpreted',
                'lectured', 'liaised', 'mediated', 'moderated', 'negotiated', 'persuaded',
                'presented', 'promoted', 'publicized', 'reconciled', 'recruited', 'reported',
                'rewrote', 'spoke', 'suggested', 'synthesized', 'translated', 'verbalized', 'wrote'
            ],
            'research': [
                'clarified', 'collected', 'concluded', 'conducted', 'constructed', 'critiqued',
                'derived', 'determined', 'diagnosed', 'discovered', 'evaluated', 'examined',
                'extracted', 'formed', 'identified', 'inspected', 'interpreted', 'interviewed',
                'investigated', 'modeled', 'organized', 'resolved', 'reviewed', 'summarized',
                'surveyed', 'systematized', 'tested'
            ],
            'technical': [
                'assembled', 'built', 'calculated', 'computed', 'designed', 'devised',
                'engineered', 'fabricated', 'installed', 'maintained', 'operated', 'optimized',
                'overhauled', 'programmed', 'remodeled', 'repaired', 'solved', 'standardized',
                'streamlined', 'upgraded'
            ],
            'quantitative': [
                'administered', 'allocated', 'analyzed', 'appraised', 'audited', 'balanced',
                'budgeted', 'calculated', 'computed', 'developed', 'forecasted', 'managed',
                'marketed', 'maximized', 'minimized', 'planned', 'projected', 'researched'
            ]
        }

        # All action verbs combined for validation
        self.all_action_verbs = set()
        for category_verbs in self.action_verbs.values():
            self.all_action_verbs.update(category_verbs)

        # Personal pronouns to detect and flag
        self.personal_pronouns = {
            'first_person': ['i', 'me', 'my', 'mine', 'myself'],
            'second_person': ['you', 'your', 'yours', 'yourself'],
            'third_person': ['he', 'she', 'it', 'his', 'her', 'its', 'him', 'himself', 'herself', 'itself']
        }

        # Common abbreviations that should be spelled out
        self.abbreviations_to_expand = {
            'mgmt': 'management',
            'dev': 'development',
            'eng': 'engineering',
            'tech': 'technology',
            'admin': 'administration',
            'ops': 'operations',
            'hr': 'human resources',
            'qa': 'quality assurance',
            'ui': 'user interface',
            'ux': 'user experience',
            'api': 'application programming interface',
            'sql': 'structured query language',
            'crm': 'customer relationship management',
            'roi': 'return on investment',
            'kpi': 'key performance indicator'
        }

    async def analyze(self, resume_content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze resume for Harvard Career Services language compliance.

        Args:
            resume_content: The resume text to analyze
            context: Additional context (target roles, preferences, etc.)

        Returns:
            Dictionary containing Harvard compliance analysis results
        """
        context = context or {}
        target_roles = context.get('target_roles', [])

        # Perform all compliance checks
        pronoun_violations = self._detect_personal_pronouns(resume_content)
        passive_voice_issues = await self._detect_passive_voice(resume_content)
        action_verb_analysis = self._analyze_action_verbs(resume_content)
        abbreviation_issues = self._detect_abbreviations(resume_content)
        narrative_style_issues = self._detect_narrative_style(resume_content)
        quantification_analysis = self._analyze_quantification(resume_content)
        grammar_spelling_issues = await self._check_grammar_spelling(resume_content)

        # Calculate compliance scores
        compliance_scores = self._calculate_compliance_scores(
            pronoun_violations, passive_voice_issues, action_verb_analysis,
            abbreviation_issues, narrative_style_issues, quantification_analysis,
            grammar_spelling_issues
        )

        prompt = f"""
        You are a Harvard Career Services compliance expert. Based on the detailed analysis performed,
        provide a comprehensive evaluation of this resume's adherence to Harvard standards.

        Resume Content:
        {resume_content[:2000]}...

        Analysis Results:
        - Personal Pronoun Violations: {len(pronoun_violations)} found
        - Passive Voice Issues: {len(passive_voice_issues)} found
        - Action Verb Coverage: {action_verb_analysis['coverage_percentage']:.1f}%
        - Abbreviation Issues: {len(abbreviation_issues)} found
        - Narrative Style Issues: {len(narrative_style_issues)} found
        - Quantified Achievements: {quantification_analysis['quantified_bullets']}/{quantification_analysis['total_bullets']}
        - Grammar/Spelling Issues: {len(grammar_spelling_issues)} found

        Target Roles: {', '.join(target_roles) if target_roles else 'General professional roles'}

        Provide your evaluation in this exact JSON format:
        {{
            "harvard_compliance_score": 0-10,
            "overall_compliance": "excellent|good|fair|poor",

            "language_compliance": {{
                "score": 0-10,
                "pronoun_violations": {len(pronoun_violations)},
                "passive_voice_count": {len(passive_voice_issues)},
                "narrative_style_issues": {len(narrative_style_issues)},
                "compliance_level": "excellent|good|fair|poor"
            }},

            "action_verb_compliance": {{
                "score": 0-10,
                "coverage_percentage": {action_verb_analysis['coverage_percentage']:.1f},
                "strong_verbs_used": {len(action_verb_analysis['strong_verbs_found'])},
                "weak_verbs_found": {len(action_verb_analysis['weak_verbs_found'])},
                "missing_categories": {action_verb_analysis['missing_categories']},
                "compliance_level": "excellent|good|fair|poor"
            }},

            "grammar_spelling_compliance": {{
                "score": 0-10,
                "errors_found": {len(grammar_spelling_issues)},
                "abbreviations_count": {len(abbreviation_issues)},
                "compliance_level": "excellent|good|fair|poor"
            }},

            "quantification_compliance": {{
                "score": 0-10,
                "quantified_achievements": {quantification_analysis['quantified_bullets']},
                "total_achievements": {quantification_analysis['total_bullets']},
                "quantification_rate": {quantification_analysis['quantification_rate']:.1f},
                "compliance_level": "excellent|good|fair|poor"
            }},

            "critical_violations": [
                {{
                    "violation_type": "personal_pronouns|passive_voice|abbreviations|narrative_style|grammar|missing_quantification",
                    "severity": "critical|high|medium|low",
                    "description": "Specific violation description",
                    "examples": ["example1", "example2"],
                    "fix_instruction": "How to fix this violation"
                }}
            ],

            "harvard_improvements": [
                {{
                    "category": "Language|Action Verbs|Grammar|Quantification|Structure",
                    "priority": "critical|high|medium|low",
                    "improvement": "Specific improvement needed",
                    "harvard_standard": "The specific Harvard standard being violated",
                    "example_fix": "Before: → After: example"
                }}
            ],

            "compliance_summary": {{
                "total_violations": 0,
                "critical_violations": 0,
                "compliance_percentage": 0.0,
                "harvard_readiness": "ready|needs_minor_fixes|needs_major_fixes|not_compliant",
                "submission_recommendation": "Recommendation text"
            }}
        }}

        Focus on specific, actionable improvements that align with Harvard Career Services standards.
        Prioritize the most critical violations that would prevent this resume from meeting professional standards.
        """

        result = await self.llm_call(prompt)

        # Add detailed analysis results
        result.update({
            "agent_name": self.agent_name,
            "analysis_type": "harvard_compliance",
            "target_roles": target_roles,
            "detailed_analysis": {
                "pronoun_violations": pronoun_violations,
                "passive_voice_issues": passive_voice_issues,
                "action_verb_analysis": action_verb_analysis,
                "abbreviation_issues": abbreviation_issues,
                "narrative_style_issues": narrative_style_issues,
                "quantification_analysis": quantification_analysis,
                "grammar_spelling_issues": grammar_spelling_issues
            }
        })

        return result

    def _detect_personal_pronouns(self, text: str) -> List[Dict[str, Any]]:
        """Detect personal pronoun usage (Harvard violation)."""
        violations = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            words = re.findall(r'\b\w+\b', line.lower())
            for word_pos, word in enumerate(words):
                for pronoun_type, pronouns in self.personal_pronouns.items():
                    if word in pronouns:
                        violations.append({
                            'pronoun': word,
                            'type': pronoun_type,
                            'line': line_num,
                            'position': word_pos,
                            'context': line.strip(),
                            'severity': 'critical' if pronoun_type == 'first_person' else 'high'
                        })

        return violations

    async def _detect_passive_voice(self, text: str) -> List[Dict[str, Any]]:
        """Detect passive voice constructions."""
        passive_patterns = [
            r'\b(was|were|is|are|been|being)\s+\w+ed\b',
            r'\b(was|were|is|are|been|being)\s+\w+en\b',
            r'\bthat\s+(was|were|is|are)\s+\w+ed\b',
            r'\bwhich\s+(was|were|is|are)\s+\w+ed\b'
        ]

        violations = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            for pattern in passive_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    violations.append({
                        'passive_phrase': match.group(),
                        'line': line_num,
                        'context': line.strip(),
                        'suggestion': f'Rewrite in active voice',
                        'severity': 'high'
                    })

        return violations

    def _analyze_action_verbs(self, text: str) -> Dict[str, Any]:
        """Analyze action verb usage and categorization."""
        bullet_points = re.findall(r'[•·▪▫▸▹‣⁃]\s*(.+)', text)

        analysis = {
            'total_bullets': len(bullet_points),
            'strong_verbs_found': [],
            'weak_verbs_found': [],
            'missing_verbs': [],
            'categories_used': set(),
            'missing_categories': [],
            'coverage_percentage': 0
        }

        if not bullet_points:
            return analysis

        for bullet in bullet_points:
            first_word = bullet.split()[0].lower() if bullet.split() else ''

            if first_word in self.all_action_verbs:
                analysis['strong_verbs_found'].append({
                    'verb': first_word,
                    'bullet': bullet[:50] + '...' if len(bullet) > 50 else bullet,
                    'category': self._get_verb_category(first_word)
                })
                analysis['categories_used'].add(self._get_verb_category(first_word))
            else:
                analysis['weak_verbs_found'].append({
                    'verb': first_word,
                    'bullet': bullet[:50] + '...' if len(bullet) > 50 else bullet,
                    'suggestion': self._suggest_action_verb(bullet)
                })

        # Calculate coverage
        verbs_with_action = len(analysis['strong_verbs_found'])
        analysis['coverage_percentage'] = (verbs_with_action / len(bullet_points)) * 100 if bullet_points else 0

        # Identify missing categories
        all_categories = set(self.action_verbs.keys())
        analysis['missing_categories'] = list(all_categories - analysis['categories_used'])

        return analysis

    def _get_verb_category(self, verb: str) -> str:
        """Get the category for a given action verb."""
        for category, verbs in self.action_verbs.items():
            if verb in verbs:
                return category
        return 'other'

    def _suggest_action_verb(self, bullet: str) -> str:
        """Suggest a strong action verb for a bullet point."""
        bullet_lower = bullet.lower()

        if any(word in bullet_lower for word in ['manage', 'lead', 'oversee']):
            return 'led'
        elif any(word in bullet_lower for word in ['create', 'build', 'make']):
            return 'developed'
        elif any(word in bullet_lower for word in ['improve', 'enhance', 'better']):
            return 'optimized'
        elif any(word in bullet_lower for word in ['analyze', 'examine', 'study']):
            return 'analyzed'
        elif any(word in bullet_lower for word in ['work', 'collaborate']):
            return 'collaborated'
        else:
            return 'accomplished'

    def _detect_abbreviations(self, text: str) -> List[Dict[str, Any]]:
        """Detect abbreviations that should be spelled out."""
        violations = []

        for abbrev, full_form in self.abbreviations_to_expand.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                violations.append({
                    'abbreviation': match.group(),
                    'full_form': full_form,
                    'position': match.start(),
                    'context': text[max(0, match.start()-30):match.end()+30],
                    'severity': 'medium'
                })

        return violations

    def _detect_narrative_style(self, text: str) -> List[Dict[str, Any]]:
        """Detect narrative style writing (paragraphs vs bullet points)."""
        violations = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Skip headers, contact info, and proper sections
            if (line_stripped.isupper() or
                '@' in line_stripped or
                line_stripped.startswith(('EXPERIENCE', 'EDUCATION', 'SKILLS', 'SUMMARY')) or
                len(line_stripped) < 10):
                continue

            # Detect narrative paragraphs (complete sentences without bullet points)
            if (not line_stripped.startswith(('•', '·', '-', '*', '▪', '▫')) and
                '.' in line_stripped and
                len(line_stripped) > 30 and
                not line_stripped.endswith(':') and
                ' ' in line_stripped):

                violations.append({
                    'line': line_num,
                    'content': line_stripped,
                    'issue': 'narrative_paragraph',
                    'suggestion': 'Convert to bullet point format',
                    'severity': 'high'
                })

        return violations

    def _analyze_quantification(self, text: str) -> Dict[str, Any]:
        """Analyze quantification of achievements."""
        bullet_points = re.findall(r'[•·▪▫▸▹‣⁃]\s*(.+)', text)

        analysis = {
            'total_bullets': len(bullet_points),
            'quantified_bullets': 0,
            'quantification_rate': 0,
            'quantified_examples': [],
            'missing_quantification': []
        }

        # Patterns for quantification
        quantification_patterns = [
            r'\b\d+%\b',  # Percentages
            r'\b\d+\+?\s*(million|thousand|billion)\b',  # Large numbers
            r'\b\d+[kK]\+?\b',  # Thousands (10k, 5K+)
            r'\$\d+',  # Dollar amounts
            r'\b\d+\s*(years?|months?|days?|hours?)\b',  # Time periods
            r'\b\d+\s*(people|team|members|users|customers)\b',  # People/users
            r'\b\d+x\b',  # Multipliers
            r'\b\d{1,3}(,\d{3})*\b'  # Formatted numbers
        ]

        for bullet in bullet_points:
            has_quantification = False
            for pattern in quantification_patterns:
                if re.search(pattern, bullet, re.IGNORECASE):
                    has_quantification = True
                    analysis['quantified_examples'].append({
                        'bullet': bullet[:100] + '...' if len(bullet) > 100 else bullet,
                        'quantification': re.findall(pattern, bullet, re.IGNORECASE)
                    })
                    break

            if has_quantification:
                analysis['quantified_bullets'] += 1
            else:
                analysis['missing_quantification'].append({
                    'bullet': bullet[:100] + '...' if len(bullet) > 100 else bullet,
                    'suggestion': 'Add specific metrics or numbers'
                })

        if bullet_points:
            analysis['quantification_rate'] = (analysis['quantified_bullets'] / len(bullet_points)) * 100

        return analysis

    async def _check_grammar_spelling(self, text: str) -> List[Dict[str, Any]]:
        """Basic grammar and spelling check."""
        issues = []

        # Basic patterns for common errors
        common_errors = [
            (r'\bteh\b', 'the', 'spelling'),
            (r'\brecieve\b', 'receive', 'spelling'),
            (r'\boccured\b', 'occurred', 'spelling'),
            (r'\bseperate\b', 'separate', 'spelling'),
            (r'\bdefinately\b', 'definitely', 'spelling'),
            (r'\.{2,}', '.', 'punctuation'),  # Multiple periods
            (r'\s{2,}', ' ', 'spacing'),  # Multiple spaces
            (r'\s+[,.]', '.', 'spacing'),  # Space before punctuation
        ]

        for pattern, correction, error_type in common_errors:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'error': match.group(),
                    'correction': correction,
                    'type': error_type,
                    'position': match.start(),
                    'context': text[max(0, match.start()-20):match.end()+20],
                    'severity': 'critical' if error_type == 'spelling' else 'medium'
                })

        return issues

    def _calculate_compliance_scores(self, pronoun_violations: List, passive_voice_issues: List,
                                   action_verb_analysis: Dict, abbreviation_issues: List,
                                   narrative_style_issues: List, quantification_analysis: Dict,
                                   grammar_spelling_issues: List) -> Dict[str, float]:
        """Calculate compliance scores based on violations."""

        # Base scores start at 10, deduct for violations
        language_score = 10 - min(10, len(pronoun_violations) * 2 + len(passive_voice_issues) * 0.5 + len(narrative_style_issues) * 1)

        action_verb_score = min(10, action_verb_analysis['coverage_percentage'] / 10)

        grammar_score = 10 - min(10, len(grammar_spelling_issues) * 1.5 + len(abbreviation_issues) * 0.5)

        quantification_score = min(10, quantification_analysis['quantification_rate'] / 10)

        overall_score = (language_score + action_verb_score + grammar_score + quantification_score) / 4

        return {
            'language_compliance': max(0, language_score),
            'action_verb_compliance': max(0, action_verb_score),
            'grammar_compliance': max(0, grammar_score),
            'quantification_compliance': max(0, quantification_score),
            'overall_compliance': max(0, overall_score)
        }

    def get_capabilities(self) -> List[str]:
        """Return Harvard compliance analysis capabilities."""
        return [
            "harvard_language_compliance",
            "personal_pronoun_detection",
            "passive_voice_detection",
            "action_verb_validation",
            "abbreviation_detection",
            "narrative_style_prevention",
            "quantification_enforcement",
            "grammar_spelling_validation"
        ]

    def validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate Harvard compliance analysis result structure."""
        required_fields = [
            "harvard_compliance_score",
            "language_compliance",
            "action_verb_compliance",
            "grammar_spelling_compliance",
            "quantification_compliance"
        ]
        return all(field in result for field in required_fields) and isinstance(result.get("harvard_compliance_score"), (int, float))