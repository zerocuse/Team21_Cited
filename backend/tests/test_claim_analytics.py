import pytest
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'models'))
from claim_analytics import ClaimAnalytics, ClaimRecord

def make_claim(claim_id, user_id, text, verified, days_ago=0):
    return ClaimRecord(
        claim_id=claim_id,
        user_id=user_id,
        claim_text=text,
        verified=verified,
        submitted_at=datetime.now() - timedelta(days=days_ago)
    )

class TestClaimRecord:

    def test_valid_creation(self):
        record = ClaimRecord("c1", "u1", "The earth is round", True)
        assert record.claim_id == "c1"
        assert record.verified == True

    def test_empty_claim_id_raises(self):
        with pytest.raises(ValueError):
            ClaimRecord("", "u1", "some claim", True)

    def test_empty_user_id_raises(self):
        with pytest.raises(ValueError):
            ClaimRecord("c1", "", "some claim", True)

    def test_empty_text_raises(self):
        with pytest.raises(ValueError):
            ClaimRecord("c1", "u1", "", True)

    def test_to_dict(self):
        record = ClaimRecord("c1", "u1", "some claim", False)
        data = record.to_dict()
        assert data['claim_id'] == "c1"
        assert data['verified'] == False

class TestClaimAnalytics:

    def test_empty_analytics(self):
        analytics = ClaimAnalytics()
        report = analytics.generate_analytics_report()
        assert report['total_claims'] == 0

    def test_add_claim(self):
        analytics = ClaimAnalytics()
        analytics.add_claim(make_claim("c1", "u1", "some claim", True))
        assert len(analytics._claims) == 1

    def test_submission_frequency(self):
        analytics = ClaimAnalytics()
        analytics.add_claim(make_claim("c1", "u1", "claim one", True, days_ago=0))
        analytics.add_claim(make_claim("c2", "u2", "claim two", False, days_ago=0))
        freq = analytics.get_submission_frequency()
        today = datetime.now().strftime('%Y-%m-%d')
        assert freq[today] == 2

    def test_verification_success_rate(self):
        analytics = ClaimAnalytics()
        analytics.add_claim(make_claim("c1", "u1", "claim one", True))
        analytics.add_claim(make_claim("c2", "u1", "claim two", False))
        rate = analytics.get_verification_success_rate("u1")
        assert rate == 50.0

    def test_no_claims_for_user_raises(self):
        analytics = ClaimAnalytics()
        with pytest.raises(ValueError):
            analytics.get_verification_success_rate("unknown_user")

    def test_trending_claims(self):
        analytics = ClaimAnalytics()
        analytics.add_claim(make_claim("c1", "u1", "the earth is flat", False))
        analytics.add_claim(make_claim("c2", "u2", "the earth is flat", False))
        trending = analytics.get_trending_claims(threshold=2)
        assert "the earth is flat" in trending

    def test_high_false_claim_users(self):
        analytics = ClaimAnalytics()
        analytics.add_claim(make_claim("c1", "u1", "claim one", False))
        analytics.add_claim(make_claim("c2", "u1", "claim two", False))
        flagged = analytics.get_high_false_claim_users(threshold=70.0)
        assert "u1" in flagged

    def test_export_as_dict(self):
        analytics = ClaimAnalytics()
        analytics.add_claim(make_claim("c1", "u1", "some claim", True))
        exported = analytics.export_as_dict()
        assert exported['total_claims'] == 1
        assert len(exported['claims']) == 1

    def test_most_verified_topics(self):
        analytics = ClaimAnalytics()
        analytics.add_claim(make_claim("c1", "u1", "climate change is real", True))
        analytics.add_claim(make_claim("c2", "u2", "climate change affects everyone", True))
        topics = analytics.get_most_verified_topics(limit=1)
        assert topics[0]['topic'] == 'climate'