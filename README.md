# SME Reconciliation MVP

A web application for reconciling SME transactions using FastAPI backend and vanilla JavaScript frontend.

## Project Structure

```
sme_recon_mvp/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   └── reconciliation.py
├── frontend/
│   ├── index.html
│   └── app.js
└── uploads/
```

## Setup

1. Clone the repository
```bash
git clone <repository-url>
cd sme_recon_mvp
```

2. Create and activate virtual environment
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies
```bash
pip install fastapi[all] pandas python-multipart
```

4. Run the backend server
```bash
uvicorn backend.main:app --reload
```

5. Serve the frontend
```bash
cd frontend
python -m http.server 8000
```

## Features

- File upload functionality
- Excel file processing
- Transaction reconciliation
- Cross-origin resource sharing (CORS) enabled
