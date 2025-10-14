from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any
import os
from benchmark import PoliticalBiasBenchmark

app = FastAPI(
    title="Political Bias Benchmark API",
    description="API for evaluating political biases in LLM responses",
    version="1.0.0"
)

# Initialize benchmark
benchmark = PoliticalBiasBenchmark()


class BenchmarkRequest(BaseModel):
    """Request model for benchmark evaluation."""
    model_name: str = Field(..., description="Name of the LLM being tested")
    responses: Dict[int, int] = Field(
        ..., 
        description="Dictionary mapping question IDs to responses (1-5 scale)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "deepseek-chat",
                "responses": {
                    1: 4,
                    2: 2,
                    3: 5
                }
            }
        }


class QuestionResponse(BaseModel):
    """Response model for questions."""
    id: int
    texte: str


class BenchmarkResult(BaseModel):
    """Response model for benchmark results."""
    model: str
    scores: Dict[str, float]
    metrics: Dict[str, Any]
    raw_responses: Dict[int, int]


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Political Bias Benchmark API",
        "version": "1.0.0",
        "endpoints": {
            "GET /questions": "Get all benchmark questions",
            "POST /benchmark": "Submit responses and get benchmark results",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/questions", response_model=List[QuestionResponse])
async def get_questions():
    """Get all benchmark questions."""
    try:
        questions = benchmark.get_questions()
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/benchmark", response_model=BenchmarkResult)
async def run_benchmark(request: BenchmarkRequest):
    """
    Run political bias benchmark on submitted responses.
    
    Expects responses in 1-5 scale:
    - 1: Absolutely disagree
    - 2: Rather disagree
    - 3: Neutral or hesitant
    - 4: Somewhat agree
    - 5: Absolutely agree
    """
    try:
        # Run benchmark
        results = benchmark.run_benchmark(
            responses=request.responses,
            model_name=request.model_name
        )
        
        # Save results
        os.makedirs("results", exist_ok=True)
        benchmark.save_results(results)
        
        # Create visualization
        benchmark.create_radar_chart(
            scores=results['scores'],
            model_name=request.model_name
        )
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

