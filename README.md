# ViraLearn ContentBot

A sophisticated multi-agent content generation system powered by LangGraph, supporting multiple LLM providers and multimedia content creation.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git
- API keys for your chosen LLM providers

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ContentBot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   Edit `.env` file with your API keys (see Configuration section below).

5. **Run the application**
   
   **Option A: Streamlit UI**
   ```bash
   streamlit run streamlit_app.py
   ```
   
   **Option B: FastAPI Server**
   ```bash
   python src/api/main.py
   ```
   
   **Option C: Direct Python**
   ```bash
   python src/main.py
   ```

## 📋 Project Overview

ViraLearn ContentBot is a multi-agent system that generates high-quality content across multiple formats:

- **Text Content**: Blog posts, articles, social media content
- **Image Generation**: AI-powered visual content creation
- **Audio Processing**: Voice synthesis and audio content
- **Cross-Platform**: Optimized content for different platforms
- **Brand Voice**: Consistent brand messaging across all content

## 📁 Directory Structure

```
ContentBot/
├── src/                    # Main source code
│   ├── agents/            # Multi-agent system components
│   ├── api/               # FastAPI application
│   ├── core/              # Core workflow engine
│   ├── models/            # Data models and schemas
│   ├── services/          # External service integrations
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── tests/                 # Test suite
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── migrations/            # Database migrations
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # Container definition
├── requirements.txt      # Python dependencies
└── streamlit_app.py      # Streamlit UI entry point
```

## ⚙️ Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following:

#### LLM Providers
```bash
# Google Gemini
GOOGLE_API_KEY=your_google_api_key_here

# Mistral AI
MISTRAL_API_KEY=your_mistral_api_key_here

# Hugging Face
HUGGINGFACE_API_TOKEN=hf_your_token_here
```

#### Google Cloud Services
```bash
# For Imagen and Audio services
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

#### Database Configuration
```bash
# PostgreSQL (Production)
DATABASE_URL=postgresql://user:password@localhost:5432/contentbot

# SQLite (Development)
DATABASE_URL=sqlite:///./contentbot.db

# Redis (Caching)
REDIS_URL=redis://localhost:6379/0
```

### API Key Setup Guide

#### Google Gemini API
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env` as `GOOGLE_API_KEY`

#### Mistral AI
1. Sign up at [Mistral AI](https://console.mistral.ai/)
2. Generate API key in dashboard
3. Add to `.env` as `MISTRAL_API_KEY`

#### Google Cloud (Imagen & Audio)
1. Create project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Imagen and Text-to-Speech APIs
3. Create service account and download JSON key
4. Set `GOOGLE_APPLICATION_CREDENTIALS` path

#### Hugging Face
1. Create account at [Hugging Face](https://huggingface.co/)
2. Generate access token in settings
3. Add to `.env` as `HUGGINGFACE_API_TOKEN`

## 🐳 Docker Usage

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🗄️ Database Setup

### PostgreSQL (Recommended for Production)
```bash
# Using Docker
docker-compose up postgres -d

# Manual setup
createdb contentbot
psql contentbot < migrations/001_initial_schema.sql
```

### SQLite (Development)
No setup required - database file created automatically.

## 🔄 LLM Provider Switching

The system supports multiple LLM providers. Configure in your `.env`:

```bash
# Primary LLM provider
PRIMARY_LLM_PROVIDER=gemini  # Options: gemini, mistral, huggingface

# Fallback provider
FALLBACK_LLM_PROVIDER=mistral
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Test with coverage
pytest --cov=src tests/
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **API Key Issues**
   - Verify API keys are correctly set in `.env`
   - Check API key permissions and quotas
   - Ensure service accounts have proper roles

3. **Database Connection**
   ```bash
   # Test database connection
   python -c "from src.database.service import DatabaseService; print('DB OK')"
   ```

4. **Port Conflicts**
   - Streamlit default: `http://localhost:8501`
   - FastAPI default: `http://localhost:8000`
   - Modify ports in configuration if needed

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables for all sensitive data
- Regularly rotate API keys
- Enable API key restrictions where possible
- Use service accounts with minimal required permissions

## 📚 Key Entry Points

- **Streamlit UI**: `streamlit_app.py` - Interactive web interface
- **FastAPI Server**: `src/api/main.py` - REST API server
- **Core Engine**: `src/main.py` - Direct Python execution
- **Workflow Engine**: `src/core/workflow_engine.py` - Multi-agent orchestration

## 🛠️ Scripts

- `scripts/setup.sh` - Initial setup automation
- `scripts/test.sh` - Test execution
- `scripts/deploy.sh` - Deployment automation

## 📖 Documentation

- `docs/mistral_setup_guide.md` - Detailed Mistral AI setup
- `ARCHITECTURE.md` - System architecture overview
- API documentation available at `/docs` when running FastAPI

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in the application
3. Consult the documentation in `docs/`
4. Create an issue in the repository

## 🚀 Getting Started Checklist

- [ ] Clone repository
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Set up API keys in `.env`
- [ ] Test database connection
- [ ] Run application
- [ ] Verify content generation works

You're ready to start generating amazing content with ViraLearn ContentBot!