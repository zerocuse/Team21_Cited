import pytest
from report import StructuredReport, Source, Verdict

class TestSource:
	def test_valid_source_creation(self):
		source = Source(
			url="https://example.com",
			title="Test Article",
			quote="This is a quote",
			relevance_score=0.8
		)
		assert source.url == "https://example.com"
		assert source.title == "Test Article"
		assert source.relevance_score == 0.8
	
	def test_empty_url_raises_error(self):
		with pytest.raises(ValueError):
			Source(url="", title="Test", quote="Quote")
	
	def test_invalid_relevance_score(self):
		with pytest.raises(ValueError):
			Source(url="https://example.com", title="Test", quote="Quote", relevance_score=1.5)

class TestStructuredReport:
	def test_valid_report_creation(self):
		report = StructuredReport("The sky is blue")
		assert report.claim == "The sky is blue"
	
	def test_empty_claim_raises_error(self):
		with pytest.raises(ValueError):
			StructuredReport("")
	
	def test_set_credibility_score(self):
		report = StructuredReport("Test claim")
		report.set_credibility_score(85.5)
		assert report.credibility_score == 85.5
	
	def test_invalid_credibility_score(self):
		report = StructuredReport("Test claim")
		with pytest.raises(ValueError):
			report.set_credibility_score(150)
	
	def test_add_source(self):
		report = StructuredReport("Test claim")
		report.add_source(
			url="https://example.com",
			title="Test Source",
			quote="Relevant quote",
			relevance_score=0.9
		)
		assert len(report.sources) == 1
		assert report.sources[0].url == "https://example.com"
	
	def test_set_verdict(self):
		report = StructuredReport("Test claim")
		report.set_verdict(Verdict.TRUE)
		assert report.verdict == Verdict.TRUE
	
	def test_validate_sources_with_valid_sources(self):
		report = StructuredReport("Test claim")
		report.add_source("https://example.com", "Title", "Quote")
		assert report.validate_sources() == True
	
	def test_validate_sources_with_no_sources(self):
		report = StructuredReport("Test claim")
		assert report.validate_sources() == False
	
	def test_generate_complete_report(self):
		report = StructuredReport("Test claim")
		report.set_credibility_score(75.0)
		report.set_verdict(Verdict.PARTIALLY_TRUE)
		report.add_source("https://example.com", "Source 1", "Quote 1", 0.8)
		report.add_source("https://example2.com", "Source 2", "Quote 2", 0.6)
		
		result = report.generate_report()
		
		assert result["claim"] == "Test claim"
		assert result["credibility_score"] == 75.0
		assert result["verdict"] == "Partially True"
		assert result["source_count"] == 2
		assert len(result["sources"]) == 2
	
	def test_generate_report_without_score_raises_error(self):
		report = StructuredReport("Test claim")
		report.set_verdict(Verdict.TRUE)
		report.add_source("https://example.com", "Title", "Quote")
		
		with pytest.raises(ValueError):
			report.generate_report()
	
	def test_get_source_links(self):
		report = StructuredReport("Test claim")
		report.add_source("https://example1.com", "Title 1", "Quote 1")
		report.add_source("https://example2.com", "Title 2", "Quote 2")
		
		links = report.get_source_links()
		assert len(links) == 2
		assert "https://example1.com" in links
		assert "https://example2.com" in links
	
	def test_get_quotes(self):
		report = StructuredReport("Test claim")
		report.add_source("https://example.com", "Title", "First quote")
		report.add_source("https://example2.com", "Title 2", "Second quote")
		
		quotes = report.get_quotes()
		assert len(quotes) == 2
		assert "First quote" in quotes
		assert "Second quote" in quotes