# AI-Powered Security & Code Analysis API

Flask API with queue system for Dockerfile reviews, code analysis, phishing detection, and web scraping using the Qwen2.5-Coder-0.5B-Instruct model.

## Features

- **Dockerfile Review**: Analyze build stages, security issues, and estimate build time
- **Code Review**: Quality scoring, issue detection, and best practice recommendations
- **Phishing Detection**: AI-powered analysis of URLs and content for phishing indicators
- **Web Scraping**: Automated scraping with Playwright and AI-powered content analysis
- **Queue System**: Async task processing with unique task IDs
- **JSON-Only Responses**: Clean, structured output for easy integration

## Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Run the Server

```bash
python3 app.py
```

Server runs on `http://localhost:3500`

## API Endpoints

### Health Check

```bash
curl http://localhost:3500/health
```

### Dockerfile Review

Queue a Dockerfile analysis:

```bash
curl -X POST http://localhost:3500/queue/dockerfile-review \
  -H "Content-Type: application/json" \
  -d '{
    "dockerfile": "FROM node:18\nWORKDIR /app\nCOPY . .\nRUN npm install\nEXPOSE 3000\nCMD [\"npm\", \"start\"]"
  }'
```

Response:
```json
{
  "task_id": "abc-123-def",
  "status": "queued"
}
```

### Code Review

Analyze code quality:

```bash
curl -X POST http://localhost:3500/queue/code-review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "function add(a,b){return a+b}",
    "language": "javascript"
  }'
```

### Phishing Check

Detect phishing attempts:

```bash
curl -X POST http://localhost:3500/queue/phishing-check \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "content": "Urgent! Verify your account now!"
  }'
```

### Web Scraping

Scrape and analyze a website:

```bash
curl -X POST http://localhost:3500/queue/web-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```

### Check Task Status

Get task status and results:

```bash
curl http://localhost:3500/queue/status/abc-123-def
```

Response (completed):
```json
{
  "id": "abc-123-def",
  "type": "dockerfile_review",
  "status": "completed",
  "created_at": "2026-03-03T10:30:00",
  "started_at": "2026-03-03T10:30:01",
  "completed_at": "2026-03-03T10:30:15",
  "result": {
    "stages": [
      {"name": "build", "purpose": "Install dependencies"}
    ],
    "review": [
      {
        "severity": "medium",
        "issue": "Running as root user",
        "suggestion": "Add USER directive"
      }
    ],
    "estimated_build_time": "2-5 minutes",
    "security_score": 75
  }
}
```

### List All Tasks

```bash
curl http://localhost:3500/queue/list
```

## Response Formats

### Dockerfile Review
```json
{
  "stages": [
    {"name": "builder", "purpose": "Compile application"}
  ],
  "review": [
    {
      "severity": "high|medium|low",
      "issue": "Description of issue",
      "suggestion": "How to fix"
    }
  ],
  "estimated_build_time": "X-Y minutes",
  "security_score": 85
}
```

### Code Review
```json
{
  "quality_score": 85,
  "issues": [
    {
      "severity": "medium",
      "line": 10,
      "issue": "Missing error handling",
      "fix": "Add try-catch block"
    }
  ],
  "best_practices": ["Use const instead of var"],
  "complexity": "medium"
}
```

### Phishing Check
```json
{
  "is_phishing": true,
  "confidence": 95,
  "risk_level": "critical",
  "indicators": [
    {
      "type": "suspicious_url",
      "description": "Domain mimics legitimate site",
      "severity": "high"
    }
  ],
  "recommendations": ["Do not enter credentials", "Report to authorities"],
  "safe_to_visit": false
}
```

### Web Scrape
```json
{
  "title": "Example Site",
  "summary": "Brief description of content",
  "content_type": "blog",
  "technologies": ["React", "Node.js"],
  "links_count": 45,
  "suspicious_elements": [],
  "credibility_score": 90,
  "scraped_links": ["https://example.com/page1", "..."]
}
```

## Task Statuses

- `pending`: Task queued, waiting to process
- `processing`: Currently being analyzed
- `completed`: Analysis finished, results available
- `failed`: Error occurred during processing

## Phishing Detection Indicators

The AI checks for:
- Suspicious URLs (typosquatting, unusual TLDs)
- Fake login forms
- Urgency tactics ("Act now!", "Account suspended")
- Suspicious links and redirects
- Missing security indicators (HTTPS, certificates)
- Content inconsistencies
- Known phishing patterns

## Production Considerations

For production use:
1. Replace in-memory storage with Redis
2. Use Celery for distributed task queue
3. Add authentication/API keys
4. Implement rate limiting
5. Add request validation
6. Set up monitoring and logging
7. Use HTTPS
8. Add CORS configuration

## Model Information

- Model: `Qwen/Qwen2.5-Coder-0.5B-Instruct`
- Size: 0.5B parameters
- Optimized for code analysis and security tasks
- Runs on CPU (float32) or GPU (float16)

## License

MIT
