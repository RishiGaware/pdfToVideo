# Doc2Video Pro

An AI-powered, full-stack application that transforms complex, unstructured PDF documents—specifically Standard Operating Procedures (SOPs)—into interactive, professional, narrated training videos. 

> [!CAUTION]
> **Format Dependency Notice:** 
> The document parsing and structural extraction engine inside this project is currently strictly tuned to process a *specific* SOP tabular format (provided as a sample in `backend/temp/16. Validation SOP for Compressed Air-GAS Revision.03 130219 (1).pdf`). If you intend to use this engine with entirely different document layouts or different manufacturer SOP headers/footers, you will need to customize the extraction zones and noise patterns in `backend/app/services/utils.py` and `analyzer.py` to match your specific requirements.

## 🚀 Use Case

Traditional onboarding and compliance training often rely on employees reading dense, multi-page PDF documents. **Doc2Video Pro** solves this by instantly converting standard text-heavy documents into engaging, automated video modules.

**Ideal for:**
- **Corporate Training**: Instantly convert HR manuals into video walkthroughs.
- **Compliance & Quality Assurance**: Transform pharmaceutical SOPs, GMP guidelines, and safety manuals into easily digestible narrated slides.
- **Educational E-Learning**: Convert lecture notes and complex textbooks into engaging audiovisual study guides.

## ✨ Key Features

- **Advanced Document Segmentation**: Intelligently parses PDFs and detects topic boundaries. It automatically filters out document noise (like repeating SOP page headers, footers, page numbers, and dates).
- **Table Preservation & Rendering**: Unlike basic text extractors, this engine uses computer vision to detect, extract, and accurately render complex tabular data directly into the video frames using professional formatting.
- **LLM Content Summarization**: Leverages local/free-tier advanced language models (Ollama/Llama/Mistral) to condense verbose paragraphs into concise, punchy bullet points ideal for presentations.
- **High-Quality Voice Narration**: Integrated with Microsoft Edge-TTS (Text-to-Speech) to provide enterprise-grade, realistic neural voice narration for the generated bullet points—without requiring paid API keys.
- **Intelligent Storyboarding**: Automatically synchronizes audio durations with visual slides, splits tables that are too vertical over multiple slides, and composites professional frames using Python's `PIL`.
- **Premium Frontend Dashboard**: A sleek, dark-mode, glassmorphism React interface that allows users to instantly process a default example SOP or upload their own custom documents. Multi-threaded status polling provides real-time progress updates.

## 📁 Project Architecture

```text
pdfToVideo/
├── backend/                  # FastAPI Backend (Python)
│   ├── app/
│   │   ├── core/             # AutomatedTrainingEngine orchestration
│   │   └── services/         # Extraction, Segmenter, Cleaner, Analyzer, Audio, TTS, Renderer
│   ├── outputs/              # Compiled MP4 videos and temporary frame generation
│   ├── temp/                 # Default testing SOPs and uploaded PDF buffering
│   └── main.py               # REST API Entry Point
├── frontend/                 # React Frontend (Vite)
│   ├── src/                  
│   │   ├── App.jsx           # Premium Dual-Action Dashboard UI
│   │   └── index.css         # Glassmorphism & modern design system
│   └── package.json          
└── README.md                 
```

## 🛠️ Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- [FFmpeg](https://ffmpeg.org/) installed and added to your system PATH (Required for video frame compositing and audio merging).

### 1. Setup Backend
The backend utilizes FastAPI to handle asynchronous file processing and TTS generation.

```bash
cd backend
python -m venv venv

# Activate Virtual Environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Start the FastApi Server
python main.py
```

### 2. Setup Frontend
The frontend features a modern Vite + React configuration.

```bash
cd frontend
npm install

# Start the Vite Development Server
npm run dev
```

## 🎮 How to Use

1. **Launch the Interface**: Navigate to `http://localhost:5173` in your browser.
2. **Choose a Pathway**:
   - **Test Example SOP**: Click this button to run a demonstration. The backend will automatically process the system's default `Validation SOP for Compressed Air-GAS.pdf` loaded in the `/temp` directory.
   - **Upload Custom SOP**: Click the file picker to upload your own PDF document and click "Upload & Generate".
3. **Wait & Watch**: The real-time progress bar will update as the system extracts tables, summarizes text, generates voice narration, and renders frames.
4. **Download**: Once processing is complete, the final training module will appear in the integrated video player. Use the "Download Video" button to save your `.mp4`.

## 📜 License
MIT
