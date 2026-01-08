# Resume Application Automation

An intelligent system for automating resume-based job applications with AI-powered text generation, form autofill, and GitHub integration.

## Features

- **Resume Parsing**: Extract structured data from PDF and DOCX resume files
- **Resume Normalization**: Transform resume data into ATS-friendly formats
- **Form Schema Extraction**: Automatically extract form fields from job application pages
- **Field Mapping**: Intelligent mapping between resume data and ATS form fields
- **Live Preview Autofill**: Preview form autofill before submission
- **AI Text Generation**: Generate cover letters and personal statements using AI
- **GitHub Integration**: Link GitHub account and select repositories as projects
- **Feature Flags**: Enable/disable features with role-based permissions
- **Structured Logging**: Comprehensive logging with sensitive data protection

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Relational database
- **Alembic**: Database migrations
- **Playwright**: Browser automation for form extraction and autofill
- **OpenAI API**: AI text generation
- **Python-JSON-Logger**: Structured logging

### Frontend
- **Next.js**: React framework
- **Tailwind CSS**: Utility-first CSS framework

## Project Structure

```
InternApplicationAutomation/
├── app/                    # FastAPI application
│   ├── core/              # Core utilities (logging)
│   ├── db/                # Database configuration
│   ├── dependencies/      # FastAPI dependencies
│   ├── middleware/        # Custom middleware
│   ├── models/           # Database models and schemas
│   ├── routers/          # API route handlers
│   └── services/         # Business logic services
├── alembic/              # Database migrations
├── frontend/             # Next.js frontend application
├── tests/                # Test files
├── resume_parser.py      # Resume parsing module
├── resume_normalizer.py   # Resume normalization module
├── ats_field_mapper.py   # ATS field mapping module
├── form_schema_extractor.py  # Form schema extraction
└── requirements.txt       # Python dependencies
```

## Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Playwright (installed via pip)

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key (for AI generation)
- `SECRET_KEY`: Secret key for JWT tokens
- `GITHUB_CLIENT_ID`: GitHub OAuth client ID (optional)
- `GITHUB_CLIENT_SECRET`: GitHub OAuth client secret (optional)
- `LOG_LEVEL`: Logging level (default: INFO)

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your API URL
```

4. Start the development server:
```bash
npm run dev
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Key Modules

### Resume Parser (`resume_parser.py`)
Extracts structured information from PDF and DOCX resume files. Provides a frozen API for stable integration.

### Resume Normalizer (`resume_normalizer.py`)
Maps raw resume data to canonical ATS-friendly representations with role-specific normalization rules.

### ATS Field Mapper (`ats_field_mapper.py`)
Intelligent mapping between ATS form field names and resume schema paths with fuzzy matching and confidence scoring.

### Form Schema Extractor (`form_schema_extractor.py`)
Playwright-based tool for extracting form schemas from web pages with ATS platform detection.

## Feature Flags

The system supports feature flags for:
- **Autofill**: Enable/disable form autofill functionality
- **AI Generation**: Enable/disable AI text generation

Feature flags can be configured globally or per-role through admin endpoints.

## Authentication

The system supports OAuth authentication with:
- Google
- GitHub

All API endpoints (except health check) require authentication.

## Database Migrations

Run migrations:
```bash
alembic upgrade head
```

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

## Testing

Run tests:
```bash
pytest
```

## Logging

The system uses structured JSON logging with:
- Request/response logging
- Failed mapping tracking
- Autofill abort logging
- Sensitive data sanitization

Logs are output to stdout in JSON format and can be configured via `LOG_LEVEL` environment variable.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.

