# AI-Powered Fitness Pal

A multi-agent fitness application powered by LangGraph and LLMs (Claude/GPT-4) that provides personalized health assessments, nutrition planning, recipe suggestions, fitness programming, and daily coaching.

## Features

- **Health Assessment Agent**: Calculate BMI, TDEE, and caloric targets based on user metrics
- **Nutrition Planning Agent**: Generate personalized meal plans with macro distribution
- **Recipe Suggestion Agent**: Conversational recipe matching based on available ingredients
- **Fitness Programming Agent**: Create customized workout programs for various goals
- **Daily Coach Agent**: Provide comprehensive daily schedules with meal timing and workout optimization
- **Orchestrator Agent**: Intelligent routing and multi-agent coordination

## Architecture

The application uses a multi-agent architecture built with LangGraph, where specialized agents collaborate to provide comprehensive fitness guidance. All agents share a common state and communicate through an orchestrator.

## Project Structure

```
fitness-pal/
├── src/
│   ├── agents/          # Agent implementations
│   ├── models/          # Pydantic models and state schemas
│   ├── utils/           # Helper functions and calculations
│   ├── api/             # FastAPI routes
│   ├── database/        # Database models and repositories
│   └── config.py        # Configuration management
├── tests/
│   ├── unit/            # Unit tests for each component
│   ├── integration/     # Integration tests for agent communication
│   └── e2e/             # End-to-end workflow tests
├── frontend/            # Simple web UI
│   ├── static/
│   └── templates/
├── requirements.txt
├── .env.example
├── pytest.ini
└── README.md
```

## Setup

### Prerequisites

- Python 3.10 or higher
- API key for Claude (Anthropic) or OpenAI GPT-4

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fitness-pal
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. Initialize the database:
```bash
alembic upgrade head
```

## Configuration

Edit the `.env` file to configure:

- **LLM Provider**: Choose between `claude` or `openai`
- **API Keys**: Add your Anthropic or OpenAI API key
- **Database**: SQLite database path (default: `./fitness_pal.db`)
- **API Settings**: Host, port, and debug mode

## Running the Application

### Start the API server:

```bash
uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run all tests:
```bash
pytest
```

Run specific test types:
```bash
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/e2e/           # End-to-end tests only
```

Run with coverage report:
```bash
pytest --cov=src --cov-report=html
```

## Usage

### Example: Complete Onboarding Flow

1. Create a user profile
2. Get health assessment (BMI, TDEE, caloric targets)
3. Generate nutrition plan
4. Create workout program
5. Get daily schedule

### API Endpoints

- `POST /api/v1/users` - Create user profile
- `GET /api/v1/users/{user_id}` - Get user profile
- `PUT /api/v1/users/{user_id}` - Update user profile
- `GET /api/v1/users/{user_id}/health` - Get health assessment
- `POST /api/v1/chat` - Chat with agents
- `GET /api/v1/users/{user_id}/meal-plan` - Get current meal plan
- `GET /api/v1/users/{user_id}/workout-plan` - Get workout plan
- `GET /api/v1/users/{user_id}/daily-schedule` - Get daily schedule

## Development

### Adding a New Agent

1. Create agent file in `src/agents/`
2. Define agent tools and prompts
3. Integrate with LangGraph workflow
4. Add unit and integration tests
5. Update orchestrator routing logic

### Code Quality

- Write comprehensive tests (target: 80%+ coverage)
- Follow PEP 8 style guidelines
- Add type hints for all functions
- Document complex logic with comments

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

## Support

[Add support information here]

