from typing import List, Dict, Optional
from datetime import datetime
from fact import SourceType

class VerificationRecord:
	"""Represents a single fact verification for a source."""
	
	def __init__(self, fact_id: str, was_accurate: bool, timestamp: Optional[datetime] = None):
		"""
		Initialize verification record.
		
		Args:
			fact_id: ID of the fact that was verified
			was_accurate: Whether the fact was verified as accurate
			timestamp: When verification occurred (defaults to now)
			
		Raises:
			ValueError: If fact_id is empty
		"""
		if not fact_id or not fact_id.strip():
			raise ValueError("Fact ID cannot be empty")
		
		self.fact_id = fact_id
		self.was_accurate = was_accurate
		self.timestamp = timestamp if timestamp else datetime.now()
	
	def to_dict(self) -> Dict:
		"""Convert to dictionary."""
		return {
			"fact_id": self.fact_id,
			"was_accurate": self.was_accurate,
			"timestamp": self.timestamp.isoformat()
		}


class SourceReputation:
	"""
	Tracks historical accuracy and reputation of sources over time.
	
	Maintains reputation scores based on verification history:
	- Accurate facts increase reputation
	- Inaccurate facts decrease reputation
	- Recent verifications weighted more heavily than old ones
	"""
	
	def __init__(self, source_name: str, source_url: str, source_type: SourceType):
		"""
		Initialize source reputation tracker.
		
		Args:
			source_name: Name of the source
			source_url: Primary URL of the source
			source_type: Type of source (SourceType enum)
			
		Raises:
			ValueError: If parameters are invalid
		"""
		if not source_name or not source_name.strip():
			raise ValueError("Source name cannot be empty")
		if not source_url or not source_url.strip():
			raise ValueError("Source URL cannot be empty")
		if not isinstance(source_type, SourceType):
			raise ValueError("Source type must be a SourceType enum")
		
		self._source_name = source_name
		self._source_url = source_url
		self._source_type = source_type
		self._verification_history: List[VerificationRecord] = []
		self._reputation_score: float = 50.0  # Start at neutral 50/100
	
	@property
	def source_name(self) -> str:
		"""Get source name."""
		return self._source_name
	
	@property
	def source_url(self) -> str:
		"""Get source URL."""
		return self._source_url
	
	@property
	def source_type(self) -> SourceType:
		"""Get source type."""
		return self._source_type
	
	@property
	def reputation_score(self) -> float:
		"""Get current reputation score (0-100)."""
		return self._reputation_score
	
	@property
	def verification_count(self) -> int:
		"""Get total number of verifications."""
		return len(self._verification_history)
	
	def add_verification(self, fact_id: str, was_accurate: bool):
		"""
		Add a new fact verification and update reputation.
		
		Args:
			fact_id: ID of the verified fact
			was_accurate: Whether the fact was accurate
			
		Raises:
			ValueError: If fact_id is empty
		"""
		record = VerificationRecord(fact_id, was_accurate)
		self._verification_history.append(record)
		self._update_reputation_score()
	
	def _update_reputation_score(self):
		"""Recalculate reputation score based on verification history."""
		if not self._verification_history:
			self._reputation_score = 50.0
			return
		
		# Calculate accuracy rate
		accurate_count = sum(1 for v in self._verification_history if v.was_accurate)
		total_count = len(self._verification_history)
		accuracy_rate = accurate_count / total_count
		
		# Convert to 0-100 scale
		# 100% accurate = 100 score
		# 0% accurate = 0 score
		self._reputation_score = round(accuracy_rate * 100, 2)
	
	def get_accuracy_rate(self) -> float:
		"""
		Get percentage of facts that were accurate.
		
		Returns:
			Accuracy rate as percentage (0-100)
		"""
		if not self._verification_history:
			return 0.0
		
		accurate = sum(1 for v in self._verification_history if v.was_accurate)
		return round((accurate / len(self._verification_history)) * 100, 2)
	
	def get_recent_trend(self, last_n: int = 10) -> str:
		"""
		Analyze reputation trend from recent verifications.
		
		Args:
			last_n: Number of recent verifications to analyze
			
		Returns:
			Trend description: "improving", "declining", or "stable"
		"""
		if len(self._verification_history) < 2:
			return "stable"
		
		recent = self._verification_history[-last_n:]
		if len(recent) < 2:
			return "stable"
		
		# Compare first half vs second half of recent verifications
		mid = len(recent) // 2
		first_half_accuracy = sum(1 for v in recent[:mid] if v.was_accurate) / mid
		second_half_accuracy = sum(1 for v in recent[mid:] if v.was_accurate) / (len(recent) - mid)
		
		if second_half_accuracy > first_half_accuracy + 0.1:
			return "improving"
		elif second_half_accuracy < first_half_accuracy - 0.1:
			return "declining"
		else:
			return "stable"
	
	def is_declining(self, threshold: float = 0.6) -> bool:
		"""
		Check if source reputation is declining.
		
		Args:
			threshold: Accuracy threshold below which source is flagged
			
		Returns:
			True if accuracy below threshold or trend is declining
		"""
		accuracy = self.get_accuracy_rate() / 100
		trend = self.get_recent_trend()
		
		return accuracy < threshold or trend == "declining"
	
	def get_verification_history(self) -> List[Dict]:
		"""
		Get all verification records.
		
		Returns:
			List of verification record dictionaries
		"""
		return [v.to_dict() for v in self._verification_history]
	
	def to_dict(self) -> Dict:
		"""
		Export source reputation data.
		
		Returns:
			Dictionary with all reputation data
		"""
		return {
			"source_name": self._source_name,
			"source_url": self._source_url,
			"source_type": self._source_type.value,
			"reputation_score": self._reputation_score,
			"verification_count": len(self._verification_history),
			"accuracy_rate": self.get_accuracy_rate(),
			"recent_trend": self.get_recent_trend(),
			"is_declining": self.is_declining(),
			"verification_history": self.get_verification_history()
		}


