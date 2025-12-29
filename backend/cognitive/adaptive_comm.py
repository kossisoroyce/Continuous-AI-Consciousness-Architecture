"""
Adaptive Communication System
Adjusts AI communication style to match operator's vocabulary and expertise level
"""
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import re
import math

class CommunicationStyle(str, Enum):
    """Communication style presets"""
    TECHNICAL = "technical"      # Full jargon, precise terminology
    PROFESSIONAL = "professional"  # Balanced technical/plain language
    CONVERSATIONAL = "conversational"  # Plain language, explanations
    SIMPLIFIED = "simplified"    # Basic terms, step-by-step

class ExpertiseLevel(str, Enum):
    """Operator expertise assessment"""
    EXPERT = "expert"        # 10+ years, advanced terminology
    PROFICIENT = "proficient"  # 3-10 years, standard terminology  
    INTERMEDIATE = "intermediate"  # 1-3 years, guided language
    NOVICE = "novice"        # <1 year, simple explanations

class OperatorProfile(BaseModel):
    """Learned operator communication profile"""
    operator_id: str
    
    # Vocabulary metrics
    avg_word_length: float = 5.0
    avg_sentence_length: float = 12.0
    vocabulary_richness: float = 0.5  # Type-token ratio
    technical_term_ratio: float = 0.1
    
    # Reading level (Flesch-Kincaid)
    reading_grade_level: float = 10.0
    
    # Expertise indicators
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    domain_familiarity: Dict[str, float] = Field(default_factory=dict)
    
    # Preferences
    preferred_style: CommunicationStyle = CommunicationStyle.PROFESSIONAL
    prefers_detail: bool = True
    prefers_examples: bool = True
    
    # Learning
    messages_analyzed: int = 0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Domain-specific vocabulary
DOMAIN_VOCABULARY = {
    "military": [
        "sitrep", "ops", "tactical", "strategic", "recon", "intel",
        "engagement", "extract", "insertion", "rally", "overwatch",
        "bearing", "heading", "grid", "coordinates", "waypoint"
    ],
    "aviation": [
        "altitude", "airspeed", "heading", "pitch", "yaw", "roll",
        "throttle", "flaps", "aileron", "rudder", "climb", "descent",
        "hover", "loiter", "waypoint", "flight path"
    ],
    "technical": [
        "algorithm", "model", "detection", "classification", "confidence",
        "threshold", "latency", "bandwidth", "resolution", "inference",
        "calibration", "parameters", "optimization"
    ]
}

# Vocabulary complexity mapping
SIMPLE_ALTERNATIVES = {
    "reconnaissance": "scouting",
    "surveillance": "watching",
    "engagement": "contact",
    "neutralize": "stop",
    "exfiltrate": "leave",
    "infiltrate": "enter",
    "optimal": "best",
    "suboptimal": "not ideal",
    "classification": "type",
    "identification": "ID",
    "probability": "chance",
    "trajectory": "path",
    "velocity": "speed",
    "altitude": "height",
    "azimuth": "direction",
    "proximity": "nearness",
    "approximately": "about",
    "subsequently": "then",
    "consequently": "so",
    "nevertheless": "but",
    "furthermore": "also",
    "regarding": "about",
    "numerous": "many",
    "sufficient": "enough",
    "commence": "start",
    "terminate": "end",
    "utilize": "use",
    "implement": "do",
    "facilitate": "help",
    "endeavor": "try",
}

