from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class Verdict(Enum):
	"""Enumeration of possible verdicts for claim analysis."""
	TRUE = "True"
	FALSE = "False"
	PARTIALLY_TRUE = "Partially True"
	UNVERIFIED = "Unverified"
	INSUFFICIENT_DATA = "Insufficient Data"
	
@dataclass
class Source:
	"""Represents a source used in the report."""
	url: str
	title: str
	quote: str
	relevance_score: float = 0.0
	
	def __post_init__(self):
		if not self.url or not self.url.strip():
			raise ValueError("Source URL cannot be empty")
		if not self.title or not self.title.strip():
			raise ValueError("Source title cannot be empty")
		if self.relevance_score < 0 or self.relevance_score > 1:
			raise ValueError("Relevance score must be between 0 and 1")

class StructuredReport:
	"""
	Generates structured reports for fact-checking claims.
	
	A report includes:
	- Credibility score
	- Source validation
	- Relevant quotes
	- Source links
	- Final verdict
	"""
	
	def __init__(self, claim: str):
		"""
		Initialize report generator with a claim to analyze.
		
		Args:
			claim: The user's input claim to fact-check
			
		Raises:
			ValueError: If claim is None or empty
		"""
		if not claim or not claim.strip():
			raise ValueError("Claim cannot be null or empty")
		
		self._claim = claim.strip()
		self._credibility_score: Optional[float] = None
		self._sources: List[Source] = []
		self._verdict: Optional[Verdict] = None
		self._analysis_notes: str = ""
	
	@property
	def claim(self) -> str:
		"""Get the claim being analyzed."""
		return self._claim
	
	@property
	def credibility_score(self) -> Optional[float]:
		"""Get the credibility score (0-100)."""
		return self._credibility_score
	
	@property
	def sources(self) -> List[Source]:
		"""Get list of sources used in analysis."""
		return self._sources.copy()
	
	@property
	def verdict(self) -> Optional[Verdict]:
		"""Get the final verdict."""
		return self._verdict
	
	def set_credibility_score(self, score: float):
		"""
		Set the credibility score for the claim.
		
		Args:
			score: Credibility score between 0 and 100
			
		Raises:
			ValueError: If score is outside valid range
		"""
		if score < 0 or score > 100:
			raise ValueError("Credibility score must be between 0 and 100")
		self._credibility_score = score
	
	def add_source(self, url: str, title: str, quote: str, relevance_score: float = 0.0):
		"""
		Add a source to the report.
		
		Args:
			url: URL of the source
			title: Title of the source
			quote: Relevant quote from the source
			relevance_score: How relevant this source is (0-1)
			
		Raises:
			ValueError: If source data is invalid
		"""
		source = Source(url=url, title=title, quote=quote, relevance_score=relevance_score)
		self._sources.append(source)
	
	def set_verdict(self, verdict: Verdict):
		"""
		Set the final verdict for the claim.
		
		Args:
			verdict: The verdict enumeration value
		"""
		if not isinstance(verdict, Verdict):
			raise ValueError("Verdict must be a Verdict enum value")
		self._verdict = verdict
	
	def set_analysis_notes(self, notes: str):
		"""
		Set additional analysis notes.
		
		Args:
			notes: Explanatory notes about the analysis
		"""
		self._analysis_notes = notes
	
	def validate_sources(self) -> bool:
		"""
		Validate that all sources meet minimum requirements.
		
		Returns:
			True if all sources are valid, False otherwise
		"""
		if not self._sources:
			return False
		
		for source in self._sources:
			if not source.url or not source.title or not source.quote:
				return False
		
		return True
	
	def generate_report(self) -> Dict:
		"""
		Generate the structured report as a dictionary.
		
		Returns:
			Dictionary containing all report components
			
		Raises:
			ValueError: If required fields are missing
		"""
		if self._credibility_score is None:
			raise ValueError("Cannot generate report: credibility score not set")
		if self._verdict is None:
			raise ValueError("Cannot generate report: verdict not set")
		if not self._sources:
			raise ValueError("Cannot generate report: no sources provided")
		
		return {
			"claim": self._claim,
			"credibility_score": self._credibility_score,
			"verdict": self._verdict.value,
			"sources": [
				{
					"url": source.url,
					"title": source.title,
					"quote": source.quote,
					"relevance_score": source.relevance_score
				}
				for source in self._sources
			],
			"source_count": len(self._sources),
			"sources_validated": self.validate_sources(),
			"analysis_notes": self._analysis_notes
		}
	
	def get_source_links(self) -> List[str]:
		"""
		Get list of all source URLs used in the report.
		
		Returns:
			List of source URLs
		"""
		return [source.url for source in self._sources]
	
	def get_quotes(self) -> List[str]:
		"""
		Get all quotes from sources.
		
		Returns:
			List of quotes related to the claim
		"""
		return [source.quote for source in self._sources]