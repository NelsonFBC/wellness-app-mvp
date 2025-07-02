# main.py
# To run this backend server:
# 1. Install the necessary libraries:
#    pip install "fastapi[all]" uvicorn
#
# 2. Save this code as `main.py`.
#
# 3. Run the server from your terminal:
#    uvicorn main:app --reload
#
# 4. The API will be live at http://127.0.0.1:8000
#    You can access the interactive documentation at http://127.0.0.1:8000/docs

from fastapi import FastAPI
# --- FIX: Import CORSMiddleware ---
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

# --- 1. Define Data Models ---
# Pydantic models ensure that the data we receive matches the expected structure.
# This provides automatic data validation and is a best practice for building robust APIs.

class SleepData(BaseModel):
    duration: float = Field(..., gt=0, description="Total sleep duration in hours.")
    quality: float = Field(..., ge=0, le=1, description="Sleep quality score from 0.0 to 1.0.")
    deep_percent: float = Field(..., ge=0, le=1, description="Percentage of deep sleep.")

class HeartRateData(BaseModel):
    resting: int = Field(..., gt=0, description="Resting heart rate in beats per minute.")
    hrv: int = Field(..., gt=0, description="Heart rate variability in milliseconds.")

class ActivityData(BaseModel):
    steps: int = Field(..., ge=0, description="Total steps for the day.")
    zone_minutes: int = Field(..., ge=0, description="Minutes spent in active heart rate zones.")

class HealthData(BaseModel):
    """This is the main model representing all the data we expect from the frontend."""
    sleep: SleepData
    heartRate: HeartRateData
    activity: ActivityData

class WellnessResponse(BaseModel):
    """This is the model for the data our API will send back."""
    score: int
    insight: str

# --- 2. Create FastAPI Application ---
app = FastAPI(
    title="AI Wellness Companion API",
    description="MVP of the wellness analysis backend.",
    version="1.0.0"
)

# --- FIX: Add CORS Middleware ---
# This block allows the frontend (running on a different origin) to make requests to this backend.
# This is the primary fix for the "Failed to fetch" error.
origins = ["*"]  # For development. In production, restrict this to your frontend's domain.

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Implement the Wellness Algorithm ---
# This is the core logic ported directly from our MVP prototype.
# It takes the validated HealthData object and returns a score and insight.

def calculate_wellness(data: HealthData) -> WellnessResponse:
    """
    Analyzes health data using a rule-based algorithm to generate a wellness score and insight.
    """
    score = 50  # Start with a baseline score
    insights = []

    # 1. Analyze Sleep
    if data.sleep.duration >= 7.5:
        score += 15
        insights.append("Excellent sleep duration has prepared your body for the day.")
    elif data.sleep.duration < 6:
        score -= 20
        # Corrected a typo from .push to .append for Python list method
        insights.append("Short sleep duration may impact your cognitive function and physical performance. Prioritize rest.")
    else:
        score += 5
    
    if data.sleep.quality < 0.75:
        score -= 10

    # 2. Analyze Heart Rate
    if data.heartRate.resting <= 60:
        score += 15
    elif data.heartRate.resting > 65:
        score -= 15
        insights.append("Your resting heart rate is elevated, suggesting your body is under stress. Consider a lighter day.")
    
    if data.heartRate.hrv >= 65:
        score += 15
        insights.append("A high HRV indicates your nervous system is well-recovered and ready for strain.")
    elif data.heartRate.hrv < 40:
        score -= 20
        insights.append("Low HRV is a sign of fatigue. Focus on recovery activities.")

    # 3. Analyze Activity
    if data.activity.steps >= 10000:
        score += 10
    
    # This is a more complex insight, combining two data points
    if data.activity.zone_minutes > 60 and data.heartRate.hrv < 45:
        insights.append("High activity levels combined with low recovery metrics suggest a risk of overtraining.")

    # Normalize score to be between 0 and 100
    score = max(0, min(100, score))
    
    # Combine insights into a single paragraph
    final_insight = ' '.join(insights) if insights else "Your metrics are balanced. A good day to maintain your routine."

    return WellnessResponse(score=round(score), insight=final_insight)


# --- 4. Define API Endpoint ---
@app.post("/analyze", response_model=WellnessResponse)
async def analyze_health_data(health_data: HealthData):
    """
    This endpoint receives a user's daily health data, analyzes it using
    the wellness algorithm, and returns a readiness score and a personalized insight.
    """
    # The `health_data` parameter is automatically validated against the HealthData model.
    # If the incoming data doesn't match the structure, FastAPI returns an error.
    
    response = calculate_wellness(health_data)
    
    return response

# You can add a simple root endpoint for health checks
@app.get("/")
def read_root():
    return {"status": "Wellness API is running"}
