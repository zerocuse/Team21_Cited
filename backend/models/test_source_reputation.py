import pytest
from datetime import datetime, timedelta
from source_reputation import SourceReputation, SourceReputationManager, VerificationRecord
from fact import SourceType

class TestVerificationRecord:
	def test_valid_record_creation(self):
		record = VerificationRecord("fact123", True)
		assert record.fact_id == "fact123"
		assert record.was_accurate == True
		assert isinstance(record.timestamp, datetime)
	
	def test_empty_fact_id_raises_error(self):
		with pytest.raises(ValueError):
			VerificationRecord("", True)
	
	def test_to_dict(self):
		record = VerificationRecord("fact123", False)
		data = record.to_dict()
		assert data["fact_id"] == "fact123"
		assert data["was_accurate"] == False

class TestSourceReputation:
	def test_initialization(self):
		source = SourceReputation("CNN", "https://cnn.com", SourceType.NEWS)
		assert source.source_name == "CNN"
		assert source.source_url == "https://cnn.com"
		assert source.source_type == SourceType.NEWS
		assert source.reputation_score == 50.0
	
	def test_empty_name_raises_error(self):
		with pytest.raises(ValueError):
			SourceReputation("", "https://example.com", SourceType.NEWS)
	
	def test_add_verification_accurate(self):
		source = SourceReputation("Source", "https://example.com", SourceType.NEWS)
		source.add_verification("fact1", True)
		assert source.verification_count == 1
		assert source.reputation_score == 100.0
	
	def test_add_verification_inaccurate(self):
		source = SourceReputation("Source", "https://example.com", SourceType.NEWS)
		source.add_verification("fact1", False)
		assert source.reputation_score == 0.0
	
	def test_mixed_verifications(self):
		source = SourceReputation("Source", "https://example.com", SourceType.ACADEMIC)
		source.add_verification("fact1", True)
		source.add_verification("fact2", True)
		source.add_verification("fact3", False)
		# 2 accurate out of 3 = 66.67%
		assert 66 <= source.reputation_score <= 67
	
	def test_accuracy_rate(self):
		source = SourceReputation("Source", "https://example.com", SourceType.NEWS)
		source.add_verification("fact1", True)
		source.add_verification("fact2", True)
		source.add_verification("fact3", True)
		source.add_verification("fact4", False)
		assert source.get_accuracy_rate() == 75.0
	
	def test_trend_improving(self):
		source = SourceReputation("Source", "https://example.com", SourceType.NEWS)
		# Add poor early verifications
		for i in range(5):
			source.add_verification(f"fact{i}", False)
		# Add good recent verifications
		for i in range(5, 10):
			source.add_verification(f"fact{i}", True)
		assert source.get_recent_trend() == "improving"
	
	def test_trend_declining(self):
		source = SourceReputation("Source", "https://example.com", SourceType.NEWS)
		# Add good early verifications
		for i in range(5):
			source.add_verification(f"fact{i}", True)
		# Add poor recent verifications
		for i in range(5, 10):
			source.add_verification(f"fact{i}", False)
		assert source.get_recent_trend() == "declining"
	
	def test_is_declining_low_accuracy(self):
		source = SourceReputation("Source", "https://example.com", SourceType.NEWS)
		source.add_verification("fact1", False)
		source.add_verification("fact2", False)
		source.add_verification("fact3", True)
		assert source.is_declining() == True
	
	def test_to_dict(self):
		source = SourceReputation("CNN", "https://cnn.com", SourceType.NEWS)
		source.add_verification("fact1", True)
		data = source.to_dict()
		assert data["source_name"] == "CNN"
		assert data["reputation_score"] == 100.0
		assert data["verification_count"] == 1

class TestSourceReputationManager:
	def test_add_source(self):
		manager = SourceReputationManager()
		source = manager.add_source("CNN", "https://cnn.com", SourceType.NEWS)
		assert source.source_name == "CNN"
		assert manager.get_source_by_url("https://cnn.com") == source
	
	def test_add_duplicate_source_returns_existing(self):
		manager = SourceReputationManager()
		source1 = manager.add_source("CNN", "https://cnn.com", SourceType.NEWS)
		source2 = manager.add_source("CNN", "https://cnn.com", SourceType.NEWS)
		assert source1 is source2
	
	def test_get_source_by_name(self):
		manager = SourceReputationManager()
		manager.add_source("CNN", "https://cnn.com", SourceType.NEWS)
		source = manager.get_source_by_name("CNN")
		assert source.source_url == "https://cnn.com"
	
	def test_get_top_rated_sources(self):
		manager = SourceReputationManager()
		
		source1 = manager.add_source("High", "https://high.com", SourceType.NEWS)
		source1.add_verification("f1", True)
		source1.add_verification("f2", True)
		
		source2 = manager.add_source("Low", "https://low.com", SourceType.NEWS)
		source2.add_verification("f3", False)
		
		top = manager.get_top_rated_sources(limit=2)
		assert top[0].source_name == "High"
		assert top[1].source_name == "Low"
	
	def test_get_top_rated_by_category(self):
		manager = SourceReputationManager()
		manager.add_source("News1", "https://news1.com", SourceType.NEWS)
		manager.add_source("Academic1", "https://academic1.com", SourceType.ACADEMIC)
		
		top_news = manager.get_top_rated_sources(category=SourceType.NEWS)
		assert len(top_news) == 1
		assert top_news[0].source_type == SourceType.NEWS
	
	def test_get_declining_sources(self):
		manager = SourceReputationManager()
		
		good_source = manager.add_source("Good", "https://good.com", SourceType.NEWS)
		good_source.add_verification("f1", True)
		good_source.add_verification("f2", True)
		
		bad_source = manager.add_source("Bad", "https://bad.com", SourceType.NEWS)
		bad_source.add_verification("f3", False)
		bad_source.add_verification("f4", False)
		
		declining = manager.get_declining_sources()
		assert len(declining) == 1
		assert declining[0].source_name == "Bad"