import pytest
from unittest.mock import MagicMock, patch, call
from services.claim_service import (
    create_source,
    link_source_to_claim,
    add_citation,
    get_sources_for_claim,
    search_sources_by_keyword
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db(monkeypatch):
    """Patch db.session so no real database is needed."""
    mock_session = MagicMock()
    mock_or = MagicMock()

    import service_sources
    monkeypatch.setattr(service_sources.db, "session", mock_session)
    monkeypatch.setattr(service_sources.db, "or_", mock_or)
    return mock_session


def make_source(source_id=1, title="BBC News", url="https://bbc.com"):
    source = MagicMock()
    source.sourceID = source_id
    source.title = title
    source.url = url
    source.source_type = "unknown"
    return source


def make_claim(claim_id=1):
    claim = MagicMock()
    claim.claimID = claim_id
    claim.sources = []
    return claim


# ---------------------------------------------------------------------------
# create_source
# ---------------------------------------------------------------------------

class TestCreateSource:

    def test_creates_source_successfully(self, mock_db):
        result = create_source("BBC News", "https://bbc.com")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_returns_source_object(self, mock_db):
        result = create_source("BBC News", "https://bbc.com")
        assert result is not None

    def test_sets_default_source_type_to_unknown(self, mock_db):
        with patch("service_sources.Source") as MockSource:
            mock_instance = MagicMock()
            MockSource.return_value = mock_instance
            create_source("BBC News", "https://bbc.com")
            MockSource.assert_called_once_with(
                title="BBC News",
                url="https://bbc.com",
                source_type="unknown"
            )

    def test_raises_if_source_name_empty(self, mock_db):
        with pytest.raises(ValueError, match="Source name cannot be null or empty"):
            create_source("", "https://bbc.com")

    def test_raises_if_source_name_whitespace(self, mock_db):
        with pytest.raises(ValueError, match="Source name cannot be null or empty"):
            create_source("   ", "https://bbc.com")

    def test_raises_if_source_name_none(self, mock_db):
        with pytest.raises(ValueError, match="Source name cannot be null or empty"):
            create_source(None, "https://bbc.com")

    def test_raises_if_source_url_empty(self, mock_db):
        with pytest.raises(ValueError, match="Source URL cannot be null or empty"):
            create_source("BBC News", "")

    def test_raises_if_source_url_whitespace(self, mock_db):
        with pytest.raises(ValueError, match="Source URL cannot be null or empty"):
            create_source("BBC News", "   ")

    def test_raises_if_source_url_none(self, mock_db):
        with pytest.raises(ValueError, match="Source URL cannot be null or empty"):
            create_source("BBC News", None)


# ---------------------------------------------------------------------------
# link_source_to_claim
# ---------------------------------------------------------------------------

class TestLinkSourceToClaim:

    def test_links_source_to_claim_successfully(self, mock_db, monkeypatch):
        mock_source = make_source()
        mock_claim = make_claim()

        import service_sources
        monkeypatch.setattr(service_sources.Source.query, "get", lambda x: mock_source)
        monkeypatch.setattr(service_sources.Claim.query, "get", lambda x: mock_claim)

        link_source_to_claim(1, 1)

        assert mock_source in mock_claim.sources
        mock_db.commit.assert_called_once()

    def test_raises_if_source_not_found(self, mock_db, monkeypatch):
        import service_sources
        monkeypatch.setattr(service_sources.Source.query, "get", lambda x: None)

        with pytest.raises(ValueError, match="Source with ID 99 does not exist"):
            link_source_to_claim(99, 1)

    def test_raises_if_claim_not_found(self, mock_db, monkeypatch):
        mock_source = make_source()

        import service_sources
        monkeypatch.setattr(service_sources.Source.query, "get", lambda x: mock_source)
        monkeypatch.setattr(service_sources.Claim.query, "get", lambda x: None)

        with pytest.raises(ValueError, match="Claim with ID 99 does not exist"):
            link_source_to_claim(1, 99)


# ---------------------------------------------------------------------------
# add_citation
# ---------------------------------------------------------------------------

class TestAddCitation:

    def test_creates_citation_successfully(self, mock_db, monkeypatch):
        mock_source = make_source()
        mock_claim = make_claim()

        import service_sources
        monkeypatch.setattr(service_sources.Source.query, "get", lambda x: mock_source)
        monkeypatch.setattr(service_sources.Claim.query, "get", lambda x: mock_claim)

        with patch("service_sources.Citation") as MockCitation:
            mock_citation = MagicMock()
            MockCitation.return_value = mock_citation

            result = add_citation(1, 1, info_used="Key statistic on page 4")

            MockCitation.assert_called_once_with(claimID=1, sourceID=1, info_used="Key statistic on page 4")
            mock_db.add.assert_called_once_with(mock_citation)
            mock_db.commit.assert_called_once()
            assert result == mock_citation

    def test_info_used_is_optional(self, mock_db, monkeypatch):
        mock_source = make_source()
        mock_claim = make_claim()

        import service_sources
        monkeypatch.setattr(service_sources.Source.query, "get", lambda x: mock_source)
        monkeypatch.setattr(service_sources.Claim.query, "get", lambda x: mock_claim)

        with patch("service_sources.Citation") as MockCitation:
            MockCitation.return_value = MagicMock()
            add_citation(1, 1)  # no info_used passed
            MockCitation.assert_called_once_with(claimID=1, sourceID=1, info_used=None)

    def test_raises_if_source_not_found(self, mock_db, monkeypatch):
        import service_sources
        monkeypatch.setattr(service_sources.Source.query, "get", lambda x: None)

        with pytest.raises(ValueError, match="Source with ID 99 does not exist"):
            add_citation(1, 99)

    def test_raises_if_claim_not_found(self, mock_db, monkeypatch):
        mock_source = make_source()

        import service_sources
        monkeypatch.setattr(service_sources.Source.query, "get", lambda x: mock_source)
        monkeypatch.setattr(service_sources.Claim.query, "get", lambda x: None)

        with pytest.raises(ValueError, match="Claim with ID 99 does not exist"):
            add_citation(99, 1)


# ---------------------------------------------------------------------------
# get_sources_for_claim
# ---------------------------------------------------------------------------

class TestGetSourcesForClaim:

    def test_returns_sources_for_valid_claim(self, mock_db, monkeypatch):
        mock_source = make_source()
        mock_claim = make_claim()
        mock_claim.sources = [mock_source]

        import service_sources
        monkeypatch.setattr(service_sources.Claim.query, "get", lambda x: mock_claim)

        result = get_sources_for_claim(1)
        assert result == [mock_source]

    def test_returns_empty_list_if_no_sources(self, mock_db, monkeypatch):
        mock_claim = make_claim()
        mock_claim.sources = []

        import service_sources
        monkeypatch.setattr(service_sources.Claim.query, "get", lambda x: mock_claim)

        result = get_sources_for_claim(1)
        assert result == []

    def test_raises_if_claim_not_found(self, mock_db, monkeypatch):
        import service_sources
        monkeypatch.setattr(service_sources.Claim.query, "get", lambda x: None)

        with pytest.raises(ValueError, match="Claim with ID 99 does not exist"):
            get_sources_for_claim(99)


# ---------------------------------------------------------------------------
# search_sources_by_keyword
# ---------------------------------------------------------------------------

class TestSearchSourcesByKeyword:

    def test_returns_matching_sources(self, mock_db, monkeypatch):
        mock_source = make_source(title="BBC News Science")

        import service_sources
        mock_filter = MagicMock()
        mock_filter.all.return_value = [mock_source]
        monkeypatch.setattr(service_sources.Source.query, "filter", lambda *a: mock_filter)

        result = search_sources_by_keyword("BBC")
        assert result == [mock_source]

    def test_returns_empty_list_if_no_match(self, mock_db, monkeypatch):
        import service_sources
        mock_filter = MagicMock()
        mock_filter.all.return_value = []
        monkeypatch.setattr(service_sources.Source.query, "filter", lambda *a: mock_filter)

        result = search_sources_by_keyword("zzznomatch")
        assert result == []

    def test_raises_if_keyword_empty(self, mock_db):
        with pytest.raises(ValueError, match="Keyword cannot be null or empty"):
            search_sources_by_keyword("")

    def test_raises_if_keyword_whitespace(self, mock_db):
        with pytest.raises(ValueError, match="Keyword cannot be null or empty"):
            search_sources_by_keyword("   ")

    def test_raises_if_keyword_none(self, mock_db):
        with pytest.raises(ValueError, match="Keyword cannot be null or empty"):
            search_sources_by_keyword(None)