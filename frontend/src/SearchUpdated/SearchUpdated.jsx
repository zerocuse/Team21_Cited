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
	const [activeTab, setActiveTab] = useState("verdict"); // verdict | sources | news

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
		setActiveTab("verdict"); // Reset to verdict tab on new search
		const formData = new FormData();
		formData.append("query", input);
		formData.append("fact_check_method", s.factCheckMethod ?? 'web-scrape');
		if (uploadedFile) formData.append("file", uploadedFile);

		try {
			const token = localStorage.getItem('token');
			const response = await fetch("http://127.0.0.1:5000/fact-check", {
				method: "POST",
    			headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    			body: formData,
			});
			if (!response.ok) throw new Error(`Server responded with ${response.status}`);
			const data = await response.json();
			setResults(data.results || []);
			if ((s.autoScroll ?? false) && resultsRef.current) {
				setTimeout(() => resultsRef.current.scrollIntoView({ behavior: 'smooth' }), 100);
			}
		} catch (error) {
			console.error("Fetch error:", error);
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

	const getFilePreview = (file) => {
		if (file.type.startsWith("image/")) return URL.createObjectURL(file);
		return null;
	};

	const getFileIcon = (file) => {
		if (file.type.startsWith("image/")) return null;
		if (file.type.includes("pdf")) return "📄";
		if (file.type.includes("word") || file.name.endsWith(".docx")) return "📝";
		if (file.type.includes("sheet") || file.name.endsWith(".xlsx")) return "📊";
		return "📎";
	};

	const handleKeyDown = (e) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSubmit(e);
		}
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

	const confidenceColor = (confidence) => {
		switch (confidence?.toLowerCase()) {
			case "high":
				return "#10b981";
			case "medium":
				return "#f59e0b";
			case "low":
				return "#ef4444";
			default:
				return "#6b7280";
		}
	};

	const sourceStanceIcon = (stance) => {
		switch (stance?.toLowerCase()) {
			case "supports":
				return "👍";
			case "contradicts":
				return "👎";
			default:
				return "📌";
		}
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
					rows="3"
				/>
				
				{word_count_error && (
					<div className="word_count">⚠️ {word_count_error}</div>
				)}

				{uploadedFile && (
					<div className="uploaded-file">
						<span className="file-icon">{getFileIcon(uploadedFile)}</span>
						<span className="file-name">{uploadedFile.name}</span>
						<button type="button" className="remove-file" onClick={removeFile}>
							✕
						</button>
					</div>
				)}

				<div className="search-actions">
					<label htmlFor="file-upload" className="icon-button" title="Upload document">
						<img src="./src/assets/attachment-icon.svg" alt="fileupload" className='attachment-icon'/>
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

			{/* Results */}
			<div className="results-list" ref={resultsRef}>
				{results.map((item, index) => {
					const s = getSettings();
					const verdict = item.verdict;
					const factChecks = (item.fact_checks || []).slice(0, s.resultsPerClaim ?? 5);
					const news = item.news || {};
					const sourcesCited = item.sources_cited || [];
					const isCurrentEvent = item.is_current_event || false;

					return (
						<div key={index} className="result-card">
							{/* Claim Header */}
							<div className="search-term-header">
								<small>Claim:</small>
								<h4>{item.original_claim}</h4>
								{isCurrentEvent && <span className="current-event-badge">🔥 Current Event</span>}
							</div>

							{/* Main Verdict Section */}
							{verdict && (
								<div className={`verdict-section verdict-${verdict.verdict}`}>
									{/* Verdict Banner */}
									<div className="verdict-banner">
										<div className="verdict-left">
											<span className="verdict-icon">{verdictIcon(verdict.verdict)}</span>
											<div className="verdict-info">
												<h3 className="verdict-title">{verdict.verdict.toUpperCase()}</h3>
												<p className="verdict-summary">{verdict.summary}</p>
											</div>
										</div>
										<div className="verdict-right">
											<div className="confidence-badge" style={{ borderColor: confidenceColor(verdict.confidence) }}>
												<span className="confidence-label">Confidence</span>
												<span className="confidence-value">{verdict.confidence.toUpperCase()}</span>
											</div>
											<span className="verdict-source">{verdict.source}</span>
										</div>
									</div>

									{/* Detailed Reasoning */}
									{(s.showDetailedReasoning ?? true) && verdict.detailed_reasoning && (
										<div className="reasoning-box">
											<h5>Analysis</h5>
											<p>{verdict.detailed_reasoning}</p>
										</div>
									)}

									{/* Key Findings */}
									{(s.showKeyFindings ?? true) && verdict.key_findings && verdict.key_findings.length > 0 && (
										<div className="findings-box">
											<h5>Key Findings</h5>
											<ul>
												{verdict.key_findings.map((finding, idx) => (
													<li key={idx}>{finding}</li>
												))}
											</ul>
										</div>
									)}

									{/* Red Flags */}
									{verdict.red_flags && verdict.red_flags.length > 0 && (
										<div className="red-flags-box">
											<h5>⚠️ Red Flags</h5>
											<ul>
												{verdict.red_flags.map((flag, idx) => (
													<li key={idx}>{flag}</li>
												))}
											</ul>
										</div>
									)}

									{/* Evidence Assessment */}
									{verdict.evidence_assessment && (
										<div className="evidence-box">
											<h5>Evidence Assessment</h5>
											<div className="evidence-grid">
												<div className="evidence-item">
													<strong>Source Agreement:</strong>
													<span>{verdict.evidence_assessment.source_agreement}</span>
												</div>
												<div className="evidence-item">
													<strong>Fact-Checks Found:</strong>
													<span>{verdict.totalFactChecks}</span>
												</div>
												<div className="evidence-item">
													<strong>News Articles:</strong>
													<span>{verdict.totalNewsArticles}</span>
												</div>
											</div>
											{verdict.evidence_assessment.fact_checks_summary && (
												<p className="evidence-text">
													<strong>Fact-Checks:</strong> {verdict.evidence_assessment.fact_checks_summary}
												</p>
											)}
											{verdict.evidence_assessment.news_coverage_summary && (
												<p className="evidence-text">
													<strong>News Coverage:</strong> {verdict.evidence_assessment.news_coverage_summary}
												</p>
											)}
											{verdict.evidence_assessment.trending_context && (
												<p className="evidence-text">
													<strong>Trending:</strong> {verdict.evidence_assessment.trending_context}
												</p>
											)}
										</div>
									)}

									{/* Watch/Context */}
									{(s.showWhatToWatch ?? true) && verdict.what_to_watch && (
										<div className="watch-box">
											<h5>What to Watch</h5>
											<p>{verdict.what_to_watch}</p>
										</div>
									)}
								</div>
							)}

							{/* Tabbed Sources/News */}
							{(sourcesCited.length > 0 || news.articles?.length > 0 || factChecks.length > 0) && (
								<div className="results-tabs">
									<div className="tab-buttons">
										<button
											className={`tab-btn ${activeTab === "verdict" ? "active" : ""}`}
											onClick={() => setActiveTab("verdict")}>
											Verdict
										</button>
										{sourcesCited.length > 0 && (
											<button
												className={`tab-btn ${activeTab === "sources" ? "active" : ""}`}
												onClick={() => setActiveTab("sources")}>
												Sources ({sourcesCited.length})
											</button>
										)}
										{news.articles?.length > 0 && (
											<button
												className={`tab-btn ${activeTab === "news" ? "active" : ""}`}
												onClick={() => setActiveTab("news")}>
												News ({news.articles.length})
											</button>
										)}
										{factChecks.length > 0 && (
											<button
												className={`tab-btn ${activeTab === "matches" ? "active" : ""}`}
												onClick={() => setActiveTab("matches")}>
												Claim Matches ({factChecks.length})
											</button>
										)}
									</div>

									{/* Sources Tab */}
									{activeTab === "sources" && sourcesCited.length > 0 && (
										<div className="tab-content sources-tab">
											<div className="sources-list">
												{sourcesCited.map((src, idx) => (
													<div key={idx} className="source-item">
														<div className="source-header">
															<span className="source-type-badge">{src.type}</span>
															<span className="source-stance">{sourceStanceIcon(src.stance)} {src.stance || "neutral"}</span>
														</div>
														<div className="source-content">
															{src.publisher && (
																<h6 className="source-name">{src.publisher}</h6>
															)}
															{src.source && (
																<h6 className="source-name">{src.source}</h6>
															)}
															{src.rating && (
																<span className={`source-rating rating-${src.rating.toLowerCase()}`}>
																	{src.rating}
																</span>
															)}
															{src.title && (
																<p className="source-title">{src.title}</p>
															)}
															{src.excerpt && (
																<p className="source-excerpt">"{src.excerpt}"</p>
															)}
															<div className="source-meta">
																{src.date && <span className="source-date">📅 {new Date(src.date).toLocaleDateString()}</span>}
																{src.url && (
																	<a
																		href={src.url}
																		target="_blank"
																		rel="noreferrer"
																		className="source-link">
																		View Source →
																	</a>
																)}
															</div>
														</div>
													</div>
												))}
											</div>
										</div>
									)}

									{/* News Tab */}
									{activeTab === "news" && news.articles?.length > 0 && (
										<div className="tab-content news-tab">
											<div className="news-grid">
												{news.articles.map((article, idx) => (
													<div key={idx} className="news-card">
														{article.imageUrl && (
															<img src={article.imageUrl} alt={article.title} className="news-image" />
														)}
														<div className="news-content">
															<span className="news-source">{article.source}</span>
															<h5 className="news-title">{article.title}</h5>
															{article.description && (
																<p className="news-description">{article.description}</p>
															)}
															<div className="news-footer">
																{article.publishedAt && (
																	<span className="news-date">📅 {new Date(article.publishedAt).toLocaleDateString()}</span>
																)}
																<a
																	href={article.url}
																	target="_blank"
																	rel="noreferrer"
																	className="news-link">
																	Read More →
																</a>
															</div>
														</div>
													</div>
												))}
											</div>
											{news.source_diversity && (
												<div className="news-stats">
													<p>📊 Coverage from {news.source_diversity.unique_sources} unique source{news.source_diversity.unique_sources !== 1 ? 's' : ''}</p>
													{news.source_diversity.is_diverse && (
														<span className="diversity-badge">✓ Diverse Coverage</span>
													)}
												</div>
											)}
										</div>
									)}

									{/* Claim Matches Tab */}
									{activeTab === "matches" && factChecks.length > 0 && (
										<div className="tab-content matches-tab">
											{factChecks.map((claim, i) => (
												<div key={i} className="claim-match">
													<div className="claim-text-box">
														<strong>Similar Claim:</strong>
														<p>{claim.text}</p>
														{claim.relevance && (
															<span className="relevance-score">Relevance: {Math.round(claim.relevance * 100)}%</span>
														)}
													</div>

													<div className="reviews-list">
														{claim.claimReview && claim.claimReview.map((review, j) => (
															<div key={j} className="review-item">
																<div className="review-rating">
																	<span className={`rating-badge ${review.ratingCategory || "unrated"}`}>
																		{review.condensedRating || review.textualRating || "Unrated"}
																	</span>
																	{review.textualRating && review.textualRating !== review.condensedRating && (
																		<span className="textual-rating">({review.textualRating})</span>
																	)}
																</div>
																<div className="review-details">
																	<strong>{review.publisher?.name || "Unknown Publisher"}</strong>
																	{review.reviewDate && (
																		<span className="review-date">📅 {new Date(review.reviewDate).toLocaleDateString()}</span>
																	)}
																	{(s.showSourceLinks ?? true) && review.url && (
																		<a
																			href={review.url}
																			target="_blank"
																			rel="noreferrer"
																			className="review-link">
																			View Review →
																		</a>
																	)}
																</div>
															</div>
														))}
													</div>
												</div>
											))}
										</div>
									)}
								</div>
							)}

							{/* No Results Fallback */}
							{!verdict && factChecks.length === 0 && (
								<p className="no-results">
									No results found. Try refining your claim or check back later.
								</p>
							)}
						</div>
					);
				})}
			</div>
		</>
	);
}

export default SearchUpdated;