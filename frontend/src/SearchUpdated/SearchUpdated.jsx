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
	const [files, setFiles] = useState([]);
  	const fileInputRef = useRef(null);
	const [uploadedFile, setUploadedFile] = useState(null);
	const [results, setResults] = useState([]);
	const [isLoading, setIsLoading] = useState(false);
	const [word_count_error, set_word_count_Error] = useState("");
	const resultsRef = useRef(null);

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
			const response = await fetch("http://127.0.0.1:5001/fact-check", {
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
	const FILE_LIMIT = 1;

	const getFileIcon = (file) => {
		if (file.type.startsWith("image/")) return null;
		if (file.type.includes("pdf")) return "📄";
		if (file.type.includes("word") || file.name.endsWith(".docx")) return "📝";
		if (file.type.includes("sheet") || file.name.endsWith(".xlsx")) return "📊";
		return "📎";
	};

	const handleKeyDown = (e) => {
		if (e.key === "Enter") {
			if (!e.shiftKey) {
				e.preventDefault();
				handleSubmit(e);
			}
		}
	};

	const verdictIcon = (category) => {
		switch (category) {
			case "true":
				return "✅";
			case "false":
				return "❌";
			case "mixed":
				return "⚠️";
			default:
				return "ℹ️";
		}
	};

	return (
		<>
			<form onSubmit={handleSubmit} className="search-container">
				{/* File previews */}
        {files.length > 0 && (
          <>
            <div className="file-previews">
              {files.map((file, idx) => {
                const preview = getFilePreview(file);
                const icon = getFileIcon(file);
                return (
                  <div key={idx} className="file-chip">
                    {preview ? (
                      <img src={preview} alt={file.name} className="file-thumb" />
                    ) : (
                      <span className="file-icon">{icon}</span>
                    )}
                    <span className="file-name">{file.name}</span>
                    <button
                      type="button"
                      className="file-remove"
                      onClick={() => removeFile(idx)}
                      aria-label="Remove file"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>
                );
              })}
            </div>
            <hr className="search-divider" />
          </>
        )}

				<textarea
					value={input}
					onChange={handleInputChange}
					onKeyDown={handleKeyDown}
					placeholder="Type a claim or input a file to be fact-checked"
					className="search-input"
					rows="3"
				/>
				{word_count_error && <div className="word_count"> ⚠️ {word_count_error}</div>}
				{uploadedFile && (
					<div className="uploaded-file">
						<span className="file-name">{uploadedFile.name}</span>
						<button type="button" className="remove-file" onClick={removeFile}>
							✕
						</button>
					</div>
				)}

				<div className="search-actions">
					<label htmlFor="file-upload" className="icon-button">
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
						}>
						{isLoading ? (
							<span className="spinner" />
						) : (
							<svg
								width="20"
								height="20"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								strokeWidth="2">
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

					return (
						<div key={index} className="result-card">
							<div className="search-term-header">
								<small>Results for:</small>
								<h4>{item.original_claim}</h4>
							</div>

							{factChecks.length > 0 ? (
								<>
									{/*Summary Verdict */}
									{verdict && (
										<div className={`verdict-summary verdict-${verdict.category}`}>
											<div className="verdict-headline">
												<span className="verdict-icon">{verdictIcon(verdict.category)}</span>
												<p className="verdict-text">{verdict.summary}</p>
											</div>

											{(s.showBreakdown ?? true) && Object.keys(verdict.breakdown).length > 1 && (
												<div className="verdict-breakdown">
													<small>Breakdown:</small>
													<ul>
														{Object.entries(verdict.breakdown)
															.sort((a, b) => b[1] - a[1])
															.map(([rating, count]) => (
																<li key={rating}>
																	<span className="breakdown-rating">{rating}</span>
																	<span className="breakdown-count">× {count}</span>
																</li>
															))}
													</ul>
												</div>
											)}
										</div>
									)}
									{factChecks.map((claim, i) => (
										<div key={i} className="claim-match">
											<p className="db-claim-text">
												<strong>Match:</strong> {claim.text}
											</p>
											{claim.claimReview.map((review, j) => (
												<div key={j} className="verdict-row">
													<span className={`rating-badge ${review.ratingCategory || "unrated"}`}>
														{review._inverted 
															? (review.ratingCategory === "true" ? "Supports Claim" : "Contradicts Claim")
															: (review.condensedRating || review.textualRating)
														}
													</span>
													<span className="original-rating">({review.textualRating})</span>
													<span className="publisher-name">by {review.publisher.name}</span>
													{(s.showSourceLinks ?? true) && (
														<a
															href={review.url}
															target="_blank"
															rel="noreferrer"
															className="view-link">
															Source
														</a>
													)}
												</div>
											))}
										</div>
									))}
								</>
							) : verdict ? (
								<div className={`verdict-summary verdict-${verdict.category}`}>
									<div className="verdict-headline">
										<span className="verdict-icon">{verdictIcon(verdict.category)}</span>
										<p className="verdict-text">{verdict.summary}</p>
									</div>
									{verdict.confidence_score && (
										<div style={{
											display: 'flex',
											alignItems: 'center',
											gap: '0.5rem',
											marginTop: '0.75rem',
										}}>
											<div style={{
												flex: 1,
												height: '6px',
												background: '#e5e7eb',
												borderRadius: '3px',
												overflow: 'hidden',
											}}>
												<div style={{
													width: `${verdict.confidence_score}%`,
													height: '100%',
													background: verdict.confidence_score > 70 ? '#22c55e' : verdict.confidence_score > 40 ? '#f59e0b' : '#ef4444',
													borderRadius: '3px',
												}} />
											</div>
											<span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
												{verdict.confidence_score}% confidence
											</span>
										</div>
									)}
									{verdict.sources && verdict.sources.length > 0 && (
										<div style={{ marginTop: '0.75rem' }}>
											<small style={{ color: '#9ca3af', textTransform: 'uppercase', fontSize: '0.7rem', letterSpacing: '0.05em' }}>Sources:</small>
											<ul style={{ listStyle: 'none', padding: 0, margin: '0.35rem 0 0' }}>
												{verdict.sources.map((src, i) => (
													<li key={i} style={{ fontSize: '0.85rem', marginBottom: '0.3rem' }}>
														<a href={src.url} target="_blank" rel="noreferrer" style={{ color: '#6366f1', textDecoration: 'none' }}>
															{src.title}
														</a>
														<span style={{ color: '#9ca3af', fontSize: '0.78rem' }}> — {src.publisher}</span>
													</li>
												))}
											</ul>
										</div>
									)}
									{verdict.ai_generated && (
										<p style={{ fontSize: '0.78rem', color: '#9ca3af', marginTop: '0.5rem', fontStyle: 'italic' }}>
											AI-generated analysis — no professional fact-checks were found for this claim
										</p>
									)}
								</div>
							) : (
                            <p className="no-results">No professional fact-checks found for this claim.</p>
                        )}
						</div>
					);
				})}
			</div>
		</>
	);
}

export default SearchUpdated;
