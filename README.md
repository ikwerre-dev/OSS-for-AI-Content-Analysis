# Granite 4.0 350M Flask API

Flask API serving the sam860/granite-4.0-350m model.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

## Usage

```bash
# Generate text
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?", "max_length": 100, "temperature": 0.7}'

# Health check
curl http://localhost:5000/health
```
