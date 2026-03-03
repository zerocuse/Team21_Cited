from typing import List, Dict, Tuple
from fact import Fact, SourceType

class CredibilityCalculator:
	"""
	Calculates aggregate credibility scores from multiple facts.
	
	Weights sources by type:
	- Academic: 1.0
	- Scientific: 0.95
	- Government: 0.9
	- Expert: 0.85
	- News: 0.7
	- Organization: 0.65
	- Other: 0.5
	"""
	
	# Source type weights
	WEIGHTS = {
		SourceType.ACADEMIC: 1.0,
		SourceType.SCIENTIFIC: 0.95,
		SourceType.GOVERNMENT: 0.9,
		SourceType.EXPERT: 0.85,
		SourceType.NEWS: 0.7,
		SourceType.ORGANIZATION: 0.65,
		SourceType.OTHER: 0.5
	}
	
	def __init__(self):
		"""Initialize calculator."""
		self._calculation_history: List[Dict] = []
	
	def calculate_aggregate_score(self, facts: List[Fact]) -> float:
		"""
		Calculate weighted average credibility from multiple facts.
		
		Args:
			facts: List of Fact objects about the same claim
			
		Returns:
			Aggregate credibility score (0-100)
			
		Raises:
			ValueError: If facts list is empty
		"""
		if not facts:
			raise ValueError("Facts list cannot be empty")
		
		weighted_sum = 0.0
		total_weight = 0.0
		
		for fact in facts:
			weight = self.WEIGHTS.get(fact.source_type, 0.5)
			weighted_sum += fact.credibility_score * weight
			total_weight += weight
		
		aggregate = weighted_sum / total_weight if total_weight > 0 else 0.0
		
		# Store calculation for explanation
		self._calculation_history.append({
			"num_facts": len(facts),
			"aggregate_score": aggregate,
			"facts_used": [f.fact_id for f in facts]
		})
		
		return round(aggregate, 2)
	
	def handle_conflicting_facts(self, supporting_facts: List[Fact], 
								  contradicting_facts: List[Fact]) -> Tuple[float, str]:
		"""
		Calculate credibility when facts conflict.
		
		Args:
			supporting_facts: Facts that support the claim
			contradicting_facts: Facts that contradict the claim
			
		Returns:
			Tuple of (credibility_score, explanation)
			
		Raises:
			ValueError: If both lists are empty
		"""
		if not supporting_facts and not contradicting_facts:
			raise ValueError("At least one fact list must have facts")
		
		support_score = self.calculate_aggregate_score(supporting_facts) if supporting_facts else 0.0
		contradict_score = self.calculate_aggregate_score(contradicting_facts) if contradicting_facts else 0.0
		
		# Calculate net credibility
		support_weight = len(supporting_facts)
		contradict_weight = len(contradicting_facts)
		total = support_weight + contradict_weight
		
		net_score = ((support_score * support_weight) - (contradict_score * contradict_weight)) / total
		
		# Normalize to 0-100 range
		final_score = max(0, min(100, 50 + net_score / 2))
		
		explanation = f"{len(supporting_facts)} supporting sources (avg: {support_score:.1f}), "
		explanation += f"{len(contradicting_facts)} contradicting sources (avg: {contradict_score:.1f}). "
		explanation += f"Net credibility: {final_score:.1f}"
		
		return round(final_score, 2), explanation
	
	def explain_calculation(self, facts: List[Fact]) -> str:
		"""
		Generate explanation of how score was calculated.
		
		Args:
			facts: List of facts used in calculation
			
		Returns:
			Human-readable explanation string
		"""
		if not facts:
			return "No facts provided for calculation"
		
		explanation = f"Credibility calculated from {len(facts)} source(s):\n\n"
		
		for i, fact in enumerate(facts, 1):
			weight = self.WEIGHTS.get(fact.source_type, 0.5)
			explanation += f"{i}. {fact.source_name} ({fact.source_type.value})\n"
			explanation += f"   - Base credibility: {fact.credibility_score}\n"
			explanation += f"   - Source weight: {weight}\n"
			explanation += f"   - Weighted score: {fact.credibility_score * weight:.2f}\n\n"
		
		aggregate = self.calculate_aggregate_score(facts)
		explanation += f"Aggregate credibility score: {aggregate}"
		
		return explanation
	
	def get_source_breakdown(self, facts: List[Fact]) -> Dict[str, int]:
		"""
		Get breakdown of facts by source type.
		
		Args:
			facts: List of facts to analyze
			
		Returns:
			Dictionary mapping source types to counts
		"""
		breakdown = {}
		for fact in facts:
			source_type = fact.source_type.value
			breakdown[source_type] = breakdown.get(source_type, 0) + 1
		return breakdown

