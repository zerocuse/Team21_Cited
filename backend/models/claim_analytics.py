from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import Counter

class ClaimRecord:
    """Represents a single submitted claim for analytics."""

    def __init__(self, claim_id: str, user_id: str, claim_text: str,
                 verified: bool, submitted_at: Optional[datetime] = None):
        """
        Initialize a claim record.

        Args:
            claim_id: Unique identifier for the claim
            user_id: ID of user who submitted the claim
            claim_text: Text of the claim
            verified: Whether claim was verified as true
            submitted_at: When claim was submitted (defaults to now)

        Raises:
            ValueError: If claim_id, user_id, or claim_text is empty
        """
        if not claim_id or not claim_id.strip():
            raise ValueError("Claim ID cannot be empty")
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if not claim_text or not claim_text.strip():
            raise ValueError("Claim text cannot be empty")

        self.claim_id = claim_id
        self.user_id = user_id
        self.claim_text = claim_text
        self.verified = verified
        self.submitted_at = submitted_at if submitted_at else datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "claim_id": self.claim_id,
            "user_id": self.user_id,
            "claim_text": self.claim_text,
            "verified": self.verified,
            "submitted_at": self.submitted_at.isoformat()
        }


class ClaimAnalytics:
    """
    Tracks and analyzes patterns in user submitted claims.
    Identifies trending claims, verification success rates,
    and flags users with high false claim submission rates.
    """

    def __init__(self):
        """Initialize analytics with empty claim records."""
        self._claims: List[ClaimRecord] = []

    def add_claim(self, claim: ClaimRecord):
        """
        Add a claim record to analytics.

        Args:
            claim: ClaimRecord to add
        """
        self._claims.append(claim)

    def get_submission_frequency(self, days: int = 7) -> Dict[str, int]:
        """
        Count how many claims were submitted per day over the last N days.

        Args:
            days: Number of days to look back (default 7)

        Returns:
            Dictionary mapping date string to claim count
        """
        cutoff = datetime.now() - timedelta(days=days)
        frequency = {}
        for claim in self._claims:
            if claim.submitted_at >= cutoff:
                date_str = claim.submitted_at.strftime('%Y-%m-%d')
                frequency[date_str] = frequency.get(date_str, 0) + 1
        return frequency

    def get_most_verified_topics(self, limit: int = 5) -> List[Dict]:
        """
        Identify most commonly verified claim topics by keyword frequency.

        Args:
            limit: Number of top topics to return

        Returns:
            List of dictionaries with topic and count
        """
        verified_claims = [c for c in self._claims if c.verified]
        words = []
        for claim in verified_claims:
            words.extend([
                w.lower() for w in claim.claim_text.split()
                if len(w) > 4
            ])
        counter = Counter(words)
        return [{"topic": word, "count": count}
                for word, count in counter.most_common(limit)]

    def get_verification_success_rate(self, user_id: str) -> float:
        """
        Calculate what percentage of a user's claims were verified true.

        Args:
            user_id: ID of user to calculate rate for

        Returns:
            Success rate as percentage (0-100)

        Raises:
            ValueError: If user has no claims
        """
        user_claims = [c for c in self._claims if c.user_id == user_id]
        if not user_claims:
            raise ValueError(f"No claims found for user {user_id}")
        verified = sum(1 for c in user_claims if c.verified)
        return round((verified / len(user_claims)) * 100, 2)

    def get_trending_claims(self, threshold: int = 2) -> List[str]:
        """
        Detect claims submitted by multiple users (trending).

        Args:
            threshold: Minimum number of users for a claim to be trending

        Returns:
            List of trending claim texts
        """
        claim_users: Dict[str, set] = {}
        for claim in self._claims:
            normalized = claim.claim_text.lower().strip()
            if normalized not in claim_users:
                claim_users[normalized] = set()
            claim_users[normalized].add(claim.user_id)

        return [
            claim_text for claim_text, users in claim_users.items()
            if len(users) >= threshold
        ]

    def get_high_false_claim_users(self, threshold: float = 70.0) -> List[str]:
        """
        Identify users whose false claim rate exceeds threshold.

        Args:
            threshold: Percentage of false claims above which user is flagged

        Returns:
            List of user IDs flagged for high false claim rates
        """
        user_ids = set(c.user_id for c in self._claims)
        flagged = []
        for user_id in user_ids:
            try:
                success_rate = self.get_verification_success_rate(user_id)
                false_rate = 100 - success_rate
                if false_rate >= threshold:
                    flagged.append(user_id)
            except ValueError:
                continue
        return flagged

    def generate_analytics_report(self) -> Dict:
        """
        Generate full analytics report with all metrics.

        Returns:
            Dictionary with all analytics data
        """
        return {
            "total_claims": len(self._claims),
            "submission_frequency": self.get_submission_frequency(),
            "most_verified_topics": self.get_most_verified_topics(),
            "trending_claims": self.get_trending_claims(),
            "high_false_claim_users": self.get_high_false_claim_users(),
        }

    def export_as_dict(self) -> Dict:
        """
        Export all claim records as dictionary.

        Returns:
            Dictionary with all claim records
        """
        return {
            "total_claims": len(self._claims),
            "claims": [c.to_dict() for c in self._claims]
        }