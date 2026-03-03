from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import Counter

class QueryEntry:
	"""Represents a single query with metadata."""
	
	def __init__(self, query_text: str, timestamp: Optional[datetime] = None):
		"""
		Initialize a query entry.
		
		Args:
			query_text: The query string
			timestamp: When query was made (defaults to now)
			
		Raises:
			ValueError: If query_text is empty
		"""
		if not query_text or not query_text.strip():
			raise ValueError("Query text cannot be empty")
		
		self.query_text = query_text.strip()
		self.timestamp = timestamp if timestamp else datetime.now()
	
	def to_dict(self) -> Dict:
		"""Convert to dictionary."""
		return {
			"query": self.query_text,
			"timestamp": self.timestamp.isoformat()
		}


class QueryHistory:
	"""
	Manages user query history with search, filter, and analysis capabilities.
	
	Works with User class previous_queries field to provide advanced
	query management functionality.
	"""
	
	def __init__(self, user_id: str):
		"""
		Initialize query history manager.
		
		Args:
			user_id: ID of the user this history belongs to
			
		Raises:
			ValueError: If user_id is empty
		"""
		if not user_id or not user_id.strip():
			raise ValueError("User ID cannot be empty")
		
		self._user_id = user_id
		self._queries: List[QueryEntry] = []
	
	@property
	def user_id(self) -> str:
		"""Get user ID."""
		return self._user_id
	
	@property
	def query_count(self) -> int:
		"""Get total number of queries."""
		return len(self._queries)
	
	def add_query(self, query_text: str, timestamp: Optional[datetime] = None):
		"""
		Add a query to history.
		
		Args:
			query_text: The query string
			timestamp: When query was made (defaults to now)
			
		Raises:
			ValueError: If query_text is empty
		"""
		entry = QueryEntry(query_text, timestamp)
		self._queries.append(entry)
	
	def get_queries_by_date_range(self, start_date: datetime, 
								   end_date: datetime) -> List[QueryEntry]:
		"""
		Retrieve queries within a date range.
		
		Args:
			start_date: Start of date range (inclusive)
			end_date: End of date range (inclusive)
			
		Returns:
			List of QueryEntry objects in range
			
		Raises:
			ValueError: If start_date is after end_date
		"""
		if start_date > end_date:
			raise ValueError("Start date must be before or equal to end date")
		
		return [
			q for q in self._queries
			if start_date <= q.timestamp <= end_date
		]
	
	def search_queries_by_keyword(self, keyword: str) -> List[QueryEntry]:
		"""
		Search queries containing a keyword (case-insensitive).
		
		Args:
			keyword: Keyword to search for
			
		Returns:
			List of QueryEntry objects containing keyword
			
		Raises:
			ValueError: If keyword is empty
		"""
		if not keyword or not keyword.strip():
			raise ValueError("Keyword cannot be empty")
		
		keyword_lower = keyword.lower()
		return [
			q for q in self._queries
			if keyword_lower in q.query_text.lower()
		]
	
	def get_most_frequent_queries(self, limit: int = 10) -> List[tuple]:
		"""
		Get most frequently asked queries.
		
		Args:
			limit: Maximum number of results to return
			
		Returns:
			List of (query_text, count) tuples, sorted by frequency
			
		Raises:
			ValueError: If limit is less than 1
		"""
		if limit < 1:
			raise ValueError("Limit must be at least 1")
		
		query_texts = [q.query_text for q in self._queries]
		counter = Counter(query_texts)
		return counter.most_common(limit)
	
	def clear_history(self):
		"""Clear all query history."""
		self._queries.clear()
	
	def clear_history_before_date(self, cutoff_date: datetime):
		"""
		Clear queries before a specific date.
		
		Args:
			cutoff_date: Delete queries before this date
		"""
		self._queries = [
			q for q in self._queries
			if q.timestamp >= cutoff_date
		]
	
	def get_recent_queries(self, count: int = 10) -> List[QueryEntry]:
		"""
		Get most recent queries.
		
		Args:
			count: Number of recent queries to return
			
		Returns:
			List of most recent QueryEntry objects
			
		Raises:
			ValueError: If count is less than 1
		"""
		if count < 1:
			raise ValueError("Count must be at least 1")
		
		# Sort by timestamp descending, take first 'count'
		sorted_queries = sorted(self._queries, key=lambda q: q.timestamp, reverse=True)
		return sorted_queries[:count]
	
	def get_queries_today(self) -> List[QueryEntry]:
		"""Get all queries from today."""
		today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
		today_end = datetime.now()
		return self.get_queries_by_date_range(today_start, today_end)
	
	def get_queries_this_week(self) -> List[QueryEntry]:
		"""Get all queries from the past 7 days."""
		week_ago = datetime.now() - timedelta(days=7)
		return self.get_queries_by_date_range(week_ago, datetime.now())
	
	def export_to_list(self) -> List[str]:
		"""
		Export all queries as simple string list (for User.previous_queries).
		
		Returns:
			List of query strings
		"""
		return [q.query_text for q in self._queries]
	
	def import_from_list(self, query_list: List[str]):
		"""
		Import queries from a list of strings (from User.previous_queries).
		
		Args:
			query_list: List of query strings
		"""
		for query in query_list:
			if query and query.strip():
				self.add_query(query)
	
	def get_statistics(self) -> Dict:
		"""
		Get query history statistics.
		
		Returns:
			Dictionary with statistics
		"""
		if not self._queries:
			return {
				"total_queries": 0,
				"unique_queries": 0,
				"queries_today": 0,
				"queries_this_week": 0,
				"most_common_query": None
			}
		
		unique = len(set(q.query_text for q in self._queries))
		most_common = self.get_most_frequent_queries(1)
		
		return {
			"total_queries": len(self._queries),
			"unique_queries": unique,
			"queries_today": len(self.get_queries_today()),
			"queries_this_week": len(self.get_queries_this_week()),
			"most_common_query": most_common[0] if most_common else None
		}


