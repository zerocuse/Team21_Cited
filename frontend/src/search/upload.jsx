import React, { useRef, useState } from "react";
import "./upload.css";

export default function UploadDoc() {
  const fileInputRef = useRef(null);
  const [fileName, setFileName] = useState("");
  const [extractedText, setExtractedText] = useState(""); // State to hold the text

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
        body: formData,
      });

      const data = await res.json();
      
      if (data.extractedText) {
        setExtractedText(data.extractedText);
      }
    } catch (err) {
      console.error("Upload failed:", err);
    }
  };

  return (
    <div className="upload-container">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept=".pdf,.docx,.txt"
      />

      <button type="button" className="search-upload-btn" onClick={handleUploadClick}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      </button>
    </div>
  );
}