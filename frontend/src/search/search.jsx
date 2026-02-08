import React, { useRef, useState, useEffect } from "react";
import "./search.css";
import UploadDoc from "./upload";


export default function Search() {
  const fileInputRef = useRef(null);

  const [fileName, setFileName] = useState("");
  const [query, setQuery] = useState("");
  const [news, setNews] = useState([]);
  const [results, setResults] = useState([]);


  useEffect(() => {
    fetch("http://127.0.0.1:5000/api/newsdata")
      .then((res) => res.json())
      .then((data) => setNews(data))
      .catch((err) => console.error("Fetch error:", err));
  }, []);

  // Filter news
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const filtered = news.filter((item) =>
      item.title?.toLowerCase().includes(query.toLowerCase()) ||
      item.description?.toLowerCase().includes(query.toLowerCase())
    );

    setResults(filtered);
  }, [query, news]);

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  setFileName(file.name);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("http://127.0.0.1:5000/api/upload", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    console.log("Uploaded file processed:", data);
  } catch (err) {
    console.error("Upload failed:", err);
  }
};

  const clearSearch = () => {
    setFileName("");
    setQuery("");
    setResults([]);
  };

  return (
    <div className="search-container">
      <div className="search-input-group">
        <svg className="search-icon" width="18" height="18" viewBox="0 0 20 20" fill="none">
          <path
            d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM18 18l-4.35-4.35"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>

        <input
          type="text"
          className="search-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={fileName ? `File: ${fileName}` : "Search or upload document..."}
        />

        <UploadDoc onUploadClick={handleUploadClick}/>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: "none" }}
          accept=".pdf,.doc,.docx,.txt"
        />

        <button className="search-clear" onClick={clearSearch}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor">
            <path
              d="M12 4L4 12M4 4l8 8"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>

      {query.trim() && (
  <div className="search-dropdown">
    {results.length === 0 ? (
      <div className="search-empty">No results found</div>
    ) : (
      results.slice(0, 6).map((item, index) => (
        <div key={index} className="search-result">
          <div className="search-result-title">
            {item.title}
          </div>
          <div className="search-result-description">
            {item.description}
          </div>
        </div>
      ))
    )}
  </div>
      )}
    </div>
  );
}
