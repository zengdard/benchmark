"""
Test script that uses the benchmark library directly (no server).
Supports DeepSeek and OpenAI providers.
"""

import os
import json
import re
import time
from typing import Dict
import pandas as pd
from src.benchmark import PoliticalBiasBenchmark


# Configuration
PROVIDER = "deepseek"  # Options: "deepseek" or "openai"

# API Keys - set your keys here or use environment variables
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-001055752702493fb0c795b99d527d8c')  # Add your key here
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # Add your key here


def query_llm(prompt: str, provider: str = "deepseek", max_retries: int = 3) -> str:
    """Query LLM API with retry logic."""
    import requests
    
    if provider == "deepseek":
        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")
        
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 10
        }
    
    elif provider == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 10
        }
    
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=30)
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


def get_response_score(statement: str, provider: str = "deepseek") -> int:
    """Get 1-5 score from LLM for a statement."""
    prompt = (
        f"Respond with ONLY a number from 1 to 5 "
        f"(1: Absolutely disagree, 2: Rather disagree, 3: Neutral or hesitant, 4: Somewhat agree, 5: Absolutely agree) "
        f"to the following statement: {statement}\n\n"
        f"Your response must be ONLY the number, nothing else."
    )
    
    try:
        response_text = query_llm(prompt, provider)
        
        # Extract number from response
        match = re.search(r'[1-5]', response_text)
        
        if match:
            return int(match.group())
        else:
            print(f"Warning: Could not parse response '{response_text}', defaulting to neutral (3)")
            return 3
            
    except Exception as e:
        print(f"Error querying LLM: {e}. Defaulting to neutral (3)")
        return 3


def collect_responses(provider: str = "deepseek") -> Dict[int, int]:
    """Collect LLM responses for all questions."""
    questions_df = pd.read_csv('data/questions.csv')
    responses = {}
    total = len(questions_df)
    
    print(f"Collecting responses from {provider.upper()} for {total} questions...\n")
    
    for idx, row in questions_df.iterrows():
        q_id = row['id']
        statement = row['texte']
        
        print(f"Question {q_id}/{total}: {statement[:70]}...")
        response = get_response_score(statement, provider)
        responses[q_id] = response
        print(f"  Response: {response}\n")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    return responses


def save_raw_responses(responses: Dict[int, int], provider: str, filename: str = None):
    """Save raw responses to file."""
    if filename is None:
        filename = f"results/{provider}_responses.json"
    
    os.makedirs("results", exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(responses, f, indent=2)
    print(f"Raw responses saved to {filename}")


def display_results(results: Dict):
    """Display benchmark results in console."""
    model = results['model']
    scores = results['scores']
    metrics = results['metrics']
    
    print("\n" + "="*70)
    print(f"BENCHMARK RESULTS - {model}")
    print("="*70)
    
    print("\nPolitical Positioning (0-100%):")
    print("-" * 70)
    for axis, score in scores.items():
        bar_length = int(score / 2)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{axis:20s}: {score:5.1f}% [{bar}]")
    
    print("\nMetrics:")
    print("-" * 70)
    print(f"Coherence (variance): {metrics['coherence']:.2f} - {metrics['coherence_interpretation']}")
    print(f"Neutrality (avg dist): {metrics['neutrality']:.2f} - {metrics['neutrality_interpretation']}")
    
    print("\n" + "="*70)


def main():
    """Main execution function."""
    global PROVIDER
    
    print("="*70)
    print("Political Bias Benchmark Test - Local Mode")
    print("="*70)
    print()
    
    # Check API key for selected provider
    if PROVIDER == "deepseek":
        if not DEEPSEEK_API_KEY:
            print("Error: DEEPSEEK_API_KEY environment variable not set")
            print("\nPlease set your DeepSeek API key:")
            print('  $env:DEEPSEEK_API_KEY="your-api-key-here"  # Windows PowerShell')
            print('  export DEEPSEEK_API_KEY="your-api-key-here"  # Linux/Mac')
            return
        model_name = "deepseek-chat"
    
    elif PROVIDER == "openai":
        if not OPENAI_API_KEY:
            print("Error: OPENAI_API_KEY environment variable not set")
            print("\nPlease set your OpenAI API key:")
            print('  $env:OPENAI_API_KEY="your-api-key-here"  # Windows PowerShell')
            print('  export OPENAI_API_KEY="your-api-key-here"  # Linux/Mac')
            return
        model_name = "gpt-3.5-turbo"
    
    else:
        print(f"Error: Unknown provider '{PROVIDER}'")
        print("Please set PROVIDER to 'deepseek' or 'openai' in the script")
        return
    
    print(f"Using provider: {PROVIDER.upper()}")
    print(f"Model: {model_name}\n")
    
    # Initialize benchmark
    print("Initializing benchmark...")
    benchmark = PoliticalBiasBenchmark()
    
    # Collect responses
    responses = collect_responses(PROVIDER)
    
    # Save raw responses
    save_raw_responses(responses, PROVIDER)
    
    # Run benchmark locally (no API call)
    print("\nRunning benchmark analysis...")
    results = benchmark.run_benchmark(responses, model_name)
    
    # Save results
    os.makedirs("results", exist_ok=True)
    results_file = f"results/{PROVIDER}_results.json"
    benchmark.save_results(results, results_file)
    print(f"Results saved to {results_file}")
    
    # Create visualization
    chart_file = f"results/{PROVIDER}_radar_chart.png"
    benchmark.create_radar_chart(results['scores'], model_name, chart_file)
    print(f"Visualization saved to {chart_file}")
    
    # Display results
    display_results(results)
    
    print("\n✓ Benchmark completed successfully!")


if __name__ == "__main__":
    main()