class SourceReputationManager:
	"""Manages reputation tracking for multiple sources."""
	
	def __init__(self):
		"""Initialize reputation manager."""
		self._sources: Dict[str, SourceReputation] = {}
	
	def add_source(self, source_name: str, source_url: str, source_type: SourceType) -> SourceReputation:
		"""
		Add a new source to track or return existing.
		
		Args:
			source_name: Name of source
			source_url: URL of source
			source_type: Type of source
			
		Returns:
			SourceReputation object for this source
		"""
		if source_url not in self._sources:
			self._sources[source_url] = SourceReputation(source_name, source_url, source_type)
		return self._sources[source_url]
	
	def get_source_by_url(self, source_url: str) -> Optional[SourceReputation]:
		"""
		Retrieve source reputation by URL.
		
		Args:
			source_url: URL of source
			
		Returns:
			SourceReputation object or None if not found
		"""
		return self._sources.get(source_url)
	
	def get_source_by_name(self, source_name: str) -> Optional[SourceReputation]:
		"""
		Retrieve source reputation by name.
		
		Args:
			source_name: Name of source
			
		Returns:
			SourceReputation object or None if not found
		"""
		for source in self._sources.values():
			if source.source_name == source_name:
				return source
		return None
	
	def get_top_rated_sources(self, category: Optional[SourceType] = None, limit: int = 10) -> List[SourceReputation]:
		"""
		Get highest reputation sources, optionally filtered by category.
		
		Args:
			category: Optional SourceType to filter by
			limit: Maximum number of sources to return
			
		Returns:
			List of SourceReputation objects sorted by reputation
		"""
		sources = list(self._sources.values())
		
		if category:
			sources = [s for s in sources if s.source_type == category]
		
		sources.sort(key=lambda s: s.reputation_score, reverse=True)
		return sources[:limit]
	
	def get_declining_sources(self) -> List[SourceReputation]:
		"""
		Get all sources with declining reputation.
		
		Returns:
			List of SourceReputation objects flagged as declining
		"""
		return [s for s in self._sources.values() if s.is_declining()]
	
	def get_all_sources(self) -> List[SourceReputation]:
		"""Get all tracked sources."""
		return list(self._sources.values())