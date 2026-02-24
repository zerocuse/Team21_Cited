import pytest
from fact import Fact, SourceType
from datetime import datetime

class TestFactCreation:
	def test_valid_fact_creation(self):
		fact = Fact(
			statement="Water boils at 100°C at sea level",
			source_url="https://example.com/science",
			source_name="Science Journal",
			source_type=SourceType.SCIENTIFIC,
			credibility_score=95.0
		)
		assert fact.statement == "Water boils at 100°C at sea level"
		assert fact.source_name == "Science Journal"
		assert fact.source_type == SourceType.SCIENTIFIC
		assert fact.credibility_score == 95.0
		assert len(fact.fact_id) > 0
	
	def test_empty_statement_raises_error(self):
		with pytest.raises(ValueError):
			Fact("", "https://example.com", "Source", SourceType.NEWS, 80.0)
	
	def test_invalid_credibility_score_raises_error(self):
		with pytest.raises(ValueError):
			Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 150.0)
	
	def test_fact_has_unique_id(self):
		fact1 = Fact("Statement 1", "https://example.com", "Source", SourceType.NEWS, 80.0)
		fact2 = Fact("Statement 2", "https://example.com", "Source", SourceType.NEWS, 80.0)
		assert fact1.fact_id != fact2.fact_id

class TestSourceManagement:
	def test_add_source_url(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		fact.add_source_url("https://example2.com")
		assert len(fact.source_urls) == 2
		assert "https://example2.com" in fact.source_urls
	
	def test_add_duplicate_url_raises_error(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		with pytest.raises(ValueError):
			fact.add_source_url("https://example.com")
	
	def test_source_origin_tracking(self):
		fact = Fact("Statement", "https://example.com", "Science Journal", SourceType.SCIENTIFIC, 90.0)
		assert fact.source_origin == "Science Journal"

class TestCredibilityScoring:
	def test_update_credibility_score(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		fact.update_credibility_score(85.0)
		assert fact.credibility_score == 85.0
	
	def test_update_invalid_score_raises_error(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		with pytest.raises(ValueError):
			fact.update_credibility_score(-10)
	
	def test_update_score_updates_verification_date(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		original_date = fact.last_verified
		fact.update_credibility_score(85.0)
		assert fact.last_verified >= original_date

class TestRelatedFacts:
	def test_add_related_fact(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		fact.add_related_fact("fact-id-123")
		assert "fact-id-123" in fact.related_facts
	
	def test_add_duplicate_related_fact_raises_error(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		fact.add_related_fact("fact-id-123")
		with pytest.raises(ValueError):
			fact.add_related_fact("fact-id-123")

class TestMetadata:
	def test_initial_metadata(self):
		fact = Fact("Statement", "https://example.com", "Science Journal", SourceType.SCIENTIFIC, 90.0)
		metadata = fact.metadata
		assert metadata["source_name"] == "Science Journal"
		assert metadata["source_type"] == "Scientific"
		assert metadata["origin"] == "Science Journal"
	
	def test_update_metadata(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		fact.update_metadata("author", "John Doe")
		assert fact.metadata["author"] == "John Doe"
	
	def test_mark_verified_updates_date(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		original_date = fact.last_verified
		fact.mark_verified()
		assert fact.last_verified >= original_date

class TestSerialization:
	def test_to_dict(self):
		fact = Fact("Statement", "https://example.com", "Source", SourceType.NEWS, 80.0)
		fact_dict = fact.to_dict()
		assert fact_dict["statement"] == "Statement"
		assert fact_dict["credibility_score"] == 80.0
		assert fact_dict["source_type"] == "News"
		assert "fact_id" in fact_dict
		assert "date_added" in fact_dict