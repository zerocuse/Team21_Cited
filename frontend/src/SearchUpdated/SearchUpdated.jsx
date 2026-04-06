import { useState, useRef } from "react";
import "./SearchUpdated.css";

function getSettings() {
	try {
		return JSON.parse(localStorage.getItem('cited_settings') || '{}')
	} catch {
		return {}
	}
}

function SearchUpdated() {
	const [input, setInput] = useState("");
	const [uploadedFile, setUploadedFile] = useState(null);
	const [results, setResults] = useState([]);
	const [isLoading, setIsLoading] = useState(false);
	const [word_count_error, set_word_count_Error] = useState("");
	const resultsRef = useRef(null);
	const [expandedSections, setExpandedSections] = useState({});

	const handleSubmit = async (e) => {
		if (e) e.preventDefault();
		const s = getSettings();
		const minWords = s.minWordCount ?? 3;
		const wordCount = input.trim().split(/\s+/).filter(Boolean).length;
		const isValid = uploadedFile || wordCount >= minWords;

		if (!isValid) {
			set_word_count_Error(`Minimum of ${minWords} word${minWords === 1 ? '' : 's'} to fact-check`);
			return;
		}
		set_word_count_Error("");
		if (isLoading) return;

		setIsLoading(true);
		const formData = new FormData();
		formData.append("query", input);
		formData.append("fact_check_method", s.factCheckMethod ?? 'web-scrape');
		if (uploadedFile) formData.append("file", uploadedFile);

		try {
			const token = localStorage.getItem('token');
			const response = await fetch("http://localhost:5000/fact-check", { 
				method: "POST",
				headers: token ? { 'Authorization': `Bearer ${token}` } : {},
				body: formData,
			});
			if (!response.ok) throw new Error(`Server responded with ${response.status}`);
			const data = await response.json();
			
			console.log("API Response:", data); // Debug log
			
			setResults(data.results || []);
			
			// Open sources and evidence sections by default
			if (data.results && data.results.length > 0) {
				const newExpanded = {};
				data.results.forEach((_, idx) => {
					newExpanded[`sources-${idx}`] = true;
					newExpanded[`evidence-${idx}`] = true;
					newExpanded[`findings-${idx}`] = true;
				});
				setExpandedSections(newExpanded);
			}
			
			if ((s.autoScroll ?? false) && resultsRef.current) {
				setTimeout(() => resultsRef.current.scrollIntoView({ behavior: 'smooth' }), 100);
			}
		} catch (error) {
			console.error("Fetch error:", error);
			alert("Error fetching results: " + error.message);
		} finally {
			setIsLoading(false);
		}
	};

	const handleInputChange = (e) => {
		setInput(e.target.value);
		if (word_count_error) set_word_count_Error("");
	};

	const handleFileUpload = (e) => {
		const file = e.target.files[0];
		if (!file) return;
		setUploadedFile(file);
	};

	const removeFile = () => {
		setUploadedFile(null);
		const fileInput = document.getElementById("file-upload");
		if (fileInput) fileInput.value = "";
	};

	const handleKeyDown = (e) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSubmit(e);
		}
	};

	const getVerdictClass = (verdict) => {
		if (!verdict) return "verdict-unrated";
		const v = verdict.toLowerCase().replace(/\s+/g, '-');
		return `verdict-${v}`;
	};

	const verdictIcon = (verdict) => {
		if (!verdict) return "ℹ️";
		const v = verdict.toLowerCase();
		if (v === "true") return "✅";
		if (v === "false") return "❌";
		if (v.includes("mostly true")) return "✔️";
		if (v.includes("mostly false")) return "✖️";
		if (v === "mixed") return "⚠️";
		return "❓";
	};

	const toggleSection = (key) => {
		setExpandedSections(prev => ({
			...prev,
			[key]: !prev[key]
		}));
	};

	const getRatingBadgeClass = (rating) => {
		if (!rating) return "unrated";
		const r = rating.toLowerCase().replace(/\s+/g, '-');
		return r;
	};

	const getStanceClass = (stance) => {
		if (!stance) return "neutral";
		return stance.toLowerCase();
	};

	const getConfidenceClass = (confidence) => {
		if (!confidence) return "low";
		return confidence.toLowerCase();
	};

	const getAgreementClass = (agreement) => {
		if (!agreement) return "disagree";
		if (agreement.toLowerCase() === "agree") return "strong";
		if (agreement.toLowerCase() === "partial") return "partial";
		return "disagree";
	};

	return (
		<>
			{/* Search Form */}
			<form onSubmit={handleSubmit} className="search-container">
				<textarea
					value={input}
					onChange={handleInputChange}
					onKeyDown={handleKeyDown}
					placeholder="Type a claim to be fact-checked..."
					className="search-input"
					rows="4"
				/>
				
				{word_count_error && (
					<div className="word_count">⚠️ {word_count_error}</div>
				)}

				{uploadedFile && (
					<div className="uploaded-file">
						<span className="file-name">📎 {uploadedFile.name}</span>
						<button type="button" className="remove-file" onClick={removeFile}>
							✕
						</button>
					</div>
				)}

				<div className="search-actions">
					<label htmlFor="file-upload" className="icon-button" title="Upload document">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
							<path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
						</svg>
						<input
							id="file-upload"
							type="file"
							onChange={handleFileUpload}
							style={{ display: "none" }}
						/>
					</label>

					<button
						type="submit"
						className="submit-button"
						disabled={
							isLoading || (!uploadedFile && input.trim().split(/\s+/).filter(Boolean).length < (getSettings().minWordCount ?? 3))
						}
						title={isLoading ? "Checking..." : "Fact-check this claim"}>
						{isLoading ? (
							<span className="spinner" />
						) : (
							<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
								<line x1="12" y1="19" x2="12" y2="5" />
								<polyline points="5 12 12 5 19 12" />
							</svg>
						)}
					</button>
				</div>
			</form>

			{/* Loading State */}
			{isLoading && (
				<div className="loading-container">
					<div className="loading-animation">
						<div className="loading-text">
							<h4>Fact-checking your claim...</h4>
							<p>Searching through multiple sources</p>
						</div>
						<div className="loading-steps">
							<div className="loading-step">
								<span className="spinner"></span>
								<span>Searching fact-check databases</span>
							</div>
							<div className="loading-step">
								<span className="spinner"></span>
								<span>Analyzing news coverage</span>
							</div>
							<div className="loading-step">
								<span className="spinner"></span>
								<span>Compiling verdict</span>
							</div>
						</div>
					</div>
				</div>
			)}

			{/* Results */}
			<div className="results-list" ref={resultsRef}>
				{results.length === 0 && !isLoading ? (
					<div style={{ textAlign: 'center', color: 'var(--muted)', marginTop: '2rem' }}>
						<p>No results yet. Enter a claim above to get started.</p>
					</div>
				) : null}

				{results.map((item, index) => {
					const s = getSettings();
					const verdict = item.verdict;
					const sourcesCited = item.sources_cited || [];
					const news = item.news || {};
					const factChecks = (item.fact_checks || []).slice(0, s.resultsPerClaim ?? 5);

					console.log("Result item:", item); // Debug log
					console.log("Verdict:", verdict); // Debug log
					console.log("Sources:", sourcesCited); // Debug log

					return (
						<div key={index} className="result-card">
							{/* Claim Header */}
							<div className="claim-header">
								<div className="claim-label">
									<span className="claim-label-text">Claim:</span>
									{item.is_current_event && (
										<span className="current-event-badge">🔥 Current Event</span>
									)}
								</div>
								<p className="claim-text">{item.original_claim}</p>
							</div>

							{/* Main Verdict - ALWAYS VISIBLE */}
							{verdict ? (
								<div className={`gemini-verdict ${getVerdictClass(verdict.verdict)}`}>
									<div className="verdict-badge-row">
										<span className="verdict-icon-large">{verdictIcon(verdict.verdict)}</span>
										<div className="verdict-label-group">
											<span className="verdict-label">{verdict.verdict.toUpperCase()}</span>
										</div>
									</div>

									<div style={{ marginTop: '0.5rem' }}>
										<p style={{ margin: '0.5rem 0', fontSize: '0.95rem', lineHeight: '1.5' }}>
											{verdict.summary}
										</p>
									</div>

									{/* Confidence & Source */}
									<div className="verdict-stats" style={{ marginTop: '0.75rem' }}>
										<span className={`confidence-pill ${getConfidenceClass(verdict.confidence)}`}>
											📊 {verdict.confidence?.toUpperCase() || 'UNKNOWN'}
										</span>
										<span className="verdict-source-tag">
											{verdict.source || 'Unknown Source'}
										</span>
									</div>

									{/* Detailed Reasoning */}
									{verdict.detailed_reasoning && (
										<div className="verdict-summary-text">
											<p><strong>Analysis:</strong> {verdict.detailed_reasoning}</p>
										</div>
									)}

									{/* Key Findings */}
									{verdict.key_findings && verdict.key_findings.length > 0 && (
										<div>
											<button
												className="section-toggle"
												onClick={() => toggleSection(`findings-${index}`)}
												style={{ marginTop: '0.75rem' }}>
												<span>🎯 Key Findings ({verdict.key_findings.length})</span>
												<span className={`toggle-arrow ${expandedSections[`findings-${index}`] ? 'expanded' : ''}`}>→</span>
											</button>
											{expandedSections[`findings-${index}`] && (
												<div className="section-content">
													<ul className="findings-list">
														{verdict.key_findings.map((finding, idx) => (
															<li key={idx} className="finding-item">{finding}</li>
														))}
													</ul>
												</div>
											)}
										</div>
									)}

									{/* Red Flags */}
									{verdict.red_flags && verdict.red_flags.length > 0 && (
										<div>
											<button
												className="section-toggle"
												onClick={() => toggleSection(`flags-${index}`)}
												style={{ marginTop: '0.75rem' }}>
												<span>⚠️ Red Flags ({verdict.red_flags.length})</span>
												<span className={`toggle-arrow ${expandedSections[`flags-${index}`] ? 'expanded' : ''}`}>→</span>
											</button>
											{expandedSections[`flags-${index}`] && (
												<div className="section-content">
													<ul className="red-flags-list">
														{verdict.red_flags.map((flag, idx) => (
															<li key={idx} className="red-flag-item">{flag}</li>
														))}
													</ul>
												</div>
											)}
										</div>
									)}

									{/* Evidence Assessment */}
									{verdict.evidence_assessment && (
										<div>
											<button
												className="section-toggle"
												onClick={() => toggleSection(`evidence-${index}`)}
												style={{ marginTop: '0.75rem' }}>
												<span>📋 Evidence Assessment</span>
												<span className={`toggle-arrow ${expandedSections[`evidence-${index}`] ? 'expanded' : ''}`}>→</span>
											</button>
											{expandedSections[`evidence-${index}`] && (
												<div className="section-content">
													<div className="evidence-grid">
														<div className="evidence-card neutral">
															<h6>Source Agreement</h6>
															<div style={{ marginTop: '0.5rem' }}>
																<span className={`agreement-badge ${getAgreementClass(verdict.evidence_assessment.source_agreement)}`}>
																	{verdict.evidence_assessment.source_agreement?.toUpperCase() || 'UNKNOWN'}
																</span>
															</div>
														</div>
														<div className="evidence-card neutral">
															<h6>Fact-Checks Found</h6>
															<p style={{ margin: '0.5rem 0 0 0', fontSize: '1.1rem', fontWeight: '700' }}>
																{verdict.totalFactChecks || 0}
															</p>
														</div>
														<div className="evidence-card neutral">
															<h6>News Articles</h6>
															<p style={{ margin: '0.5rem 0 0 0', fontSize: '1.1rem', fontWeight: '700' }}>
																{verdict.totalNewsArticles || 0}
															</p>
														</div>
													</div>

													{verdict.evidence_assessment.fact_checks_summary && (
														<div className="evidence-card neutral" style={{ marginTop: '0.85rem' }}>
															<h6>Fact-Check Summary</h6>
															<p>{verdict.evidence_assessment.fact_checks_summary}</p>
														</div>
													)}

													{verdict.evidence_assessment.news_coverage_summary && (
														<div className="evidence-card neutral" style={{ marginTop: '0.85rem' }}>
															<h6>News Coverage</h6>
															<p>{verdict.evidence_assessment.news_coverage_summary}</p>
														</div>
													)}

													{verdict.evidence_assessment.trending_context && (
														<div className="evidence-card neutral" style={{ marginTop: '0.85rem' }}>
															<h6>Trending Status</h6>
															<p>{verdict.evidence_assessment.trending_context}</p>
														</div>
													)}
												</div>
											)}
										</div>
									)}

									{/* What to Watch */}
									{verdict.what_to_watch && (
										<div className="watch-text" style={{ marginTop: '0.85rem' }}>
											<strong>What to Watch:</strong>
											<p>{verdict.what_to_watch}</p>
										</div>
									)}
								</div>
							) : (
								<div className="no-evidence">
									⏳ Verdict not available
								</div>
							)}

							{/* Sources Cited */}
							{sourcesCited && sourcesCited.length > 0 && (
								<div style={{ marginTop: '1rem' }}>
									<button
										className="section-toggle"
										onClick={() => toggleSection(`sources-${index}`)}>
										<span>📚 Sources Cited ({sourcesCited.length})</span>
										<span className={`toggle-arrow ${expandedSections[`sources-${index}`] ? 'expanded' : ''}`}>→</span>
									</button>

									{expandedSections[`sources-${index}`] && (
										<div className="section-content">
											<div className="evidence-grid">
												{sourcesCited.map((src, idx) => (
													<div key={idx} className={`evidence-card ${getStanceClass(src.stance)}`}>
														<div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
															<span className="rating-badge" style={{
																background: 'var(--primary-lighter-gray)',
																color: 'var(--primary-dark-gray)'
															}}>
																{src.type || 'source'}
															</span>
															<span className={`news-stance-tag ${getStanceClass(src.stance)}`}>
																{src.stance ? src.stance.charAt(0).toUpperCase() + src.stance.slice(1) : 'Neutral'}
															</span>
														</div>

														<h6>{src.publisher || src.source || 'Unknown'}</h6>

														{src.rating && (
															<span className={`rating-badge ${getRatingBadgeClass(src.rating)}`}>
																{src.rating}
															</span>
														)}

														{src.title && (
															<p style={{ margin: '0.5rem 0 0 0', fontSize: '0.95rem', fontWeight: '600', lineHeight: '1.3' }}>
																{src.title}
															</p>
														)}

														{src.excerpt && (
															<p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', fontStyle: 'italic', color: 'var(--muted)', lineHeight: '1.4' }}>
																"{src.excerpt}"
															</p>
														)}

														<div className="verdict-stats" style={{ marginTop: '0.75rem' }}>
															{src.date && (
																<span className="stat-item">
																	📅 {new Date(src.date).toLocaleDateString()}
																</span>
															)}
															{src.url && (
																<a
																	href={src.url}
																	target="_blank"
																	rel="noreferrer"
																	className="source-link"
																	style={{ color: 'inherit', textDecoration: 'underline', fontWeight: '600' }}>
																	View Source
																</a>
															)}
														</div>
													</div>
												))}
											</div>
										</div>
									)}
								</div>
							)}

							{/* Fact Check Matches */}
							{factChecks && factChecks.length > 0 && (
								<div style={{ marginTop: '1rem' }}>
									<button
										className="section-toggle"
										onClick={() => toggleSection(`matches-${index}`)}>
										<span>🔍 Similar Claims ({factChecks.length})</span>
										<span className={`toggle-arrow ${expandedSections[`matches-${index}`] ? 'expanded' : ''}`}>→</span>
									</button>

									{expandedSections[`matches-${index}`] && (
										<div className="section-content">
											<div className="evidence-grid">
												{factChecks.map((claim, i) => (
													<div key={i} className="fact-check-item neutral">
														<h6>{claim.text}</h6>

														{claim.relevance && (
															<span className={`relevance-badge ${claim.relevance >= 0.7 ? 'high' : claim.relevance >= 0.4 ? 'medium' : 'low'}`}>
																Relevance: {Math.round(claim.relevance * 100)}%
															</span>
														)}

														<div style={{ marginTop: '0.75rem' }}>
															{claim.claimReview && claim.claimReview.map((review, j) => (
																<div key={j} className="review-row">
																	<span className={`rating-badge ${getRatingBadgeClass(review.ratingCategory || review.textualRating)}`}>
																		{review.condensedRating || review.textualRating || "Unrated"}
																	</span>
																	<span className="stat-item">
																		{review.publisher?.name || "Unknown"}
																	</span>
																	{review.reviewDate && (
																		<span className="stat-item">
																			📅 {new Date(review.reviewDate).toLocaleDateString()}
																		</span>
																	)}
																	{review.url && (
																		<a
																			href={review.url}
																			target="_blank"
																			rel="noreferrer"
																			className="source-link"
																			style={{ fontSize: '0.9rem' }}>
																			View
																		</a>
																	)}
																</div>
															))}
														</div>
													</div>
												))}
											</div>
										</div>
									)}
								</div>
							)}

							{/* News Coverage */}
							{news.articles && news.articles.length > 0 && (
								<div style={{ marginTop: '1rem' }}>
									<button
										className="section-toggle"
										onClick={() => toggleSection(`news-${index}`)}>
										<span>📰 News Coverage ({news.articles.length})</span>
										<span className={`toggle-arrow ${expandedSections[`news-${index}`] ? 'expanded' : ''}`}>→</span>
									</button>

									{expandedSections[`news-${index}`] && (
										<div className="section-content">
											<div className="news-articles-list">
												{news.articles.map((article, idx) => (
													<a
														key={idx}
														href={article.url}
														target="_blank"
														rel="noreferrer"
														className="news-article-item">
														{article.imageUrl && (
															<img src={article.imageUrl} alt={article.title} className="news-article-thumb" />
														)}
														<span className="news-source">{article.source}</span>
														<h6 className="news-article-title">{article.title}</h6>
														{article.description && (
															<p style={{ margin: '0.5rem 0 0 0', color: 'var(--muted)' }}>
																{article.description}
															</p>
														)}
														<div className="news-article-meta" style={{ marginTop: '0.75rem' }}>
															{article.publishedAt && (
																<span className="news-date">
																	📅 {new Date(article.publishedAt).toLocaleDateString()}
																</span>
															)}
														</div>
													</a>
												))}
											</div>

											{news.source_diversity && (
												<div className="source-diversity" style={{ marginTop: '1rem' }}>
													<h6>Source Diversity</h6>
													<p style={{ margin: '0.5rem 0 0 0' }}>
														Coverage from {news.source_diversity.unique_sources} source{news.source_diversity.unique_sources !== 1 ? 's' : ''}
													</p>
													{news.source_diversity.is_diverse && (
														<span className="diversity-badge high" style={{ marginTop: '0.5rem' }}>
															✓ Diverse Coverage
														</span>
													)}
												</div>
											)}
										</div>
									)}
								</div>
							)}

							{/* No Results */}
							{!verdict && factChecks.length === 0 && (
								<div className="no-evidence">
									⚠️ No results found for this claim.
								</div>
							)}
						</div>
					);
				})}
			</div>
		</>
	);
}

export default SearchUpdated;