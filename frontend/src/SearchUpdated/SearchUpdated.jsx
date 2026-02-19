import { useState } from 'react';
import './SearchUpdated.css';

function SearchUpdated() {
  const [input, setInput] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input && !uploadedFile) return;

    setIsLoading(true);
    const formData = new FormData();
    formData.append('query', input);
    if (uploadedFile) formData.append('file', uploadedFile);

    try {
      const response = await fetch('http://127.0.0.1:5000/fact-check', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error(`Server responded with ${response.status}`);
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Fetch error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadedFile(file);
  };

  const removeFile = () => {
    setUploadedFile(null);
    const fileInput = document.getElementById('file-upload');
    if (fileInput) fileInput.value = '';
  };

  const verdictIcon = (category) => {
    switch (category) {
      case 'true': return '✅';
      case 'false': return '❌';
      case 'mixed': return '⚠️';
      default: return 'ℹ️';
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="search-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a claim or input a file to be fact-checked"
          className="search-input"
          rows="3"
        />
        {uploadedFile && (
          <div className="uploaded-file">
            <span className="file-name">{uploadedFile.name}</span>
            <button type="button" className="remove-file" onClick={removeFile}>✕</button>
          </div>
        )}

        <div className="search-actions">
          <label htmlFor="file-upload" className="icon-button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
            <input id="file-upload" type="file" onChange={handleFileUpload} style={{ display: 'none' }} />
          </label>

          <button type="button" className="icon-button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="16 18 22 12 16 6" />
              <polyline points="8 6 2 12 8 18" />
            </svg>
          </button>

          <button type="button" className="icon-button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            </svg>
          </button>

          <button type="submit" className="submit-button" disabled={isLoading}>
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
      <div className="results-list">
        {results.map((item, index) => {
          const verdict = item.verdict;

          return (
            <div key={index} className="result-card">
              <div className="search-term-header">
                <small>Results for:</small>
                <h4>{item.original_claim}</h4>
              </div>

              {item.fact_checks && item.fact_checks.length > 0 ? (
                <>
                {/*Summary Verdict */}
                  {verdict && (
                    <div className={`verdict-summary verdict-${verdict.category}`}>
                      <div className="verdict-headline">
                        <span className="verdict-icon">
                          {verdictIcon(verdict.category)}
                        </span>
                        <p className="verdict-text">{verdict.summary}</p>
                      </div>

                      {Object.keys(verdict.breakdown).length > 1 && (
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
                  {item.fact_checks.map((claim, i) => (
                    <div key={i} className="claim-match">
                      <p className="db-claim-text">
                        <strong>Match:</strong> {claim.text}
                      </p>
                      {claim.claimReview.map((review, j) => (
                        <div key={j} className="verdict-row">
                          <span className={`rating-badge ${review.ratingCategory || 'unrated'}`}>
                            {review.condensedRating || review.textualRating}
                          </span>
                          <span className="original-rating">
                            ({review.textualRating})
                          </span>
                          <span className="publisher-name">
                            by {review.publisher.name}
                          </span>
                          <a
                            href={review.url}
                            target="_blank"
                            rel="noreferrer"
                            className="view-link"
                          >
                            Source
                          </a>
                        </div>
                      ))}
                    </div>
                  ))}

                  
                </>
              ) : (
                <p className="no-results">
                  No professional fact-checks found for this claim.
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