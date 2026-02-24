from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid

class SourceType(Enum):
	"""Types of sources for facts."""
	ACADEMIC = "Academic"
	NEWS = "News"
	GOVERNMENT = "Government"
	SCIENTIFIC = "Scientific"
	EXPERT = "Expert"
	ORGANIZATION = "Organization"
	OTHER = "Other"

class Fact:
	"""
	Represents a verified fact with metadata and source information.
	
	Facts include:
	- Fact statement/content
	- Source links and references
	- Metadata (date, source type, credibility)
	- Origin information
	- Related facts
	"""
	
	def __init__(self, statement: str, source_url: str, source_name: str,
				 source_type: SourceType, credibility_score: float):
		"""
		Initialize a Fact.
		
		Args:
			statement: The fact statement/content
			source_url: Primary source URL
			source_name: Name of the source
			source_type: Type of source (SourceType enum)
			credibility_score: Initial credibility score (0-100)
			
		Raises:
			ValueError: If parameters are invalid
		"""
		if not statement or not statement.strip():
			raise ValueError("Fact statement cannot be empty")
		if not source_url or not source_url.strip():
			raise ValueError("Source URL cannot be empty")
		if not source_name or not source_name.strip():
			raise ValueError("Source name cannot be empty")
		if not isinstance(source_type, SourceType):
			raise ValueError("Source type must be a SourceType enum")
		if credibility_score < 0 or credibility_score > 100:
			raise ValueError("Credibility score must be between 0 and 100")
		
		self._fact_id = str(uuid.uuid4())
		self._statement = statement.strip()
		self._source_urls: List[str] = [source_url]
		self._source_name = source_name
		self._source_type = source_type
		self._source_origin = source_name  # Where fact originated
		self._credibility_score = credibility_score
		self._date_added = datetime.now()
		self._last_verified = datetime.now()
		self._related_facts: List[str] = []  # List of related fact IDs
		self._metadata: dict = {
			"source_name": source_name,
			"source_type": source_type.value,
			"origin": source_name
		}
	
	@property
	def fact_id(self) -> str:
		"""Get unique fact ID."""
		return self._fact_id
	
	@property
	def statement(self) -> str:
		"""Get fact statement."""
		return self._statement
	
	@property
	def source_urls(self) -> List[str]:
		"""Get list of source URLs."""
		return self._source_urls.copy()
	
	@property
	def source_name(self) -> str:
		"""Get source name."""
		return self._source_name
	
	@property
	def source_type(self) -> SourceType:
		"""Get source type."""
		return self._source_type
	
	@property
	def source_origin(self) -> str:
		"""Get where the fact originated from."""
		return self._source_origin
	
	@property
	def credibility_score(self) -> float:
		"""Get credibility score."""
		return self._credibility_score
	
	@property
	def date_added(self) -> datetime:
		"""Get date fact was added."""
		return self._date_added
	
	@property
	def last_verified(self) -> datetime:
		"""Get last verification date."""
		return self._last_verified
	
	@property
	def related_facts(self) -> List[str]:
		"""Get list of related fact IDs."""
		return self._related_facts.copy()
	
	@property
	def metadata(self) -> dict:
		"""Get fact metadata."""
		return self._metadata.copy()
	
	def add_source_url(self, url: str):
		"""
		Add an additional source URL.
		
		Args:
			url: Source URL to add
			
		Raises:
			ValueError: If URL is invalid or duplicate
		"""
		if not url or not url.strip():
			raise ValueError("URL cannot be empty")
		if url in self._source_urls:
			raise ValueError("URL already exists")
		self._source_urls.append(url)
	
	def update_credibility_score(self, new_score: float):
		"""
		Update the credibility score.
		
		Args:
			new_score: New credibility score (0-100)
			
		Raises:
			ValueError: If score is invalid
		"""
		if new_score < 0 or new_score > 100:
			raise ValueError("Credibility score must be between 0 and 100")
		self._credibility_score = new_score
		self._last_verified = datetime.now()
	
	def add_related_fact(self, fact_id: str):
		"""
		Add a related fact ID.
		
		Args:
			fact_id: ID of related fact
			
		Raises:
			ValueError: If fact_id is invalid or duplicate
		"""
		if not fact_id or not fact_id.strip():
			raise ValueError("Fact ID cannot be empty")
		if fact_id in self._related_facts:
			raise ValueError("Fact ID already in related facts")
		self._related_facts.append(fact_id)
	
	def update_metadata(self, key: str, value: str):
		"""
		Update or add metadata.
		
		Args:
			key: Metadata key
			value: Metadata value
			
		Raises:
			ValueError: If key or value is invalid
		"""
		if not key or not key.strip():
			raise ValueError("Metadata key cannot be empty")
		if not value or not value.strip():
			raise ValueError("Metadata value cannot be empty")
		self._metadata[key] = value
	
	def mark_verified(self):
		"""Update last verified timestamp to now."""
		self._last_verified = datetime.now()
	
	def to_dict(self) -> dict:
		"""
		Convert fact to dictionary representation.
		
		Returns:
			Dictionary with all fact data
		"""
		return {
			"fact_id": self._fact_id,
			"statement": self._statement,
			"source_urls": self._source_urls,
			"source_name": self._source_name,
			"source_type": self._source_type.value,
			"source_origin": self._source_origin,
			"credibility_score": self._credibility_score,
			"date_added": self._date_added.isoformat(),
			"last_verified": self._last_verified.isoformat(),
			"related_facts": self._related_facts,
			"metadata": self._metadata
		}