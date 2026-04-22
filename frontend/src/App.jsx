import React, { useState, useEffect } from "react";

import "./index.css";

const API_BASE = "http://localhost:8000";

function App() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [videoUrl, setVideoUrl] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    setError(null);
    setVideoUrl(null);
    setJobId(null);
    setProgress(0);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setJobId(data.job_id);
      setStatus("processing");
    } catch (err) {
      setError("Upload failed");
    }
  };

  useEffect(() => {
    let interval;
    if (jobId && status === "processing") {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/status/${jobId}`);
          const data = await res.json();
          setProgress(data.progress || 0);
          setMessage(data.message || "");
          if (data.status === "completed") {
            setStatus("completed");
            setVideoUrl(`${API_BASE}${data.video_url}`);
            clearInterval(interval);
          } else if (data.status === "failed") {
            setStatus("failed");
            setError(data.error);
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [jobId, status]);

  return (
    <div className="container">
      <h1>Doc Trainer</h1>
      <p>Automated Document-to-Training Video Engine</p>

      <div className="upload-box">
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button
          onClick={handleUpload}
          disabled={!file || status === "processing"}
        >
          {status === "processing"
            ? "Processing..."
            : "Upload & Generate Training"}
        </button>
      </div>

      {status === "processing" && (
        <div className="progress-container">
          <div className="message">{message}</div>
          <div className="progress-bar-wrapper">
            <div
              className="progress-bar"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <span>{progress}%</span>
        </div>
      )}

      {error && <p className="error">{error}</p>}

      {videoUrl && (
        <div className="video-container">
          <h2>Result:</h2>
          <video src={videoUrl} controls autoPlay width="100%" />
          <a href={videoUrl} download className="download-btn">
            Download Video
          </a>
        </div>
      )}
    </div>
  );
}

export default App;
