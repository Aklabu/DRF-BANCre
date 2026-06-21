# BANCre Backend API

BANCre is a comprehensive commercial real estate (CRE) financing platform designed to connect **Sponsors** (property owners/developers seeking financing) with **Lenders** (financial institutions providing loan quotes). The backend is built using **Django 6.0**, **Django REST Framework (DRF)**, **Celery**, **Redis**, and a custom **AI/RAG (Retrieval-Augmented Generation)** underwriting pipeline.

---

## Key Features

### 1. User Authentication & Security
- **Role-Based Profiles:** Support for three customer categories: `Sponsor`, `Lender`, and `Broker`.
- **JWT Authentication:** Secure stateless session management using `djangorestframework-simplejwt`.
- **2FA OTP Verification:** Two-factor authorization codes (`signup`, `login_2fa`, `forgot_password`) sent via custom email triggers.
- **Secure Password Reset:** Verification sessions for resetting passwords securely.

### 2. Commercial Property Profiles
- **Metadata Management:** Store property coordinates (Latitude/Longitude), dimensions (Rentable Area), year built/renovated, units count, parking spaces, and occupancy rates.
- **Document Store:** Support for multi-format uploads (PDF, DOCX, XLSX, PPTX, Images) mapping directly to properties.

### 3. AI-Powered Offering Memorandums (OM)
- **Automatic Multi-Section OM Generation:** Background tasks that extract information from uploaded documents and property data to compile a 14-section offering memorandum (Executive Summary, Property Overview, Highlights, Area/Market Overviews, Financial Analysis, Sales/Lease Comparables, etc.).
- **Interactive Editor:** Features an Editor Mode (allowing granular text modifications and section image uploads) and a clean Preview Mode for presentation.

### 4. Dual-Engine AI Chatbots
- **General Platform Helper:** A conversational agent that acts as a CRE expert and guides users step-by-step through the platform capabilities using OpenAI's `gpt-4`.
- **Property Document Chatbot (RAG):** Custom retrieval pipeline using `sentence-transformers` (`all-MiniLM-L6-v2`) and **FAISS** (Facebook AI Similarity Search). Lenders can ask questions and get concise answers grounded *strictly* in the property documents using `gpt-4o-mini`.

### 5. Loan Pipeline & Analytics
- **Requests & Quotes:** Sponsors submit loan requests (Amount, Term, LTV). Lenders review and submit structured quotes detailing debt structures, rates, LTV bounds, reserves, fees, collateral, and recourse conditions.
- **Side-by-Side Comparison:** Comparison utility identifying the best interest rates and highest LTV bounds automatically.
- **Dashboards:** Metrics view custom-tailored for Sponsors (total portfolio value, document counts, quotes received) and Lenders (quotes submitted, win rates, active marketplace requests).

### 6. Modernized Admin Console
- Customized with the **Django Unfold** theme, adding a beautiful Tailwind CSS-based interface, dashboard icons, custom sidebar navigation grouping, and real-time database search filters.

---

## Tech Stack

- **Core Framework:** Django 6.0 & Django REST Framework (DRF)
- **Database:** SQLite (local development), support for PostgreSQL (via `psycopg2-binary`)
- **Task Queue & Caching:** Celery (background jobs) & Redis (broker/backend cache)
- **AI Stack:** OpenAI API (`gpt-4`, `gpt-4o-mini`), Sentence-Transformers (`all-MiniLM-L6-v2`), FAISS (CPU-based Vector store)
- **Document Parsing:** pdfplumber, pdfminer.six, python-docx, pypdfium2
- **Admin Interface:** Django-Unfold

---

## Project Structure

```text
BANCre/
├── accounts/            # User profiles, custom user model, JWT Auth, and OTP utilities
├── chatbot/             # Core platform assistant agent models and endpoints
├── config/              # Django settings, root routing URLs, and Celery app instantiation
├── dashboard/           # Analytics views for lenders and sponsors
├── loans/               # Loan request and quote submission pipeline logic
├── memorandums/         # OM generation orchestration, RAG embeddings, and extractors
├── notifications/       # Multi-event notifications and user preference handlers
├── properties/          # Property metrics, document uploads, and property-specific RAG chatbot engine
├── utils/               # Custom global exceptions handler and standardized API response formats
├── manage.py            # Django CLI entrypoint
├── db.sqlite3           # Local development database
├── requirements.txt     # Python dependencies
└── .env                 # Environment secrets template
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Redis Server (listening on default port `6379`)

### 1. Clone the repository and navigate to the project directory
```bash
git clone <repository-url>
cd BANCre
```

### 2. Set up virtual environment
```bash
python -m venv venv
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install requirements
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the root directory and add the following keys (based on `.env` example):
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:4000
CORS_ALLOW_CREDENTIALS=True

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Redis & Celery
REDIS_URL=redis://localhost:6379/0

# SMTP/Email configurations for OTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Start Services

To run the complete platform locally, run the following commands:

#### Start Redis (Terminal 1)
```bash
redis-server
```

#### Start Celery Worker (Terminal 2)
```bash
# On Windows:
celery -A config worker --pool=solo --loglevel=info
# On macOS/Linux:
celery -A config worker --loglevel=info
```

#### Start Django Development Server (Terminal 3)
```bash
python manage.py runserver
```

---

## API Endpoints

The API is structured under the prefix `/api/`. All endpoints except signup/login require a valid JWT header (`Authorization: Bearer <your_token>`).

| Module | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Accounts** | `/api/accounts/signup/` | POST | Registers a new user (`Sponsor`/`Lender`) & sends signup OTP |
| | `/api/accounts/verify-otp/` | POST | Verifies OTP code for signup/login/2FA activation |
| | `/api/accounts/login/` | POST | Logs in user, returns access/refresh tokens (or prompts 2FA) |
| **Properties** | `/api/properties/` | GET/POST | Lists properties or adds a new property record |
| | `/api/properties/<id>/documents/` | POST | Uploads files (PDF, DOCX, etc.) associated with property |
| **Memorandums**| `/api/memorandums/generate/` | POST | Triggers background Celery task to generate offering memorandum |
| | `/api/memorandums/<id>/` | GET/PUT | Gets details or updates section text of the memorandum |
| **Loans** | `/api/loans/requests/` | GET/POST | Handles loan request postings visible to lenders |
| | `/api/loans/quotes/` | POST | Lenders submit quote details mapping back to requests |
| **Chatbot** | `/api/chatbot/chat/` | POST | Sends message to the general BANCre user-assistant |
| | `/api/properties/<id>/chat/` | POST | Asks property chatbot questions retrieved from documents |