# Setup Guide

## Initial Setup Steps

### 1. Create Your Environment File

Since `.env` files should not be tracked in version control, you need to create your own:

```bash
# Copy the template below to create your .env file
```

Create a file named `.env` in the root directory with the following content:

```
# LLM Configuration
LLM_PROVIDER=claude  # claude or openai
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./fitness_pal.db

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

**Important**: Replace `your_key_here` with your actual API keys:
- For Claude: Get your key from https://console.anthropic.com/
- For OpenAI: Get your key from https://platform.openai.com/

### 2. Install Dependencies

Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

Test that the configuration loads correctly:

```bash
python -c "from src.config import settings; print('Configuration loaded successfully!')"
```

### 4. Next Steps

You're now ready to proceed with the implementation phases:

- **Phase 1**: Core Calculation Utilities
- **Phase 2**: State Schema & Database
- **Phase 3**: Health Assessment Agent
- And so on...

Refer to the main README.md for full project documentation.

## Troubleshooting

### Missing API Key Error

If you see: `Warning: ANTHROPIC_API_KEY is required when using Claude`

Make sure you:
1. Created the `.env` file in the root directory
2. Added your actual API key (not `your_key_here`)
3. Set `LLM_PROVIDER=claude` if using Claude, or `openai` for OpenAI

### Import Errors

If you get module import errors:
1. Ensure your virtual environment is activated
2. Run `pip install -r requirements.txt` again
3. Check that you're in the project root directory

