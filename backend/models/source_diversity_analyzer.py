from typing import List, Dict
from fact import Fact, SourceType
from collections import Counter
import math

class SourceDiversityAnalyzer:
    """
    Analyzes diversity of sources supporting claims.
    
    Evaluates whether evidence comes from varied source types
    (academic, news, government, etc.) or single category.
    Flags single-source-type claims as potentially biased.
    """
    
    def __init__(self):
        """Initialize source diversity analyzer."""
        pass
    
    def calculate_diversity_score(self, facts: List[Fact]) -> float:
        """
        Calculate diversity score based on source type distribution.
        
        Uses Shannon entropy to measure diversity:
        - High entropy = diverse sources (score near 100)
        - Low entropy = concentrated in few types (score near 0)
        
        Args:
            facts: List of facts to analyze
            
        Returns:
            Diversity score (0-100)
            
        Raises:
            ValueError: If facts list is empty
        """
        if not facts:
            raise ValueError("Facts list cannot be empty")
        
        # Count source types
        type_counts = Counter(fact.source_type for fact in facts)
        total = len(facts)
        
        # Calculate Shannon entropy
        entropy = 0.0
        for count in type_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        # Normalize to 0-100 scale
        # Maximum entropy occurs when all types are equally represented
        max_entropy = math.log2(len(SourceType)) if len(SourceType) > 0 else 1
        normalized_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        return round(normalized_score, 2)
    
    def identify_single_source_bias(self, facts: List[Fact], threshold: float = 0.7) -> Dict:
        """
        Identify if claim is biased toward single source type.
        
        Args:
            facts: List of facts to analyze
            threshold: Percentage threshold for single-type dominance (0-1)
            
        Returns:
            Dictionary with bias analysis
            
        Raises:
            ValueError: If facts list is empty or threshold invalid
        """
        if not facts:
            raise ValueError("Facts list cannot be empty")
        if threshold < 0 or threshold > 1:
            raise ValueError("Threshold must be between 0 and 1")
        
        type_counts = Counter(fact.source_type for fact in facts)
        total = len(facts)
        
        # Find dominant type
        dominant_type, dominant_count = type_counts.most_common(1)[0]
        dominant_percentage = dominant_count / total
        
        has_bias = dominant_percentage >= threshold
        
        return {
            "has_single_source_bias": has_bias,
            "dominant_source_type": dominant_type.value,
            "dominant_percentage": round(dominant_percentage * 100, 2),
            "source_count": total,
            "unique_source_types": len(type_counts),
            "threshold_percentage": threshold * 100
        }
    
    def recommend_additional_sources(self, facts: List[Fact]) -> List[str]:
        """
        Recommend source types that should be added for better diversity.
        
        Args:
            facts: List of facts currently supporting claim
            
        Returns:
            List of recommended SourceType values to add
        """
        if not facts:
            return [st.value for st in SourceType]
        
        # Get current source types
        current_types = {fact.source_type for fact in facts}
        
        # All possible source types
        all_types = set(SourceType)
        
        # Missing types
        missing_types = all_types - current_types
        
        # Prioritize high-credibility missing types
        priority_order = [
            SourceType.ACADEMIC,
            SourceType.SCIENTIFIC,
            SourceType.GOVERNMENT,
            SourceType.EXPERT,
            SourceType.ORGANIZATION,
            SourceType.NEWS,
            SourceType.OTHER
        ]
        
        recommendations = [
            st.value for st in priority_order 
            if st in missing_types
        ]
        
        return recommendations
    
    def compare_diversity(self, claim1_facts: List[Fact], claim2_facts: List[Fact]) -> Dict:
        """
        Compare source diversity between two claims.
        
        Args:
            claim1_facts: Facts supporting first claim
            claim2_facts: Facts supporting second claim
            
        Returns:
            Dictionary with comparison results
        """
        score1 = self.calculate_diversity_score(claim1_facts) if claim1_facts else 0.0
        score2 = self.calculate_diversity_score(claim2_facts) if claim2_facts else 0.0
        
        return {
            "claim1_diversity_score": score1,
            "claim2_diversity_score": score2,
            "difference": round(abs(score1 - score2), 2),
            "more_diverse": "claim1" if score1 > score2 else "claim2" if score2 > score1 else "equal"
        }
    
    def flag_low_diversity(self, facts: List[Fact], minimum_score: float = 40.0) -> bool:
        """
        Flag claims with low source diversity for additional research.
        
        Args:
            facts: List of facts to evaluate
            minimum_score: Minimum acceptable diversity score
            
        Returns:
            True if diversity is below threshold (needs more research)
        """
        if not facts:
            return True
        
        score = self.calculate_diversity_score(facts)
        return score < minimum_score
    
    def generate_diversity_report(self, facts: List[Fact]) -> Dict:
        """
        Generate comprehensive diversity analysis report.
        
        Args:
            facts: List of facts to analyze
            
        Returns:
            Detailed diversity report
        """
        if not facts:
            return {
                "error": "No facts provided",
                "diversity_score": 0,
                "recommendations": [st.value for st in SourceType]
            }
        
        diversity_score = self.calculate_diversity_score(facts)
        bias_analysis = self.identify_single_source_bias(facts)
        recommendations = self.recommend_additional_sources(facts)
        needs_research = self.flag_low_diversity(facts)
        
        # Source type breakdown
        type_counts = Counter(fact.source_type for fact in facts)
        source_breakdown = {
            st.value: type_counts.get(st, 0) 
            for st in SourceType
        }
        
        return {
            "diversity_score": diversity_score,
            "total_sources": len(facts),
            "unique_source_types": len(type_counts),
            "source_type_breakdown": source_breakdown,
            "has_bias": bias_analysis["has_single_source_bias"],
            "dominant_source": bias_analysis["dominant_source_type"],
            "dominant_percentage": bias_analysis["dominant_percentage"],
            "recommended_additions": recommendations,
            "needs_additional_research": needs_research,
            "quality_assessment": self._assess_quality(diversity_score)
        }
    
    def _assess_quality(self, diversity_score: float) -> str:
        """
        Assess overall quality based on diversity score.
        
        Args:
            diversity_score: Calculated diversity score
            
        Returns:
            Quality assessment string
        """
        if diversity_score >= 70:
            return "Excellent - highly diverse sources"
        elif diversity_score >= 50:
            return "Good - adequate source diversity"
        elif diversity_score >= 30:
            return "Fair - limited diversity, consider additional sources"
        else:
            return "Poor - single-source bias detected, needs more diverse evidence"