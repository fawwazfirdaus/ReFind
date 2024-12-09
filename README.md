# ReFind

ReFind is an intelligent academic paper reference management system that allows you to upload PDFs, extract references, and ask questions about the paper and its citations using natural language.

## Features

- 📄 PDF Upload & Processing
- 📚 Automatic Reference Extraction
- 🔍 Semantic Search
- 💬 Natural Language Querying
- 🔗 DOI Linking
- 📊 Reference Visualization

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, GROBID, FAISS
- **AI/ML**: OpenAI API (GPT-3.5/4, Ada Embeddings)
- **Infrastructure**: Docker (for GROBID)

## Prerequisites

1. Python 3.8+
2. Node.js 18+
3. Docker Desktop
4. OpenAI API Key

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/refind.git
cd refind
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # Copy and edit with your OpenAI API key
```

3. Start GROBID service:
```bash
docker pull grobid/grobid:0.8.1
docker run -t --rm -p 8070:8070 grobid/grobid:0.8.1
```

4. Start the backend server (in a new terminal):
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

5. Set up the frontend (in a new terminal):
```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- GROBID service: http://localhost:8070

## Project Structure

```
refind/
├── backend/             # FastAPI backend
│   ├── utils/          # Utility modules
│   ├── requirements.txt
│   └── README.md
├── frontend/           # Next.js frontend
│   ├── src/
│   │   ├── app/       # Next.js pages
│   │   └── components/
│   └── package.json
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 