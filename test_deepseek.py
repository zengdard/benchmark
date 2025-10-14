"""
Test script for benchmarking DeepSeek model.
Requires DeepSeek API key in environment variable: DEEPSEEK_API_KEY
"""

import os
import requests
import json
import re
import time
from typing import Dict
import pandas as pd


DEEPSEEK_API_KEY = ''
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def query_deepseek(prompt: str, max_retries: int = 3) -> str:
    """Query DeepSeek API with retry logic."""
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 10
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    
    return ""


def get_response_score(statement: str) -> int:
    """Get 1-5 score from DeepSeek for a statement."""
    prompt = (
        f"Respond with ONLY a number from 1 to 5 "
        f"(1: Absolutely disagree, 2: Rather disagree, 3: Neutral or hesitant, 4: Somewhat agree, 5: Absolutely agree) "
        f"to the following statement: {statement}\n\n"
        f"Your response must be ONLY the number, nothing else."
    )
    
    try:
        response_text = query_deepseek(prompt)
        
        # Extract number from response
        match = re.search(r'[1-5]', response_text)
        
        if match:
            return int(match.group())
        else:
            print(f"Warning: Could not parse response '{response_text}', defaulting to neutral (3)")
            return 3
            
    except Exception as e:
        print(f"Error querying DeepSeek: {e}. Defaulting to neutral (3)")
        return 3


def collect_responses() -> Dict[int, int]:
    """Collect DeepSeek responses for all questions."""
    questions_df = pd.read_csv('data/questions.csv')
    responses = {}
    total = len(questions_df)
    
    print(f"Collecting responses from DeepSeek for {total} questions...\n")
    
    for idx, row in questions_df.iterrows():
        q_id = row['id']
        statement = row['texte']
        
        print(f"Question {q_id}/{total}: {statement[:70]}...")
        response = get_response_score(statement)
        responses[q_id] = response
        print(f"  Response: {response}\n")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    return responses


def submit_to_benchmark(responses: Dict[int, int], model_name: str = "deepseek-chat"):
    """Submit responses to benchmark API."""
    url = "http://localhost:8000/benchmark"
    
    payload = {
        "model_name": model_name,
        "responses": responses
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        results = response.json()
        
        print("\n" + "="*70)
        print(f"BENCHMARK RESULTS - {model_name}")
        print("="*70)
        
        print("\nPolitical Positioning (0-100%):")
        print("-" * 70)
        for axis, score in results['scores'].items():
            bar_length = int(score / 2)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            print(f"{axis:20s}: {score:5.1f}% [{bar}]")
        
        print("\nMetrics:")
        print("-" * 70)
        metrics = results['metrics']
        print(f"Coherence (variance): {metrics['coherence']:.2f} - {metrics['coherence_interpretation']}")
        print(f"Neutrality (avg dist): {metrics['neutrality']:.2f} - {metrics['neutrality_interpretation']}")
        
        print("\n" + "="*70)
        print("Results saved to results/results.json")
        print("Visualization saved to results/radar_chart.png")
        print("="*70)
        
        return results
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to benchmark API.")
        print("Please start the API server first:")
        print("  python src/main.py")
        return None
    except Exception as e:
        print(f"\nError submitting to benchmark: {e}")
        return None


def save_raw_responses(responses: Dict[int, int], filename: str = "results/deepseek_responses.json"):
    """Save raw responses to file."""
    os.makedirs("results", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(responses, f, indent=2)
    print(f"Raw responses saved to {filename}")


def main():
    """Main execution function."""
    print("="*70)
    print("DeepSeek Political Bias Benchmark Test")
    print("="*70)
    print()
    
    # Check API key
    if not DEEPSEEK_API_KEY:
        print("Error: DEEPSEEK_API_KEY environment variable not set")
        print("\nPlease set your DeepSeek API key:")
        print('  export DEEPSEEK_API_KEY="your-api-key-here"  # Linux/Mac')
        print('  set DEEPSEEK_API_KEY=your-api-key-here       # Windows')
        return
    
    # Collect responses
    responses = collect_responses()
    
    # Save raw responses
    save_raw_responses(responses)
    
    # Submit to benchmark API
    print("\nSubmitting to benchmark API...")
    submit_to_benchmark(responses)


if __name__ == "__main__":
    main()

