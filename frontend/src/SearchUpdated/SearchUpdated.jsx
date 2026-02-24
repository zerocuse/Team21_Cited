import { useState, useRef } from 'react';
import './SearchUpdated.css';

function SearchUpdated() {
  const [input, setInput] = useState('');
  const [files, setFiles] = useState([]);
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Submitted:', input, files);
  };

  const FILE_LIMIT = 1;

  const handleFileUpload = (e) => {
    const newFiles = Array.from(e.target.files);
    setFiles(prev => {
      const combined = [...prev, ...newFiles];
      return combined.slice(0, FILE_LIMIT);
    });
    e.target.value = '';
  };

  const removeFile = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const getFilePreview = (file) => {
    if (file.type.startsWith('image/')) return URL.createObjectURL(file);
    return null;
  };

  const getFileIcon = (file) => {
    if (file.type.startsWith('image/')) return null;
    if (file.type.includes('pdf')) return '📄';
    if (file.type.includes('word') || file.name.endsWith('.docx')) return '📝';
    if (file.type.includes('sheet') || file.name.endsWith('.xlsx')) return '📊';
    return '📎';
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="search-box">

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

        {/* Text input */}
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a claim or input a file to be fact-checked"
          className="search-input"
          rows="3"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); }
          }}
        />

        {/* Actions */}
        <div className="search-actions">
          <label htmlFor="file-upload" className={`icon-button${files.length >= FILE_LIMIT ? ' icon-button--disabled' : ''}`} title={files.length >= FILE_LIMIT ? 'File limit reached' : 'Attach file'}>
            <img src="./src/assets/attachment-icon.svg" alt="file-upload" className="file-upload-icon"/>
            <input
              id="file-upload"
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              disabled={files.length >= FILE_LIMIT}
              style={{ display: 'none' }}
            />
          </label>
          <button type="submit" className="submit-button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="19" x2="12" y2="5"/>
              <polyline points="5 12 12 5 19 12"/>
            </svg>
          </button>
        </div>
      </div>
    </form>
  );
}

export default SearchUpdated;