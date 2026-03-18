import pytest
from fact_comparison import FactComparison
from fact import Fact, SourceType

class TestKeywordExtraction:
	def test_extract_keywords_removes_stopwords(self):
		comp = FactComparison()
		keywords = comp._extract_keywords("The quick brown fox jumps over the lazy dog")
		assert "the" not in keywords
		assert "quick" in keywords
		assert "fox" in keywords
	
	def test_extract_keywords_lowercase(self):
		comp = FactComparison()
		keywords = comp._extract_keywords("Python Programming")
		assert "python" in keywords
		assert "programming" in keywords

class TestSimilarityCalculation:
	def test_calculate_similarity_identical(self):
		comp = FactComparison()
		keywords = {"water", "boils", "100", "celsius"}
		text = "water boils at 100 celsius"
		similarity = comp._calculate_similarity(keywords, text)
		assert similarity > 0.8
	
	def test_calculate_similarity_different(self):
		comp = FactComparison()
		keywords = {"water", "boils"}
		text = "dogs bark loudly"
		similarity = comp._calculate_similarity(keywords, text)
		assert similarity < 0.2
	
	def test_calculate_similarity_empty_keywords(self):
		comp = FactComparison()
		similarity = comp._calculate_similarity(set(), "some text")
		assert similarity == 0.0

class TestFindSimilarFacts:
	def test_find_similar_facts(self):
		comp = FactComparison()
		target = Fact("Water boils at 100C", "https://ex.com", "Source", SourceType.SCIENTIFIC, 90.0)
		
		similar = Fact("Water boils at 100 degrees", "https://ex2.com", "Source2", SourceType.SCIENTIFIC, 85.0)
		different = Fact("Dogs are mammals", "https://ex3.com", "Source3", SourceType.SCIENTIFIC, 80.0)
		
		database = [similar, different]
		results = comp.find_similar_facts(target, database, threshold=0.3)
		
		assert len(results) >= 1
		assert results[0][0].fact_id == similar.fact_id
	
	def test_find_similar_excludes_self(self):
		comp = FactComparison()
		fact = Fact("Statement", "https://ex.com", "Source", SourceType.NEWS, 80.0)
		
		results = comp.find_similar_facts(fact, [fact], threshold=0.1)
		assert len(results) == 0
	
	def test_invalid_threshold_raises_error(self):
		comp = FactComparison()
		fact = Fact("Statement", "https://ex.com", "Source", SourceType.NEWS, 80.0)
		
		with pytest.raises(ValueError):
			comp.find_similar_facts(fact, [], threshold=1.5)

class TestCredibilityComparison:
	def test_compare_credibility(self):
		comp = FactComparison()
		fact1 = Fact("Fact 1", "https://ex1.com", "S1", SourceType.ACADEMIC, 90.0)
		fact2 = Fact("Fact 2", "https://ex2.com", "S2", SourceType.NEWS, 70.0)
		
		result = comp.compare_credibility(fact1, fact2)
		
		assert result["fact1_score"] == 90.0
		assert result["fact2_score"] == 70.0
		assert result["difference"] == 20.0
		assert result["higher_credibility"] == fact1.fact_id
	
	def test_significant_difference_flag(self):
		comp = FactComparison()
		fact1 = Fact("Fact 1", "https://ex1.com", "S1", SourceType.ACADEMIC, 95.0)
		fact2 = Fact("Fact 2", "https://ex2.com", "S2", SourceType.NEWS, 50.0)
		
		result = comp.compare_credibility(fact1, fact2)
		assert result["significant_difference"] == True

class TestContradictionDetection:
	def test_identify_contradictions(self):
		comp = FactComparison()
		
		fact1 = Fact("Water boils at 100C at sea level", "https://ex1.com", "High", SourceType.SCIENTIFIC, 95.0)
		fact2 = Fact("Water boils at 100C always", "https://ex2.com", "Low", SourceType.OTHER, 40.0)
		
		contradictions = comp.identify_contradictions([fact1, fact2], similarity_threshold=0.4)
		
		assert len(contradictions) >= 1
	
	def test_no_contradictions_different_topics(self):
		comp = FactComparison()
		
		fact1 = Fact("Water boils at 100C", "https://ex1.com", "S1", SourceType.SCIENTIFIC, 90.0)
		fact2 = Fact("Dogs are mammals", "https://ex2.com", "S2", SourceType.SCIENTIFIC, 90.0)
		
		contradictions = comp.identify_contradictions([fact1, fact2])
		assert len(contradictions) == 0

class TestMergeSuggestions:
	def test_suggest_merging_duplicates(self):
		comp = FactComparison()
		
		fact1 = Fact("Water boils at 100 degrees celsius", "https://ex1.com", "S1", SourceType.SCIENTIFIC, 90.0)
		fact2 = Fact("Water boils at 100 celsius", "https://ex2.com", "S2", SourceType.SCIENTIFIC, 85.0)
		
		suggestions = comp.suggest_merging([fact1, fact2], similarity_threshold=0.7)
		
		assert len(suggestions) >= 1
		assert suggestions[0]["recommended_action"] == "merge"
	
	def test_no_merge_suggestions_different_facts(self):
		comp = FactComparison()
		
		fact1 = Fact("Water boils at 100C", "https://ex1.com", "S1", SourceType.SCIENTIFIC, 90.0)
		fact2 = Fact("Ice melts at 0C", "https://ex2.com", "S2", SourceType.SCIENTIFIC, 90.0)
		
		suggestions = comp.suggest_merging([fact1, fact2])
		assert len(suggestions) == 0

class TestComparisonReport:
	def test_generate_comparison_report(self):
		comp = FactComparison()
		
		target = Fact("Water boils at 100C", "https://target.com", "Target", SourceType.SCIENTIFIC, 90.0)
		related1 = Fact("Water boiling point is 100 degrees", "https://r1.com", "R1", SourceType.ACADEMIC, 95.0)
		related2 = Fact("Dogs are animals", "https://r2.com", "R2", SourceType.NEWS, 80.0)
		
		report = comp.generate_comparison_report(target, [related1, related2])
		
		assert "target_fact" in report
		assert report["target_fact"]["id"] == target.fact_id
		assert "similar_facts_count" in report
		assert "contradictions_found" in report
		assert "merge_suggestions_count" in report
	
	def test_report_includes_top_similar(self):
		comp = FactComparison()
		
		target = Fact("Python programming", "https://target.com", "T", SourceType.NEWS, 80.0)
		related = [
			Fact(f"Python programming language {i}", f"https://r{i}.com", f"R{i}", SourceType.NEWS, 80.0)
			for i in range(10)
		]
		
		report = comp.generate_comparison_report(target, related)
		
		# Should include top 5
		assert len(report["similar_facts"]) <= 5