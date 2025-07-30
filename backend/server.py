from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import json
import random
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskCreate(BaseModel):
    name: str

class DailyStar(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    day: str  # monday, tuesday, etc.
    stars: int = Field(default=0)  # 0, 1, or 2
    week_start: datetime

class WeeklyProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    week_start: datetime
    total_stars: int = Field(default=0)
    stars_in_safe: int = Field(default=0)

class Reward(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    required_stars: int
    is_claimed: bool = Field(default=False)
    claimed_at: Optional[datetime] = None

class RewardCreate(BaseModel):
    name: str
    required_stars: int

class MathProblem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    correct_answer: int
    user_answer: Optional[int] = None
    is_correct: Optional[bool] = None

class MathChallenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grade: int  # 2 or 3
    problems: List[MathProblem]
    completed: bool = Field(default=False)
    score: int = Field(default=0)
    stars_earned: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MathSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    max_number: int = Field(default=100)
    max_multiplication: int = Field(default=10)
    star_tiers: Dict[str, int] = Field(default={"90": 3, "80": 2, "70": 1})

# Helper functions
def get_current_week_start():
    today = datetime.now()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

async def generate_math_problems(grade: int, count: int = 30) -> List[MathProblem]:
    """Generate AI-powered math problems using OpenAI"""
    openai_key = os.environ.get('OPENAI_API_KEY')
    if not openai_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    # Get math settings
    settings_doc = await db.math_settings.find_one()
    if not settings_doc:
        settings = MathSettings()
        await db.math_settings.insert_one(settings.dict())
    else:
        settings = MathSettings(**settings_doc)
    
    system_message = f"""You are a math problem generator for kids. Generate exactly {count} math problems suitable for Grade {grade}.

For Grade 2: Addition and subtraction with numbers up to {settings.max_number}, multiplication tables up to x{settings.max_multiplication}
For Grade 3: Addition and subtraction with numbers up to {settings.max_number}, multiplication tables up to x{settings.max_multiplication}, some word problems

Include "sister problems" (related problems like 5+3 and 3+5).

Return ONLY a JSON array of objects with this exact format:
[{{"question": "What is 5 + 3?", "answer": 8}}, {{"question": "What is 3 + 5?", "answer": 8}}]

Make the problems diverse but appropriate for the grade level. Focus on numbers only, avoid complex word problems."""

    try:
        chat = LlmChat(
            api_key=openai_key,
            session_id=f"math-gen-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Generate {count} math problems for Grade {grade}")
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        problems_data = json.loads(response.strip())
        
        problems = []
        for i, problem_data in enumerate(problems_data[:count]):  # Ensure we don't exceed count
            problem = MathProblem(
                question=problem_data["question"],
                correct_answer=int(problem_data["answer"])
            )
            problems.append(problem)
            
        return problems
        
    except Exception as e:
        logging.error(f"Error generating math problems: {e}")
        # Fallback to simple generated problems
        return await generate_simple_math_problems(grade, count, settings)

async def generate_simple_math_problems(grade: int, count: int, settings: MathSettings) -> List[MathProblem]:
    """Fallback simple math problem generation"""
    problems = []
    for i in range(count):
        if i % 3 == 0:  # Addition
            a = random.randint(1, settings.max_number // 2)
            b = random.randint(1, settings.max_number // 2)
            problems.append(MathProblem(question=f"What is {a} + {b}?", correct_answer=a + b))
        elif i % 3 == 1:  # Subtraction
            a = random.randint(10, settings.max_number)
            b = random.randint(1, a)
            problems.append(MathProblem(question=f"What is {a} - {b}?", correct_answer=a - b))
        else:  # Multiplication
            a = random.randint(1, settings.max_multiplication)
            b = random.randint(1, 10)
            problems.append(MathProblem(question=f"What is {a} × {b}?", correct_answer=a * b))
    return problems

# Task Management Endpoints
@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate):
    task = Task(name=task_data.name)
    await db.tasks.insert_one(task.dict())
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks():
    tasks = await db.tasks.find().to_list(1000)
    return [Task(**task) for task in tasks]

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    # Also delete associated stars
    await db.daily_stars.delete_many({"task_id": task_id})
    return {"message": "Task deleted"}

# Star Management Endpoints
@api_router.post("/stars/{task_id}/{day}")
async def update_stars(task_id: str, day: str, stars: int):
    if stars < 0 or stars > 2:
        raise HTTPException(status_code=400, detail="Stars must be between 0 and 2")
    
    week_start = get_current_week_start()
    
    # Update or create daily star record
    daily_star = DailyStar(task_id=task_id, day=day, stars=stars, week_start=week_start)
    await db.daily_stars.replace_one(
        {"task_id": task_id, "day": day, "week_start": week_start},
        daily_star.dict(),
        upsert=True
    )
    return {"message": "Stars updated"}

@api_router.get("/stars")
async def get_current_week_stars():
    week_start = get_current_week_start()
    stars = await db.daily_stars.find({"week_start": week_start}).to_list(1000)
    return [DailyStar(**star) for star in stars]

# Weekly Progress Endpoints
@api_router.get("/progress")
async def get_weekly_progress():
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    
    if not progress:
        # Calculate total stars for current week
        stars = await db.daily_stars.find({"week_start": week_start}).to_list(1000)
        total_stars = sum(star["stars"] for star in stars)
        
        progress_obj = WeeklyProgress(week_start=week_start, total_stars=total_stars)
        await db.weekly_progress.insert_one(progress_obj.dict())
        return progress_obj
    
    # Recalculate total stars
    stars = await db.daily_stars.find({"week_start": week_start}).to_list(1000)
    total_stars = sum(star["stars"] for star in stars)
    progress["total_stars"] = total_stars
    
    await db.weekly_progress.replace_one({"week_start": week_start}, progress)
    return WeeklyProgress(**progress)

@api_router.post("/progress/add-to-safe")
async def add_stars_to_safe(stars: int):
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    
    if not progress:
        raise HTTPException(status_code=404, detail="No progress found for current week")
    
    if stars > progress["total_stars"]:
        raise HTTPException(status_code=400, detail="Not enough stars to add to safe")
    
    progress["stars_in_safe"] += stars
    progress["total_stars"] -= stars
    
    await db.weekly_progress.replace_one({"week_start": week_start}, progress)
    return WeeklyProgress(**progress)

@api_router.post("/progress/reset")
async def reset_weekly_progress():
    week_start = get_current_week_start()
    
    # Clear daily stars for current week
    await db.daily_stars.delete_many({"week_start": week_start})
    
    # Reset total stars but keep safe stars
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    if progress:
        progress["total_stars"] = 0
        await db.weekly_progress.replace_one({"week_start": week_start}, progress)
    
    return {"message": "Weekly progress reset"}

# Rewards Endpoints
@api_router.post("/rewards", response_model=Reward)
async def create_reward(reward_data: RewardCreate):
    reward = Reward(name=reward_data.name, required_stars=reward_data.required_stars)
    await db.rewards.insert_one(reward.dict())
    return reward

@api_router.get("/rewards", response_model=List[Reward])
async def get_rewards():
    rewards = await db.rewards.find().to_list(1000)
    return [Reward(**reward) for reward in rewards]

@api_router.post("/rewards/{reward_id}/claim")
async def claim_reward(reward_id: str):
    reward = await db.rewards.find_one({"id": reward_id})
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    # Check if enough stars in safe
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    
    if not progress or progress["stars_in_safe"] < reward["required_stars"]:
        raise HTTPException(status_code=400, detail="Not enough stars in safe")
    
    # Deduct stars and mark reward as claimed
    progress["stars_in_safe"] -= reward["required_stars"]
    reward["is_claimed"] = True
    reward["claimed_at"] = datetime.utcnow()
    
    await db.weekly_progress.replace_one({"week_start": week_start}, progress)
    await db.rewards.replace_one({"id": reward_id}, reward)
    
    return Reward(**reward)

@api_router.delete("/rewards/{reward_id}")
async def delete_reward(reward_id: str):
    result = await db.rewards.delete_one({"id": reward_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reward not found")
    return {"message": "Reward deleted"}

# Math Challenge Endpoints
@api_router.post("/math/challenge/{grade}")
async def create_math_challenge(grade: int):
    if grade not in [2, 3]:
        raise HTTPException(status_code=400, detail="Grade must be 2 or 3")
    
    problems = await generate_math_problems(grade)
    challenge = MathChallenge(grade=grade, problems=problems)
    
    await db.math_challenges.insert_one(challenge.dict())
    return challenge

@api_router.post("/math/challenge/{challenge_id}/submit")
async def submit_math_answers(challenge_id: str, answers: Dict[int, int]):
    challenge = await db.math_challenges.find_one({"id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge_obj = MathChallenge(**challenge)
    
    correct_count = 0
    total_problems = len(challenge_obj.problems)
    
    # Grade the answers
    for i, problem in enumerate(challenge_obj.problems):
        if i in answers:
            problem.user_answer = answers[i]
            problem.is_correct = problem.user_answer == problem.correct_answer
            if problem.is_correct:
                correct_count += 1
    
    # Calculate percentage and stars earned
    percentage = (correct_count / total_problems) * 100
    challenge_obj.score = percentage
    challenge_obj.completed = True
    
    # Get star tiers from settings
    settings = await db.math_settings.find_one()
    if settings:
        star_tiers = settings.get("star_tiers", {"90": 3, "80": 2, "70": 1})
    else:
        star_tiers = {"90": 3, "80": 2, "70": 1}
    
    # Calculate stars based on performance
    stars_earned = 0
    for threshold, stars in sorted([(int(k), v) for k, v in star_tiers.items()], reverse=True):
        if percentage >= threshold:
            stars_earned = stars
            break
    
    challenge_obj.stars_earned = stars_earned
    
    # Add earned stars to weekly progress
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    if not progress:
        progress = WeeklyProgress(week_start=week_start, total_stars=stars_earned).dict()
    else:
        progress["total_stars"] += stars_earned
    
    await db.weekly_progress.replace_one({"week_start": week_start}, progress, upsert=True)
    await db.math_challenges.replace_one({"id": challenge_id}, challenge_obj.dict())
    
    return {
        "challenge": challenge_obj,
        "correct_answers": correct_count,
        "total_problems": total_problems,
        "percentage": percentage,
        "stars_earned": stars_earned
    }

@api_router.get("/math/settings")
async def get_math_settings():
    settings = await db.math_settings.find_one()
    if not settings:
        settings = MathSettings()
        await db.math_settings.insert_one(settings.dict())
        return settings
    return MathSettings(**settings)

@api_router.put("/math/settings")
async def update_math_settings(settings: MathSettings):
    await db.math_settings.replace_one({}, settings.dict(), upsert=True)
    return settings

# Basic status endpoints
@api_router.get("/")
async def root():
    return {"message": "Weekly Star Tracker API Ready!"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()