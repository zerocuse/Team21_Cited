from typing import List, Dict, Tuple, Set
from fact import Fact
from credibility_calculator import CredibilityCalculator

class FactComparison:
	"""
	Compares and analyzes relationships between facts.
	
	Capabilities:
	- Find similar facts using keyword matching
	- Compare credibility scores between related facts
	- Identify contradicting facts (same topic, different conclusions)
	- Suggest fact merging when duplicates detected
	- Generate comparison reports with similarity scores
	"""
	
	def __init__(self):
		"""Initialize fact comparison engine."""
		self._credibility_calc = CredibilityCalculator()
	
	def find_similar_facts(self, target_fact: Fact, fact_database: List[Fact], 
						  threshold: float = 0.3) -> List[Tuple[Fact, float]]:
		"""
		Find facts similar to target fact using keyword matching.
		
		Args:
			target_fact: Fact to compare against
			fact_database: List of facts to search
			threshold: Minimum similarity score (0-1) to include in results
			
		Returns:
			List of (Fact, similarity_score) tuples, sorted by similarity
			
		Raises:
			ValueError: If threshold is out of range
		"""
		if threshold < 0 or threshold > 1:
			raise ValueError("Threshold must be between 0 and 1")
		
		results = []
		target_keywords = self._extract_keywords(target_fact.statement)
		
		for fact in fact_database:
			if fact.fact_id == target_fact.fact_id:
				continue  # Skip comparing fact to itself
			
			similarity = self._calculate_similarity(target_keywords, fact.statement)
			if similarity >= threshold:
				results.append((fact, similarity))
		
		# Sort by similarity descending
		results.sort(key=lambda x: x[1], reverse=True)
		return results
	
	def _extract_keywords(self, text: str) -> Set[str]:
		"""
		Extract keywords from text (simple word-based approach).
		
		Args:
			text: Text to extract keywords from
			
		Returns:
			Set of lowercase keywords
		"""
		# Remove common words (stopwords)
		stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
					'for', 'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were',
					'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did'}
		
		words = text.lower().split()
		keywords = {w.strip('.,!?;:') for w in words if w.lower() not in stopwords and len(w) > 2}
		return keywords
	
	def _calculate_similarity(self, keywords: Set[str], text: str) -> float:
		"""
		Calculate similarity between keywords and text.
		
		Args:
			keywords: Set of keywords to match
			text: Text to compare against
			
		Returns:
			Similarity score (0-1)
		"""
		if not keywords:
			return 0.0
		
		text_keywords = self._extract_keywords(text)
		if not text_keywords:
			return 0.0
		
		# Jaccard similarity: intersection / union
		intersection = len(keywords & text_keywords)
		union = len(keywords | text_keywords)
		
		return intersection / union if union > 0 else 0.0
	
	def compare_credibility(self, fact1: Fact, fact2: Fact) -> Dict:
		"""
		Compare credibility scores between two facts.
		
		Args:
			fact1: First fact
			fact2: Second fact
			
		Returns:
			Dictionary with comparison results
		"""
		diff = abs(fact1.credibility_score - fact2.credibility_score)
		higher = fact1 if fact1.credibility_score > fact2.credibility_score else fact2
		
		return {
			"fact1_id": fact1.fact_id,
			"fact1_score": fact1.credibility_score,
			"fact2_id": fact2.fact_id,
			"fact2_score": fact2.credibility_score,
			"difference": round(diff, 2),
			"higher_credibility": higher.fact_id,
			"significant_difference": diff > 20.0  # >20 points is significant
		}
	
	def identify_contradictions(self, facts: List[Fact], similarity_threshold: float = 0.5) -> List[Dict]:
		"""
		Identify facts that discuss same topic but have different conclusions.
		
		Args:
			facts: List of facts to analyze
			similarity_threshold: How similar statements must be to be considered same topic
			
		Returns:
			List of contradiction reports
		"""
		contradictions = []
		
		for i, fact1 in enumerate(facts):
			for fact2 in facts[i+1:]:
				similarity = self._calculate_similarity(
					self._extract_keywords(fact1.statement),
					fact2.statement
				)
				
				if similarity >= similarity_threshold:
					# Same topic, check if credibility scores differ significantly
					cred_diff = abs(fact1.credibility_score - fact2.credibility_score)
					
					if cred_diff > 30.0:  # Significant disagreement
						contradictions.append({
							"fact1": {
								"id": fact1.fact_id,
								"statement": fact1.statement,
								"credibility": fact1.credibility_score,
								"source": fact1.source_name
							},
							"fact2": {
								"id": fact2.fact_id,
								"statement": fact2.statement,
								"credibility": fact2.credibility_score,
								"source": fact2.source_name
							},
							"similarity": round(similarity, 2),
							"credibility_difference": round(cred_diff, 2)
						})
		
		return contradictions
	
	def suggest_merging(self, facts: List[Fact], similarity_threshold: float = 0.8) -> List[Dict]:
		"""
		Suggest facts that should be merged (likely duplicates).
		
		Args:
			facts: List of facts to analyze
			similarity_threshold: How similar facts must be to suggest merging
			
		Returns:
			List of merge suggestions
		"""
		suggestions = []
		
		for i, fact1 in enumerate(facts):
			for fact2 in facts[i+1:]:
				similarity = self._calculate_similarity(
					self._extract_keywords(fact1.statement),
					fact2.statement
				)
				
				if similarity >= similarity_threshold:
					suggestions.append({
						"fact1_id": fact1.fact_id,
						"fact2_id": fact2.fact_id,
						"similarity": round(similarity, 2),
						"reason": "High statement similarity suggests duplicate",
						"recommended_action": "merge",
						"keep_higher_credibility": fact1.fact_id if fact1.credibility_score > fact2.credibility_score else fact2.fact_id
					})
		
		return suggestions
	
	def generate_comparison_report(self, target_fact: Fact, related_facts: List[Fact]) -> Dict:
		"""
		Generate comprehensive comparison report.
		
		Args:
			target_fact: Primary fact being analyzed
			related_facts: Facts to compare against
			
		Returns:
			Detailed comparison report
		"""
		similar_facts = self.find_similar_facts(target_fact, related_facts)
		
		# Find potential contradictions
		all_facts = [target_fact] + related_facts
		contradictions = self.identify_contradictions(all_facts)
		
		# Find merge candidates
		merge_suggestions = self.suggest_merging(all_facts)
		
		# Calculate average credibility of similar facts
		if similar_facts:
			avg_credibility = sum(f.credibility_score for f, _ in similar_facts) / len(similar_facts)
		else:
			avg_credibility = 0.0
		
		return {
			"target_fact": {
				"id": target_fact.fact_id,
				"statement": target_fact.statement,
				"credibility": target_fact.credibility_score
			},
			"similar_facts_count": len(similar_facts),
			"similar_facts": [
				{
					"id": fact.fact_id,
					"statement": fact.statement,
					"similarity_score": round(score * 100, 2),
					"credibility": fact.credibility_score
				}
				for fact, score in similar_facts[:5]  # Top 5
			],
			"average_similar_credibility": round(avg_credibility, 2),
			"contradictions_found": len(contradictions),
			"contradictions": contradictions,
			"merge_suggestions_count": len(merge_suggestions),
			"merge_suggestions": merge_suggestions
		}