class AdaptiveCommunicator:
    """
    Adapts AI communication to match operator's style and expertise
    """
    
    def __init__(self):
        self.profiles: Dict[str, OperatorProfile] = {}
        self.default_profile = OperatorProfile(operator_id="default")
    
    def analyze_message(self, operator_id: str, message: str) -> OperatorProfile:
        """Analyze operator message to update their profile"""
        if operator_id not in self.profiles:
            self.profiles[operator_id] = OperatorProfile(operator_id=operator_id)
        
        profile = self.profiles[operator_id]
        
        # Tokenize
        words = re.findall(r'\b[a-zA-Z]+\b', message.lower())
        sentences = re.split(r'[.!?]+', message)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not words:
            return profile
        
        # Calculate metrics
        avg_word_len = sum(len(w) for w in words) / len(words)
        avg_sent_len = len(words) / max(1, len(sentences))
        unique_words = len(set(words))
        vocab_richness = unique_words / len(words) if words else 0
        
        # Count technical terms
        technical_count = 0
        for domain, terms in DOMAIN_VOCABULARY.items():
            domain_count = sum(1 for w in words if w in terms)
            technical_count += domain_count
            
            # Update domain familiarity
            if domain_count > 0:
                current = profile.domain_familiarity.get(domain, 0)
                profile.domain_familiarity[domain] = current * 0.9 + 0.1 * (domain_count / len(words))
        
        tech_ratio = technical_count / len(words) if words else 0
        
        # Calculate Flesch-Kincaid Grade Level
        syllables = sum(self._count_syllables(w) for w in words)
        avg_syllables = syllables / len(words) if words else 1
        fk_grade = 0.39 * avg_sent_len + 11.8 * avg_syllables - 15.59
        fk_grade = max(1, min(18, fk_grade))
        
        # Exponential moving average update
        alpha = 0.2
        profile.avg_word_length = alpha * avg_word_len + (1 - alpha) * profile.avg_word_length
        profile.avg_sentence_length = alpha * avg_sent_len + (1 - alpha) * profile.avg_sentence_length
        profile.vocabulary_richness = alpha * vocab_richness + (1 - alpha) * profile.vocabulary_richness
        profile.technical_term_ratio = alpha * tech_ratio + (1 - alpha) * profile.technical_term_ratio
        profile.reading_grade_level = alpha * fk_grade + (1 - alpha) * profile.reading_grade_level
        
        # Update expertise level
        profile.expertise_level = self._assess_expertise(profile)
        profile.preferred_style = self._infer_style(profile)
        
        profile.messages_analyzed += 1
        profile.last_updated = datetime.now(timezone.utc)
        
        return profile
    
    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        prev_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1
        
        return max(1, count)
    
    def _assess_expertise(self, profile: OperatorProfile) -> ExpertiseLevel:
        """Assess operator expertise from communication patterns"""
        score = 0
        
        # Technical vocabulary usage
        score += profile.technical_term_ratio * 30
        
        # Reading level
        if profile.reading_grade_level >= 14:
            score += 25
        elif profile.reading_grade_level >= 12:
            score += 15
        elif profile.reading_grade_level >= 10:
            score += 10
        
        # Vocabulary richness
        score += profile.vocabulary_richness * 20
        
        # Domain familiarity
        max_familiarity = max(profile.domain_familiarity.values()) if profile.domain_familiarity else 0
        score += max_familiarity * 25
        
        if score >= 60:
            return ExpertiseLevel.EXPERT
        elif score >= 40:
            return ExpertiseLevel.PROFICIENT
        elif score >= 20:
            return ExpertiseLevel.INTERMEDIATE
        return ExpertiseLevel.NOVICE
    
    def _infer_style(self, profile: OperatorProfile) -> CommunicationStyle:
        """Infer preferred communication style"""
        if profile.expertise_level == ExpertiseLevel.EXPERT:
            return CommunicationStyle.TECHNICAL
        elif profile.expertise_level == ExpertiseLevel.PROFICIENT:
            return CommunicationStyle.PROFESSIONAL
        elif profile.expertise_level == ExpertiseLevel.INTERMEDIATE:
            return CommunicationStyle.CONVERSATIONAL
        return CommunicationStyle.SIMPLIFIED
    
    def adapt_response(
        self, 
        response: str, 
        operator_id: str,
        override_style: CommunicationStyle = None
    ) -> str:
        """Adapt AI response to match operator's communication style"""
        profile = self.profiles.get(operator_id, self.default_profile)
        style = override_style or profile.preferred_style
        
        if style == CommunicationStyle.TECHNICAL:
            # Keep as-is, possibly add technical details
            return response
        
        elif style == CommunicationStyle.PROFESSIONAL:
            # Light simplification
            return self._simplify_response(response, level=0.3)
        
        elif style == CommunicationStyle.CONVERSATIONAL:
            # Moderate simplification with explanations
            simplified = self._simplify_response(response, level=0.6)
            return self._add_context(simplified, profile)
        
        elif style == CommunicationStyle.SIMPLIFIED:
            # Heavy simplification, short sentences
            simplified = self._simplify_response(response, level=0.9)
            return self._break_into_steps(simplified)
        
        return response
    
    def _simplify_response(self, text: str, level: float) -> str:
        """Simplify vocabulary based on level (0-1)"""
        result = text
        
        for complex_word, simple_word in SIMPLE_ALTERNATIVES.items():
            # Probabilistically replace based on level
            if level > 0.5 or (level > 0.3 and len(complex_word) > 8):
                pattern = re.compile(re.escape(complex_word), re.IGNORECASE)
                result = pattern.sub(simple_word, result)
        
        return result
    
    def _add_context(self, text: str, profile: OperatorProfile) -> str:
        """Add contextual explanations for less familiar operators"""
        # Add brief explanations for technical terms
        explanations = {
            "confidence": "(certainty level)",
            "threshold": "(minimum level)",
            "detection": "(identified object)",
            "calibration": "(accuracy adjustment)",
        }
        
        result = text
        for term, explanation in explanations.items():
            if term in result.lower() and profile.technical_term_ratio < 0.15:
                pattern = re.compile(f'({term})', re.IGNORECASE)
                result = pattern.sub(f'\\1 {explanation}', result, count=1)
        
        return result
    
    def _break_into_steps(self, text: str) -> str:
        """Break complex response into numbered steps"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= 2:
            return text
        
        result = []
        for i, sentence in enumerate(sentences, 1):
            if sentence.strip():
                result.append(f"{i}. {sentence.strip()}")
        
        return "\n".join(result)
    
    def get_profile(self, operator_id: str) -> OperatorProfile:
        """Get or create operator profile"""
        if operator_id not in self.profiles:
            self.profiles[operator_id] = OperatorProfile(operator_id=operator_id)
        return self.profiles[operator_id]
    
    def get_style_prompt(self, operator_id: str) -> str:
        """Get LLM system prompt modifier for operator's style"""
        profile = self.get_profile(operator_id)
        
        prompts = {
            CommunicationStyle.TECHNICAL: (
                "Use precise technical terminology. Be concise and direct. "
                "Assume expertise in the domain. Use military/aviation jargon where appropriate."
            ),
            CommunicationStyle.PROFESSIONAL: (
                "Balance technical accuracy with clarity. Define unusual terms briefly. "
                "Be professional but accessible."
            ),
            CommunicationStyle.CONVERSATIONAL: (
                "Use plain language. Explain technical concepts in simple terms. "
                "Provide examples when helpful. Be friendly but focused."
            ),
            CommunicationStyle.SIMPLIFIED: (
                "Use simple words and short sentences. Break complex ideas into steps. "
                "Avoid jargon. Provide clear, direct instructions."
            )
        }
        
        base_prompt = prompts.get(profile.preferred_style, prompts[CommunicationStyle.PROFESSIONAL])
        
        # Add domain-specific context
        if profile.domain_familiarity:
            top_domain = max(profile.domain_familiarity.items(), key=lambda x: x[1])[0]
            base_prompt += f" The operator has familiarity with {top_domain} terminology."
        
        return base_prompt

# Global instance
adaptive_communicator = AdaptiveCommunicator()
