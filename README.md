# Beam Health Backend

FastAPI backend for audio transcription using OpenAI.

## Setup with uv

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create a virtual environment and install dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

   Or use uv's sync command:
   ```bash
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Run the server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## Alternative: Using the run script

```bash
./run.sh
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required if using local backend)

