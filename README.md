# GST Fraud Detection System (GST Shield)

An Intelligent GST Fraud Pattern Detection System designed to identify anomalies, evaluate risk, and visualize potential fraud in GST invoices using Rule-based validation and Machine Learning (Isolation Forest).

## 🚀 Features

- **Real-time Dashboard**: Overview of total invoices, fraud percentage, and risk distribution.
- **Anomaly Detection**: Using Isolation Forest algorithm to identify outliers in invoice data.
- **Rule Engine**: Customizable rules for validating GSTINs, amounts, and tax rates.
- **Risk Scoring**: Intelligent risk evaluation (High, Medium, Low) for every invoice.
- **Invoice Management**: Visual list of invoices with detailed risk analysis.
- **Data Generation**: Integrated sample data generator for testing and demonstration.

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI for high-performance Async API.
- **ML Engine**: Scikit-learn (Isolation Forest) for anomaly detection.
- **Rule Engine**: Logic-based validation layer.
- **Database**: SQLite (SQLAlchemy) for persistence.

### Frontend (Next.js)
- **Framework**: Next.js 15 (App Router).
- **Styling**: Tailwind CSS & Lucide Icons.
- **Visuals**: Recharts for data visualization.
- **Theme**: Premium dark-mode UI with glassmorphism effects.

## 🗄️ Database Schema

```mermaid
erDiagram
    INVOICE ||--|| ENGINEERED_FEATURE : "has"
    INVOICE ||--|| FRAUD_ANALYSIS : "analyzed_by"
    
    INVOICE {
        string invoice_id
        string seller_gstin
        string buyer_gstin
        float invoice_amount
        datetime invoice_date
    }
    
    ENGINEERED_FEATURE {
        float tax_ratio
        float avg_seller_invoice
        float deviation_from_avg
        float seller_risk_history
    }
    
    FRAUD_ANALYSIS {
        float rule_score
        float ml_score
        string risk_level
        datetime analyzed_at
    }
```

## 📊 Project Structure & Data Flow

```mermaid
graph TD
    subgraph "Frontend (Next.js)"
        UI[Dashboard UI] --> Actions[User Actions / Hooks]
        Actions --> API_Call[Fetch / Axios]
    end

    subgraph "Backend (FastAPI)"
        API_Call --> Router[API Endpoints]
        Router --> RuleEngine[Rule Engine]
        Router --> MLEngine[ML Anomaly Detector]
        RuleEngine --> Scorer[Risk Scorer]
        MLEngine --> Scorer
        Scorer --> DB[(SQLite Database)]
        DB --> Router
    end

    Router --> UI
```

## 🛠️ Setup Instructions

### Backend
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## 📬 Contact

[Subhajit Das](https://github.com/Subhajit-Das-1)
