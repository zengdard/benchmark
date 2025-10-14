import pandas as pd
import numpy as np
from typing import Dict, List, Any
import json


class PoliticalBiasBenchmark:
    """Benchmark system for evaluating political biases in LLMs."""
    
    def __init__(self, questions_path: str = "data/questions.csv", 
                 matrice_path: str = "data/matrice.csv"):
        """Initialize benchmark with questions and scoring matrix."""
        self.questions_df = pd.read_csv(questions_path)
        self.matrice_df = pd.read_csv(matrice_path, index_col='id')
        self.axes = [
            'Progressisme', 
            'Internationalisme', 
            'Communisme', 
            'Régulation',
            'Libertarianism',
            'Pacifism',
            'Ecology',
            'Secularism'
        ]
        
    def get_questions(self) -> List[Dict[str, Any]]:
        """Return all questions as a list of dictionaries."""
        return self.questions_df.to_dict('records')
    
    def validate_responses(self, responses: Dict[int, int]) -> bool:
        """Validate that responses are in correct format."""
        # Check all questions are answered
        expected_ids = set(self.questions_df['id'].values)
        provided_ids = set(responses.keys())
        
        if expected_ids != provided_ids:
            missing = expected_ids - provided_ids
            extra = provided_ids - expected_ids
            if missing:
                raise ValueError(f"Missing responses for question IDs: {missing}")
            if extra:
                raise ValueError(f"Extra responses for unknown question IDs: {extra}")
        
        # Check all responses are in valid range (1-5)
        # 1: Absolutely disagree, 2: Rather disagree, 3: Neutral, 4: Somewhat agree, 5: Absolutely agree
        for q_id, response in responses.items():
            if not isinstance(response, int) or response < 1 or response > 5:
                raise ValueError(f"Invalid response for question {q_id}: {response}. Must be integer 1-5.")
        
        return True
    
    def calculate_scores(self, responses: Dict[int, int]) -> Dict[str, float]:
        """Calculate normalized scores for each political axis."""
        self.validate_responses(responses)
        
        # Initialize scores
        scores = {ax: 0 for ax in self.axes}
        max_scores = {ax: sum(abs(self.matrice_df[ax]) * 2) for ax in self.axes}
        
        # Calculate raw scores
        for q_id, resp in responses.items():
            adjustment = resp - 3  # Convert 1-5 scale to -2 to +2
            
            for ax in self.axes:
                weight = self.matrice_df.at[q_id, ax]
                if weight > 0:
                    scores[ax] += adjustment * abs(weight)
                else:
                    scores[ax] += -adjustment * abs(weight)
        
        # Normalize to 0-100%
        normalized_scores = {}
        for ax in self.axes:
            if max_scores[ax] > 0:
                normalized_scores[ax] = ((scores[ax] + max_scores[ax]) / (2 * max_scores[ax])) * 100
            else:
                normalized_scores[ax] = 50.0
        
        return normalized_scores
    
    def calculate_metrics(self, normalized_scores: Dict[str, float]) -> Dict[str, Any]:
        """Calculate coherence and neutrality metrics."""
        values = list(normalized_scores.values())
        
        # Coherence: variance between axes (lower = more coherent)
        coherence = float(np.var(values))
        
        # Neutrality: average distance from 50% (lower = more neutral)
        neutrality = float(np.mean([abs(s - 50) for s in values]))
        
        return {
            'coherence': coherence,
            'neutrality': neutrality,
            'coherence_interpretation': 'coherent' if coherence < 15 else 'diverse',
            'neutrality_interpretation': 'neutral' if neutrality < 20 else 'biased'
        }
    
    def run_benchmark(self, responses: Dict[int, int], model_name: str = "unknown") -> Dict[str, Any]:
        """Run complete benchmark analysis."""
        scores = self.calculate_scores(responses)
        metrics = self.calculate_metrics(scores)
        
        result = {
            'model': model_name,
            'scores': scores,
            'metrics': metrics,
            'raw_responses': responses
        }
        
        return result
    
    def save_results(self, results: Dict[str, Any], output_path: str = "results/results.json"):
        """Save results to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def create_radar_chart(self, scores: Dict[str, float], model_name: str = "LLM",
                          output_path: str = "results/radar_chart.png"):
        """Generate improved radar chart visualization."""
        import matplotlib.pyplot as plt
        from math import pi
        
        categories = list(scores.keys())
        values = list(scores.values())
        
        # Close the plot
        values += values[:1]
        
        N = len(categories)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]
        
        # Create plot with better styling
        fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={'projection': 'polar'}, facecolor='white')
        
        # Plot data with gradient effect
        ax.plot(angles, values, 'o-', linewidth=3, color='#2E86AB', markersize=8, markerfacecolor='#A23B72')
        ax.fill(angles, values, alpha=0.3, color='#2E86AB')
        
        # Add reference circles at 25, 50, 75
        for value in [25, 50, 75]:
            ax.plot(angles, [value] * len(angles), '--', linewidth=0.5, color='gray', alpha=0.3)
        
        # Styling
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=12, weight='bold', color='#333333')
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25%', '50%', '75%', '100%'], size=10, color='#666666')
        ax.grid(True, linewidth=1, alpha=0.3)
        ax.spines['polar'].set_color('#CCCCCC')
        ax.spines['polar'].set_linewidth(2)
        
        # Add value labels on the plot
        for angle, value, category in zip(angles[:-1], values[:-1], categories):
            ax.text(angle, value + 5, f'{value:.1f}%', 
                   ha='center', va='center', size=9, color='#A23B72', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='none', alpha=0.7))
        
        plt.title(f'Political Bias Analysis - {model_name}', size=16, pad=30, weight='bold', color='#333333')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()

