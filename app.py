from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
import re

app = Flask(__name__)

# Load model and tokenizer
model_name = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
print(f"Loading model: {model_name}")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)
print("Model loaded successfully")

@app.route('/review-dockerfile', methods=['POST'])
def review_dockerfile():
    data = request.json
    dockerfile_content = data.get('dockerfile', '')
    
    if not dockerfile_content:
        return jsonify({'error': 'No dockerfile content provided'}), 400
    
    prompt = f"""Analyze this Dockerfile and provide a JSON response with:
1. stages: array of build stages with their purpose
2. review: array of issues/improvements
3. estimated_build_time: approximate time in minutes

Dockerfile:
{dockerfile_content}

Respond ONLY with valid JSON in this exact format:
{{
  "stages": [
    {{"name": "stage_name", "purpose": "description"}}
  ],
  "review": [
    {{"severity": "high/medium/low", "issue": "description", "suggestion": "fix"}}
  ],
  "estimated_build_time": "X-Y minutes"
}}"""
    
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1012,
            temperature=1,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
    
    generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    
    # Extract JSON from response
    try:
        json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(generated_text)
        return jsonify(result)
    except:
        return jsonify({
            "stages": [],
            "review": [{"severity": "info", "issue": "Could not parse response", "suggestion": "Manual review needed"}],
            "estimated_build_time": "unknown",
            "raw_response": generated_text
        })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': model_name})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3500, debug=True)
