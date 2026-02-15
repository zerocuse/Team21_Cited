import { useState } from 'react';
import './SearchUpdated.css';

function SearchUpdated() {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Submitted:', input);
    // Add your fact-checking logic here
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    console.log('File uploaded:', file);
    // Handle file upload
  };

  return (
    <form onSubmit={handleSubmit} className="search-container">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a claim or input a file to be fact-checked"
        className="search-input"
        rows="3"
      />
      
      <div className="search-actions">
        <label htmlFor="file-upload" className="icon-button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
          <input 
            id="file-upload" 
            type="file" 
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </label>

        <button type="button" className="icon-button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="16 18 22 12 16 6"/>
            <polyline points="8 6 2 12 8 18"/>
          </svg>
        </button>

        <button type="button" className="icon-button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          </svg>
        </button>

        <button type="submit" className="submit-button">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="19" x2="12" y2="5"/>
            <polyline points="5 12 12 5 19 12"/>
          </svg>
        </button>
      </div>
    </form>
  );
}

export default SearchUpdated;