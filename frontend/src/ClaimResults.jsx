import { useEffect, useState } from "react";

function ClaimResults({ claimId }) {
	const [result, setResult] = useState(null);
	const [diversity, setDiversity] = useState(null);
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
			fetch(`/api/claim/${claimId}/diversity`)
      			.then((res) => res.json())
      			.then((data) => setDiversity(data))
      			.catch(() => setDiversity(null));
	}, [claimId]);

	if (loading) return <p>Loading results...</p>;
	if (!result || result.error) return <p>No results available.</p>;

	return (
		<div className="claim-results">
			<h3>Fact-Check Results</h3>
			<p>Credibility Score: {result.credibility_score} ({result.credibility_label})</p>
			<p>Source Reputation: {result.source_reputation}</p>
			<p>Contradiction Detected: {result.contradiction_detected ? "Yes" : "No"}</p>
		{diversity && diversity.is_single_source_biased && (
        <div style={{
          backgroundColor: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: '8px',
          padding: '8px 12px',
          marginTop: '8px',
          color: '#856404',
          fontSize: '0.85rem'
        }}>
          Warning: This claim is supported by only one source type and may be biased.
        </div>
      )}
		</div>
	);
}

export default ClaimResults;