import pytest
from datetime import datetime, timedelta
from query_history import QueryHistory, QueryEntry

class TestQueryEntry:
	def test_valid_entry_creation(self):
		entry = QueryEntry("What is AI?")
		assert entry.query_text == "What is AI?"
		assert isinstance(entry.timestamp, datetime)
	
	def test_empty_query_raises_error(self):
		with pytest.raises(ValueError):
			QueryEntry("")
	
	def test_custom_timestamp(self):
		custom_time = datetime(2024, 1, 1, 12, 0)
		entry = QueryEntry("Test", custom_time)
		assert entry.timestamp == custom_time

class TestQueryHistory:
	def test_initialization(self):
		history = QueryHistory("user123")
		assert history.user_id == "user123"
		assert history.query_count == 0
	
	def test_empty_user_id_raises_error(self):
		with pytest.raises(ValueError):
			QueryHistory("")
	
	def test_add_query(self):
		history = QueryHistory("user123")
		history.add_query("What is Python?")
		assert history.query_count == 1
	
	def test_add_multiple_queries(self):
		history = QueryHistory("user123")
		history.add_query("Query 1")
		history.add_query("Query 2")
		history.add_query("Query 3")
		assert history.query_count == 3

class TestDateRangeFiltering:
	def test_get_queries_by_date_range(self):
		history = QueryHistory("user123")
		now = datetime.now()
		yesterday = now - timedelta(days=1)
		
		history.add_query("Query today", now)
		history.add_query("Query yesterday", yesterday)
		
		results = history.get_queries_by_date_range(yesterday, now)
		assert len(results) == 2
	
	def test_invalid_date_range_raises_error(self):
		history = QueryHistory("user123")
		start = datetime.now()
		end = start - timedelta(days=1)
		
		with pytest.raises(ValueError):
			history.get_queries_by_date_range(start, end)

class TestKeywordSearch:
	def test_search_queries_by_keyword(self):
		history = QueryHistory("user123")
		history.add_query("What is Python?")
		history.add_query("How does Python work?")
		history.add_query("What is Java?")
		
		results = history.search_queries_by_keyword("Python")
		assert len(results) == 2
	
	def test_search_case_insensitive(self):
		history = QueryHistory("user123")
		history.add_query("What is PYTHON?")
		
		results = history.search_queries_by_keyword("python")
		assert len(results) == 1
	
	def test_search_empty_keyword_raises_error(self):
		history = QueryHistory("user123")
		with pytest.raises(ValueError):
			history.search_queries_by_keyword("")

class TestFrequencyAnalysis:
	def test_get_most_frequent_queries(self):
		history = QueryHistory("user123")
		history.add_query("What is AI?")
		history.add_query("What is AI?")
		history.add_query("What is ML?")
		
		results = history.get_most_frequent_queries(2)
		assert results[0][0] == "What is AI?"
		assert results[0][1] == 2
	
	def test_frequency_with_limit(self):
		history = QueryHistory("user123")
		for i in range(5):
			history.add_query(f"Query {i}")
		
		results = history.get_most_frequent_queries(3)
		assert len(results) == 3
	
	def test_invalid_limit_raises_error(self):
		history = QueryHistory("user123")
		with pytest.raises(ValueError):
			history.get_most_frequent_queries(0)

class TestHistoryClearing:
	def test_clear_history(self):
		history = QueryHistory("user123")
		history.add_query("Query 1")
		history.add_query("Query 2")
		
		history.clear_history()
		assert history.query_count == 0
	
	def test_clear_before_date(self):
		history = QueryHistory("user123")
		now = datetime.now()
		old = now - timedelta(days=10)
		
		history.add_query("Old query", old)
		history.add_query("New query", now)
		
		cutoff = now - timedelta(days=5)
		history.clear_history_before_date(cutoff)
		
		assert history.query_count == 1

class TestRecentQueries:
	def test_get_recent_queries(self):
		history = QueryHistory("user123")
		for i in range(20):
			history.add_query(f"Query {i}")
		
		recent = history.get_recent_queries(5)
		assert len(recent) == 5
	
	def test_recent_queries_ordered(self):
		history = QueryHistory("user123")
		history.add_query("First")
		history.add_query("Second")
		history.add_query("Third")
		
		recent = history.get_recent_queries(3)
		assert recent[0].query_text == "Third"
		assert recent[2].query_text == "First"

class TestImportExport:
	def test_export_to_list(self):
		history = QueryHistory("user123")
		history.add_query("Query 1")
		history.add_query("Query 2")
		
		exported = history.export_to_list()
		assert exported == ["Query 1", "Query 2"]
	
	def test_import_from_list(self):
		history = QueryHistory("user123")
		queries = ["Query 1", "Query 2", "Query 3"]
		
		history.import_from_list(queries)
		assert history.query_count == 3

class TestStatistics:
	def test_statistics_empty_history(self):
		history = QueryHistory("user123")
		stats = history.get_statistics()
		
		assert stats["total_queries"] == 0
		assert stats["unique_queries"] == 0
	
	def test_statistics_with_queries(self):
		history = QueryHistory("user123")
		history.add_query("Query 1")
		history.add_query("Query 1")
		history.add_query("Query 2")
		
		stats = history.get_statistics()
		assert stats["total_queries"] == 3
		assert stats["unique_queries"] == 2
