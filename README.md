# ViraLearn ContentBot

A comprehensive AI-powered content generation platform that provides text, image, and audio content creation capabilities through a unified API.

## 🚀 Features

- **Multi-Modal Content Generation**: Text, image, and audio content creation
- **LLM Integration**: Powered by Google's Gemini AI models
- **Image Generation**: Google Cloud Vertex AI integration
- **Text-to-Speech**: Google Cloud Text-to-Speech API
- **Database Management**: PostgreSQL with async SQLAlchemy
- **RESTful API**: FastAPI-based backend architecture
- **Workflow Management**: Create and manage content generation workflows

## 🏗️ Architecture

The project follows a modular microservices architecture:

```
src/
├── agents/          # AI agent implementations
├── api/             # API endpoints and routing
├── database/        # Database connection and models
├── models/          # Pydantic schemas and data models
├── services/        # Core business logic services
└── utils/           # Utility functions and helpers
```

### Core Services

1. **LLM Service** (`llm_service.py`) - Text generation using Gemini AI
2. **Image Service** (`image_service.py`) - Image generation via Vertex AI
3. **Audio Service** (`audio_service.py`) - Text-to-speech conversion
4. **Database Service** (`database_service.py`) - Data persistence and retrieval

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL database
- Google Cloud Platform account with enabled APIs:
  - Vertex AI API
  - Text-to-Speech API
  - Generative AI API

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ContentBot
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   
   Configure the following variables in `.env`:
   ```env
   # Database Configuration
   DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/contentbot
   
   # Google Cloud Configuration
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account.json
   GEMINI_API_KEY=your_gemini_api_key
   
   # Google Cloud Project
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_CLOUD_REGION=us-central1
   ```

5. **Set up the database**:
   ```bash
   # Create the database
   createdb contentbot
   
   # Run migrations
   psql -d contentbot -f migrations/001_initial_schema.sql
   ```

6. **Configure Google Cloud credentials**:
   - Create a service account in Google Cloud Console
   - Download the JSON key file
   - Set the path in `GOOGLE_APPLICATION_CREDENTIALS`
   - Enable required APIs (Vertex AI, Text-to-Speech, Generative AI)

## 🚀 Usage

### Running the Application

```bash
# Start the FastAPI server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Testing Services

```bash
# Test all services
python test_services.py

# Test individual components
python test_db_connection.py
python test_env_loading.py
```

## 📊 Service Status

Based on recent testing:

| Service | Status | Notes |
|---------|--------|---------|
| Configuration | ✅ Working | Environment variables loaded correctly |
| Database | ✅ Working | PostgreSQL connection and operations functional |
| LLM Service | ✅ Working | Gemini AI integration operational |
| Utility Functions | ✅ Working | Helper functions working correctly |
| Image Service | ⚠️ Partial | API format issues with PredictRequest.instances |
| Audio Service | ⚠️ Partial | FLAC encoding issues in text-to-speech |

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Yes |
| `GOOGLE_CLOUD_REGION` | GCP region for Vertex AI | Yes |

### Database Schema

The application uses the following main tables:
- `workflows` - Content generation workflow definitions
- `users` - User management (if authentication is implemented)

## 🐛 Known Issues

1. **Image Service**: PredictRequest.instances format needs adjustment for Vertex AI
2. **Audio Service**: FLAC encoding configuration requires refinement
3. **Database Connections**: Occasional connection pool warnings during testing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Development Notes

- The project uses async/await patterns throughout
- SQLAlchemy 2.0+ syntax with async sessions
- Pydantic v2 for data validation
- FastAPI for API framework
- Google Cloud SDK for AI services

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the API documentation at `/docs`
2. Review the test files for usage examples
3. Check the logs for detailed error information

---

**Note**: This is an active development project. Some features may be in beta or require additional configuration.