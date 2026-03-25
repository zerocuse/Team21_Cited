import { useEffect, useState } from "react";

function ClaimResults({ claimId }) {
	const [result, setResult] = useState(null);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		if (!claimId) return;
		fetch(`/api/claim/${claimId}/result`)
			.then((res) => res.json())
			.then((data) => {
				setResult(data);
				setLoading(false);
			})
			.catch(() => setLoading(false));
	}, [claimId]);

	if (loading) return <p>Loading results...</p>;
	if (!result || result.error) return <p>No results available.</p>;

	return (
		<div className="claim-results">
			<h3>Fact-Check Results</h3>
			<p>Credibility Score: {result.credibility_score} ({result.credibility_label})</p>
			<p>Source Reputation: {result.source_reputation}</p>
			<p>Contradiction Detected: {result.contradiction_detected ? "Yes" : "No"}</p>
		</div>
	);
}

export default ClaimResults;