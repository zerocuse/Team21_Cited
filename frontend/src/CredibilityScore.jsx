import { useEffect, useState } from "react";

function CredibilityScore({ claimId }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!claimId) return;
    fetch(`/api/claim/${claimId}/result`)
      .then((res) => res.json())
      .then((d) => setData(d))
      .catch(() => setData({ credibility_label: "Not Available", credibility_score: null }));
  }, [claimId]);

  if (!data) return null;

  const color =
    data.credibility_label === "High" ? "#155724" :
    data.credibility_label === "Medium" ? "#856404" : "#721c24";

  return (
    <span style={{
      fontSize: '0.75rem',
      padding: '2px 8px',
      borderRadius: '12px',
      background: '#f0f0f0',
      color: color,
      marginLeft: '8px'
    }}>
      Credibility: {data.credibility_score !== null ? `${data.credibility_score} (${data.credibility_label})` : "Not Available"}
    </span>
  );
}

export default CredibilityScore;