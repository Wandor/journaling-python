# Jay Journal

A backend journaling platform built using **FastAPI**, **SQLAlchemy**, and **Uvicorn**. It features sentiment analysis, JWT-based authentication, journaling analytics, and supports asynchronous processing with **RabbitMQ** and **Redis**. Database migrations are managed using **Alembic**.

---

## 🚀 Features

- User authentication (JWT access and refresh tokens)
- Journal entry creation and sentiment scoring
- Sentiment analysis via OpenAI
- Weekly and yearly journaling analytics
- OTP-based user verification system
- Caching with Redis
- Async job handling with RabbitMQ
- Fully environment-configurable via `.env`

---

## 📦 Requirements

- Python 3.11+
- PostgreSQL
- Redis
- RabbitMQ

---

## 🔧 Getting Started

### 1. Clone the Repository

git clone https://github.com/Wandor/journaling-python.git


cd journaling-python

### 2. Set Up a Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
### 3. Install Dependencies

pip install -r requirements.txt
### 4. Configure Environment Variables
Create a .env file in the root directory with the following content:

DATABASE_URL="postgresql+asyncpg://postgres:yourpassword@localhost:5432/journaling-python"
JWT_SECRET="your-secret-key"
JWT_EXPIRATION=3600
JWT_REFRESH_EXPIRATION=1440
REFRESH_TOKEN_EXPIRY_DAYS=7
PASSWORD_EXPIRY_DAYS=30
ACCOUNT_LOCK_MAX_COUNT=5
OTP_RESEND_MAX_COUNT=5
OTP_SEND_MAX_HOURS=1
OTP_EXPIRY_MINUTES=5
MAX_NUMBER_OF_REQUESTS=100
OPENAI_API_KEY=your-openai-api-key
SENTIMENT_ANALYSIS='sentiment'

### 5. Prepare the Database
Ensure PostgreSQL is running and the journaling-python database exists. Then run the migrations:

alembic upgrade head

Ensure you have alembic installed and configure alembic.ini by adding your database url to 'sqlalchemy.url ='
### 6. Start Redis and RabbitMQ
Ensure both services are installed and running locally.

Redis default: localhost:6379

RabbitMQ default: localhost:5672

### 7. Run the Application

uvicorn app.main:app --reload --host 127.0.0.1 --port 4000

### 📁 Project Structure

app/
├── api/               # Route definitions
├── core/              # Config and initialization logic
├── db/                # Database models and session handling
├── services/          # Business logic and integrations
├── workers/           # Background consumers (RabbitMQ)
├── utils/             # Helper functions
└── main.py            # Application entry point

### 🛠️ Technologies Used
FastAPI – API framework

SQLAlchemy + AsyncPG – Database ORM with async support

Alembic – Schema migrations

Redis – Caching layer

RabbitMQ – Asynchronous task queue

OpenAI SDK – Sentiment analysis

Uvicorn – ASGI server


