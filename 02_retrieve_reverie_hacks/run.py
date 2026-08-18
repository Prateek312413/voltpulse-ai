"""
SynapseFlow Server & API Gateway
FastAPI entry point for the SynapseFlow Multi-LLM Prompt Orchestrator and Web Studio.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from synapseflow.config import settings
from synapseflow.models import PipelineExecutionRequest, PipelineExecutionResponse
from synapseflow.pipeline.orchestrator import PipelineOrchestrator
from synapseflow.evaluation.benchmark import BenchmarkRunner

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Deterministic Multi-LLM Scientific Prompt Orchestration Engine for Reverie Hacks 2026"
)

# Enable CORS for local testing and developer tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator & Benchmark Runner
orchestrator = PipelineOrchestrator()
benchmark_runner = BenchmarkRunner(orchestrator)

# Mount Static Files Directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "ok", "message": "SynapseFlow API is active. Web UI not found."}

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "featherless_mode": "LIVE API" if orchestrator.featherless.is_live else "RESILIENT OFFLINE SIMULATION",
        "wolfram_mode": "LIVE WOLFRAM ALPHA API" if orchestrator.wolfram.is_live else "DETERMINISTIC SYMPY ORACLE",
        "active_models": settings.MODELS
    }

@app.post("/api/pipeline/run", response_model=PipelineExecutionResponse, tags=["Orchestration"])
def execute_pipeline(request: PipelineExecutionRequest):
    """Executes the complete 5-stage SynapseFlow prompt workflow on a user prompt."""
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt text must not be empty."
        )
    try:
        response = orchestrator.run(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )

@app.get("/api/pipeline/benchmark", tags=["Evaluation"])
def run_benchmark():
    """Runs the 5-case benchmark comparing Single-Prompt Naive Baselines vs SynapseFlow."""
    try:
        results = benchmark_runner.run_all()
        return {
            "total_test_cases": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark execution failed: {str(e)}"
        )

@app.get("/api/models/catalog", tags=["Catalog"])
def get_model_catalog():
    """Returns the Featherless model catalog used in SynapseFlow routing."""
    return {
        "routing_architecture": {
            "Stage 1 (Intent & Decomposition)": settings.MODELS["router"],
            "Stage 2 (Mathematical & Deep Reasoning)": settings.MODELS["reasoner"],
            "Stage 2 (Structured Schema & Coder)": settings.MODELS["coder"],
            "Stage 3 (Symbolic Verification Oracle)": "Wolfram Engine (SymPy Deterministic)",
            "Stage 4 (Consensus & Hallucination Guard)": settings.MODELS["consensus"],
            "Stage 5 (Verified Structured Synthesis)": settings.MODELS["synthesizer"]
        },
        "supported_flagship_models": [
            "deepseek-ai/DeepSeek-V3-0324",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "mistralai/Mistral-Nemo-Instruct-2407",
            "moonshotai/Kimi-K2.5",
            "THUDM/GLM-5",
            "meta-llama/Llama-3.3-70B-Instruct"
        ]
    }

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True)
