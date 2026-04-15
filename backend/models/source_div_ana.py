from typing import List, Dict, Optional
from fact import Fact, SourceType
import math

class SourceDiversityAnalyzer:
    """
    Analyzes the diversity of sources supporting a claim.
    Checks if evidence comes from varied source types rather than
    a single category. Flags claims supported only by one source
    type as potentially biased.
    """

    def __init__(self, facts: Optional[List[Fact]] = None):
        """
        Initialize analyzer with optional list of facts.

        Args:
            facts: List of Fact objects to analyze
        """
        self._facts = facts if facts else []

    def add_fact(self, fact: Fact):
        """
        Add a fact to the analyzer.

        Args:
            fact: Fact object to add
        """
        self._facts.append(fact)

    def get_source_type_distribution(self) -> Dict[str, int]:
        """
        Count how many facts come from each source type.

        Returns:
            Dictionary mapping source type name to count
        """
        distribution = {}
        for fact in self._facts:
            source_type = fact.source_type.value if hasattr(fact.source_type, 'value') else str(fact.source_type)
            distribution[source_type] = distribution.get(source_type, 0) + 1
        return distribution

    def calculate_diversity_score(self) -> float:
        """
        Calculate diversity score (0-100) using Shannon entropy.
        Higher score means more diverse sources.

        Returns:
            Diversity score as float between 0 and 100
        """
        if not self._facts:
            return 0.0

        distribution = self.get_source_type_distribution()
        total = len(self._facts)
        entropy = 0.0

        for count in distribution.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)

        max_entropy = math.log2(len(SourceType)) if len(SourceType) > 1 else 1
        score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0.0
        return round(score, 2)

    def is_single_source_biased(self) -> bool:
        """
        Check if all facts come from only one source type.

        Returns:
            True if all facts are from the same source type
        """
        distribution = self.get_source_type_distribution()
        return len(distribution) == 1 and len(self._facts) > 0

    def get_missing_source_types(self) -> List[str]:
        """
        Identify which source types are not represented.

        Returns:
            List of source type names not present in current facts
        """
        present = set(self.get_source_type_distribution().keys())
        all_types = set(s.value for s in SourceType)
        return list(all_types - present)

    def recommend_additional_sources(self) -> List[str]:
        """
        Recommend source types needed to improve diversity.

        Returns:
            List of recommended source type names
        """
        missing = self.get_missing_source_types()
        distribution = self.get_source_type_distribution()

        if not distribution:
            return [s.value for s in SourceType]

        min_count = min(distribution.values())
        underrepresented = [
            source_type for source_type, count in distribution.items()
            if count == min_count
        ]

        recommendations = missing + underrepresented
        return list(set(recommendations))

    def compare_diversity(self, other: 'SourceDiversityAnalyzer') -> Dict[str, float]:
        """
        Compare diversity score of this claim vs another.

        Args:
            other: Another SourceDiversityAnalyzer to compare with

        Returns:
            Dictionary with both scores and which is more diverse
        """
        score_a = self.calculate_diversity_score()
        score_b = other.calculate_diversity_score()

        return {
            "this_score": score_a,
            "other_score": score_b,
            "more_diverse": "this" if score_a >= score_b else "other",
            "difference": round(abs(score_a - score_b), 2)
        }

    def flag_low_diversity(self, threshold: float = 40.0) -> bool:
        """
        Flag claim as needing additional research if diversity is low.

        Args:
            threshold: Score below which claim is flagged (default 40)

        Returns:
            True if diversity score is below threshold
        """
        return self.calculate_diversity_score() < threshold

    def generate_diversity_report(self) -> Dict:
        """
        Generate full diversity report with recommendations.

        Returns:
            Dictionary with all diversity analysis data
        """
        return {
            "diversity_score": self.calculate_diversity_score(),
            "source_type_distribution": self.get_source_type_distribution(),
            "is_single_source_biased": self.is_single_source_biased(),
            "missing_source_types": self.get_missing_source_types(),
            "recommendations": self.recommend_additional_sources(),
            "flagged_for_research": self.flag_low_diversity()
        }