import pytest
from credibility_calculator import CredibilityCalculator
from fact import Fact, SourceType

class TestAggregateScore:
	def test_single_fact(self):
		calc = CredibilityCalculator()
		fact = Fact("Statement", "https://example.com", "Source", SourceType.ACADEMIC, 90.0)
		score = calc.calculate_aggregate_score([fact])
		assert score == 90.0
	
	def test_multiple_facts_same_type(self):
		calc = CredibilityCalculator()
		fact1 = Fact("S1", "https://ex1.com", "S1", SourceType.ACADEMIC, 80.0)
		fact2 = Fact("S2", "https://ex2.com", "S2", SourceType.ACADEMIC, 90.0)
		score = calc.calculate_aggregate_score([fact1, fact2])
		assert score == 85.0
	
	def test_multiple_facts_different_types(self):
		calc = CredibilityCalculator()
		fact1 = Fact("S1", "https://ex1.com", "S1", SourceType.ACADEMIC, 90.0)  # weight 1.0
		fact2 = Fact("S2", "https://ex2.com", "S2", SourceType.NEWS, 70.0)	  # weight 0.7
		score = calc.calculate_aggregate_score([fact1, fact2])
		assert 75 < score < 85  # Weighted average
	
	def test_empty_facts_raises_error(self):
		calc = CredibilityCalculator()
		with pytest.raises(ValueError):
			calc.calculate_aggregate_score([])

class TestConflictingFacts:
	def test_only_supporting_facts(self):
		calc = CredibilityCalculator()
		supporting = [Fact("S1", "https://ex.com", "S1", SourceType.ACADEMIC, 85.0)]
		contradicting = []
		score, explanation = calc.handle_conflicting_facts(supporting, contradicting)
		assert score > 50
		assert "1 supporting" in explanation
	
	def test_only_contradicting_facts(self):
		calc = CredibilityCalculator()
		supporting = []
		contradicting = [Fact("S1", "https://ex.com", "S1", SourceType.ACADEMIC, 85.0)]
		score, explanation = calc.handle_conflicting_facts(supporting, contradicting)
		assert score < 50
	
	def test_balanced_conflict(self):
		calc = CredibilityCalculator()
		supporting = [Fact("S1", "https://ex.com", "S1", SourceType.ACADEMIC, 80.0)]
		contradicting = [Fact("S2", "https://ex.com", "S2", SourceType.ACADEMIC, 80.0)]
		score, explanation = calc.handle_conflicting_facts(supporting, contradicting)
		assert 45 < score < 55
	
	def test_empty_both_raises_error(self):
		calc = CredibilityCalculator()
		with pytest.raises(ValueError):
			calc.handle_conflicting_facts([], [])

class TestExplanation:
	def test_explain_calculation(self):
		calc = CredibilityCalculator()
		fact = Fact("Statement", "https://example.com", "Journal", SourceType.SCIENTIFIC, 85.0)
		explanation = calc.explain_calculation([fact])
		assert "Journal" in explanation
		assert "Scientific" in explanation
		assert "85" in explanation
	
	def test_explain_empty_facts(self):
		calc = CredibilityCalculator()
		explanation = calc.explain_calculation([])
		assert "No facts" in explanation

class TestSourceBreakdown:
	def test_source_breakdown(self):
		calc = CredibilityCalculator()
		facts = [
			Fact("S1", "https://ex.com", "S1", SourceType.ACADEMIC, 80.0),
			Fact("S2", "https://ex.com", "S2", SourceType.ACADEMIC, 85.0),
			Fact("S3", "https://ex.com", "S3", SourceType.NEWS, 70.0)
		]
		breakdown = calc.get_source_breakdown(facts)
		assert breakdown["Academic"] == 2
		assert breakdown["News"] == 1


