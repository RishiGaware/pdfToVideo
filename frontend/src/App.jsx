import React, { useState, useEffect, useRef } from "react";

import "./index.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [videoUrl, setVideoUrl] = useState(null);
  const [error, setError] = useState(null);

  const progressEndRef = useRef(null);

  const resetState = () => {
    setError(null);
    setVideoUrl(null);
    setJobId(null);
    setProgress(0);
  };

  const handleDefaultSOP = async () => {
    resetState();
    try {
      const res = await fetch(`${API_BASE}/process_default`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to start default process");
      const data = await res.json();
      setJobId(data.job_id);
      setStatus("processing");
    } catch (err) {
      setError(err.message || "Engine initialization failed");
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    resetState();

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("File upload failed");
      const data = await res.json();
      setJobId(data.job_id);
      setStatus("processing");
    } catch (err) {
      setError(err.message || "Upload failed");
    }
  };

  useEffect(() => {
    let interval;
    if (jobId && status === "processing") {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/status/${jobId}`);
          if (!res.ok) throw new Error("Polling failed");
          const data = await res.json();

          setProgress(data.progress || 0);
          setMessage(data.message || "Initializing engine...");

          if (data.status === "completed") {
            setStatus("completed");
            setVideoUrl(`${API_BASE}${data.video_url}`);
            clearInterval(interval);
          } else if (data.status === "failed") {
            setStatus("failed");
            setError(
              data.error || "An unknown error occurred during generation.",
            );
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [jobId, status]);

  useEffect(() => {
    if (status === "processing" && progressEndRef.current) {
      progressEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [progress, status]);

  return (
    <div className="container">
      <div className="header">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "15px",
            marginBottom: "10px",
          }}
        >
          <img
            src="/icon.png"
            alt="Doc2Vid Pro Icon"
            style={{ width: "80px", height: "80px", borderRadius: "10px" }}
          />
          <h1 style={{ margin: 0 }}>Doc2Video Pro</h1>
        </div>
        <div className="subtitle">
          Automated Document-to-Training Video Engine
        </div>
      </div>

      {!status || status === "failed" || status === "completed" || status === "processing" ? (
        <div className="dashboard">
          {/* Action Card 1: Default SOP */}
          <div className="action-card">
            <div className="card-icon">📄</div>
            <div className="card-title">Test Example SOP</div>
            <div className="card-desc">
              Generate a training module using the pre-loaded Compressed Air-GAS
              Validation SOP. No upload required.
            </div>
            <button
              className="btn"
              onClick={handleDefaultSOP}
              disabled={status === "processing"}
            >
              {status === "processing" ? (
                <div className="spinner"></div>
              ) : (
                "Generate from Example"
              )}
            </button>
          </div>

          {/* Action Card 2: Custom Upload */}
          <div className="action-card">
            <div className="card-icon">📤</div>
            <div className="card-title">Upload Custom SOP</div>
            <div className="card-desc">
              Transform your own unstructured PDF standard operating procedure
              into an interactive video.
            </div>
            <div className="file-input-wrapper">
              <div className="file-custom">
                {file ? file.name : "Click to select PDF"}
              </div>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setFile(e.target.files[0])}
                disabled={status === "processing"}
              />
            </div>
            <button
              className="btn btn-secondary"
              onClick={handleUpload}
              disabled={!file || status === "processing"}
            >
              {status === "processing" && file ? (
                <div className="spinner"></div>
              ) : (
                "Upload & Generate"
              )}
            </button>
          </div>
        </div>
      ) : null}

      {status === "processing" && (
        <div className="progress-container">
          <div className="message">{message}</div>
          <div className="progress-bar-wrapper">
            <div
              className="progress-bar"
              style={{ width: `${Math.max(progress, 5)}%` }}
            ></div>
          </div>
          <span className="progress-pct">{progress}%</span>
          <div ref={progressEndRef} />
        </div>
      )}

      {error && (
        <div className="error">
          <strong>Engine Failure:</strong> {error}
        </div>
      )}

      {videoUrl && (
        <div className="video-container">
          <h2>Training Module Ready</h2>
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
