/**
 * Shared fact-report display components.
 * Used by both SearchUpdated (live results) and Account (history).
 */
import '../SearchUpdated/SearchUpdated.css';

export const TIER_LABELS = {
	cached_db:         'Cited DB Cache',
	expert_fact_check: 'Expert Fact Check',
	web_scrape:        'Primary Document',
	web_search:        'Web Search',
};

export const TIER_COLORS = {
	cached_db:         'tier-cached',
	expert_fact_check: 'tier-expert',
	web_scrape:        'tier-scrape',
	web_search:        'tier-websearch',
};

export function verdictIcon(category) {
	switch (category) {
		case 'true':   return '✅';
		case 'false':  return '❌';
		case 'mixed':  return '⚠️';
		default:       return 'ℹ️';
	}
}

export function CredibilityBar({ score }) {
	const pct = Math.round(score ?? 0);
	let colorClass = 'cred-low';
	if (pct >= 80) colorClass = 'cred-high';
	else if (pct >= 60) colorClass = 'cred-med';
	else if (pct >= 40) colorClass = 'cred-warn';

	return (
		<div className="credibility-bar-wrapper">
			<div className="credibility-bar-track">
				<div
					className={`credibility-bar-fill ${colorClass}`}
					style={{ width: `${pct}%` }}
				/>
			</div>
			<span className={`credibility-score-label ${colorClass}`}>{pct}% credibility</span>
		</div>
	);
}

export function SourceCard({ src, showLinks = true }) {
	const tierClass = TIER_COLORS[src.tier] || 'tier-websearch';
	const hasUrl = src.url && !src.url.startsWith('cited://');

	return (
		<div className={`source-card ${tierClass}`}>
			<div className="source-card-header">
				<span className={`tier-badge ${tierClass}`}>
					{TIER_LABELS[src.tier] || src.tier_label || src.tier}
				</span>
				{hasUrl && showLinks ? (
					<a href={src.url} target="_blank" rel="noreferrer" className="source-title-link">
						{src.title}
					</a>
				) : (
					<span className="source-title-text">{src.title}</span>
				)}
				{src.publisher && src.publisher !== src.title && (
					<span className="source-publisher">· {src.publisher}</span>
				)}
				{src.rating && src.rating !== 'unrated' && (
					<span className={`source-rating rating-badge ${src.tier === 'expert_fact_check' ? 'expert' : ''}`}>
						{src.rating}
					</span>
				)}
			</div>
			{src.quote && (
				<blockquote className="source-preview">{src.quote}</blockquote>
			)}
		</div>
	);
}

export function ReportSection({ report, showLinks = true }) {
	if (!report || !report.sources) return null;

	const tierCounts  = report.sources_by_tier || {};
	const activeTiers = Object.entries(tierCounts).filter(([, c]) => c > 0);

	return (
		<div className="report-section">
			<div className="report-header">
				<CredibilityBar score={report.credibility_score} />
				{activeTiers.length > 0 && (
					<div className="tiers-searched">
						{activeTiers.map(([tier, count]) => (
							<span key={tier} className={`tier-chip ${TIER_COLORS[tier] || 'tier-websearch'}`}>
								{TIER_LABELS[tier] || tier}: {count}
							</span>
						))}
					</div>
				)}
			</div>

			{report.analysis_notes && (
				<div className="analysis-notes">
					<p>{report.analysis_notes}</p>
				</div>
			)}

			{report.sources.length > 0 && (
				<div className="sources-section">
					<h5 className="sources-heading">Sources referenced in scoring</h5>
					{report.sources.map((src, i) => (
						<SourceCard key={i} src={src} showLinks={showLinks} />
					))}
				</div>
			)}
		</div>
	);
}
