# SME Reconciliation MVP

A comprehensive web application for reconciling SME (Small and Medium Enterprise) transactions between GSTR2B and Tally data using FastAPI backend and vanilla JavaScript frontend.

## 🚀 Features

### ✅ Core Functionality (8/10 Complete)
- **Perfect Reconciliation Algorithm**: Achieves 1.0 match scores for exact matches
- **Advanced Scoring System**: 65% reference + 25% amount + 8% date + 2% vendor matching
- **Multi-Format Support**: CSV and Excel file processing with auto-detection
- **Comprehensive Field Mapping**: All major GSTR2B and Tally fields included
- **Enhanced Export Capabilities**: Reconciled transactions + separate unmatched reports
- **Color-Coded Visualization**: GSTR2B (Blue), Tally (Purple), Matches (Green)
- **Advanced Analytics Dashboard**: Detailed metrics and match statistics
- **Confidence-Based Filtering**: High (≥95%), Medium (85-95%), Low (<85%)

### 🔄 In Progress
- **Database Integration**: SQLite for reconciliation history and audit trails
- **Testing & Deployment**: Comprehensive test suite and production deployment

## 📊 Project Structure

```
sme_recon_mvp/
├── backend/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI application
│   ├── simple_main.py       # Simplified version for testing
│   ├── database.py          # Database operations
│   ├── reconciliation_manager.py
│   └── reconciliation.py    # Core reconciliation logic
├── frontend/
│   ├── index.html           # Main web interface
│   ├── app.js              # Enhanced JavaScript with all features
│   ├── debug-*.html        # Debug and testing pages
│   └── debug-app.js        # Simplified debugging version
├── uploads/                 # Sample data and uploaded files
├── refrences/              # Project documentation
├── check_server.py         # Server health check utility
└── reconciliation.db       # SQLite database (auto-created)
```

## 🛠️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/amajor13/sme_recon_mvp.git
cd sme_recon_mvp
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the application

#### Backend Server (Port 8000)
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

#### Frontend Server (Port 3000)
```bash
cd frontend
python -m http.server 3000
```

### 5. Access the application
- **Main Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000

## 🎯 Usage

1. **Upload Files**: Select GSTR2B and Tally files (CSV or Excel format)
2. **View Results**: See reconciled transactions with confidence scores
3. **Filter Data**: Use confidence filters (High/Medium/Low/All)
4. **Export Reports**: 
   - Complete reconciliation report
   - Unmatched GSTR2B transactions
   - Unmatched Tally transactions
   - Combined unmatched report
5. **Analyze Metrics**: Check reconciliation statistics and match rates

## 📈 Match Quality Indicators

- **Perfect Matches**: 1.0 score (100% confidence)
- **High Confidence**: ≥0.95 (Perfect/near-perfect matches)
- **Medium Confidence**: 0.85-0.95 (Good matches with minor differences)
- **Low Confidence**: <0.85 (Possible matches requiring review)

## 🎨 Color Coding

- **GSTR2B Data**: Blue theme (#2196F3)
- **Tally Data**: Purple theme (#9C27B0)
- **Match Information**: Green theme (#4CAF50)
- **Differences**: Orange theme (#FF9800)

## 🔧 Technical Features

- **Smart Data Processing**: Handles multiple encodings and delimiters
- **Robust Error Handling**: Comprehensive validation and user feedback
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Processing**: Live updates during file processing
- **Detailed Logging**: Full audit trail for debugging and compliance

## 📝 Sample Data

The `uploads/` folder contains sample GSTR2B and Tally files for testing:
- `gstr2b_gstr2b_sample.csv`
- `tally_tally_sample.csv`

## 🚀 Development Status

| Feature | Status | Progress |
|---------|--------|----------|
| Core Reconciliation | ✅ Complete | 100% |
| File Processing | ✅ Complete | 100% |
| Frontend Interface | ✅ Complete | 100% |
| Advanced Reporting | ✅ Complete | 100% |
| Export Functionality | ✅ Complete | 100% |
| Enhanced UI/UX | ✅ Complete | 100% |
| Color Coding | ✅ Complete | 100% |
| Advanced Features | ✅ Complete | 100% |
| Database Integration | 🔄 In Progress | 0% |
| Testing & Deployment | 🔄 Planned | 0% |

**Overall Progress: 80% Complete (8/10 major features)**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and support, please check:
1. Server health: `python check_server.py`
2. Debug pages: http://localhost:3000/debug-index.html
3. API documentation: http://localhost:8000/docs
