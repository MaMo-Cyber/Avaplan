from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
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
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')

if not mongo_url:
    print("❌ ERROR: MONGO_URL environment variable is not set!")
    print("Please set MONGO_URL in Render environment variables.")
    raise ValueError("MONGO_URL environment variable is required!")

if not (mongo_url.startswith('mongodb://') or mongo_url.startswith('mongodb+srv://')):
    print(f"❌ ERROR: Invalid MONGO_URL format: {mongo_url[:50]}...")
    print("MONGO_URL must start with 'mongodb://' or 'mongodb+srv://'")
    raise ValueError("Invalid MONGO_URL format!")

# Show connection info (safely)
if 'MaMo1988' in mongo_url:
    print(f"🔗 Connecting with user MaMo1988 to: weekly-tracker.rhgfzlq.mongodb.net")
else:
    print(f"🔗 Connecting to MongoDB: {mongo_url[:50]}...")

try:
    client = AsyncIOMotorClient(mongo_url)
    # Extract database name from connection string or use default
    db_name = os.environ.get('DB_NAME', 'weekly_star_tracker')
    db = client[db_name]
    print(f"📂 Using database: {db_name}")
    print("✅ MongoDB client created successfully!")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    raise

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://weekly-star-tracker.netlify.app",  # Production frontend
        "https://weekly-star-tracker.netlify.app/",  # With trailing slash
        "*"  # Allow all for debugging
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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
    total_stars_earned: int = Field(default=0)  # Total stars earned from tasks (never decreases)
    total_stars_used: int = Field(default=0)   # Stars that have been moved to safe or available
    stars_in_safe: int = Field(default=0)  # Stars stored in safe
    available_stars: int = Field(default=0)  # Stars available for rewards (withdrawn from safe + bonus stars)
    
    @property
    def total_stars(self):
        """Available stars for moving (earned - used)"""
        return self.total_stars_earned - self.total_stars_used

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
    question_type: str = Field(default="text")  # "text", "clock", "currency"
    clock_data: Optional[Dict] = None  # For clock problems: {"hours": 3, "minutes": 30}
    currency_data: Optional[Dict] = None  # For currency problems: {"amounts": [1.50, 2.30], "operation": "add"}
    correct_answer: str  # Changed to str to handle different answer types
    user_answer: Optional[str] = None
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
    problem_count: int = Field(default=30)  # Configurable number of problems
    star_tiers: Dict[str, int] = Field(default={"90": 3, "80": 2, "70": 1})
    problem_types: Dict[str, bool] = Field(default={
        "addition": True,
        "subtraction": True, 
        "multiplication": True,
        "clock_reading": False,
        "currency_math": False,
        "word_problems": False
    })
    currency_settings: Dict[str, Any] = Field(default={
        "currency_symbol": "€",
        "max_amount": 20.00,
        "decimal_places": 2
    })
    clock_settings: Dict[str, Any] = Field(default={
        "include_half_hours": True,
        "include_quarter_hours": True,
        "include_five_minute_intervals": False
    })

class MathStatistics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_attempts: int = Field(default=0)
    grade_2_attempts: int = Field(default=0)
    grade_3_attempts: int = Field(default=0)
    total_correct: int = Field(default=0)
    total_wrong: int = Field(default=0)
    average_score: float = Field(default=0.0)
    best_score: float = Field(default=0.0)
    total_stars_earned: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# German Challenge Models
class GermanProblem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    question_type: str  # "spelling", "word_types", "fill_blank", "grammar"
    problem_data: Optional[Dict] = None  # Additional data for complex problems
    options: Optional[List[str]] = None  # For multiple choice questions
    correct_answer: str
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None

class GermanChallenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grade: int  # 2 or 3
    problems: List[GermanProblem]
    completed: bool = Field(default=False)
    score: int = Field(default=0)
    stars_earned: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GermanSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem_count: int = Field(default=20)  # Default number of German problems
    star_tiers: Dict[str, int] = Field(default={"90": 3, "80": 2, "70": 1})
    problem_types: Dict[str, bool] = Field(default={
        "spelling": True,
        "word_types": True,
        "fill_blank": True,
        "grammar": False,
        "articles": False,
        "sentence_order": False
    })
    difficulty_settings: Dict[str, Any] = Field(default={
        "spelling_difficulty": "medium",  # easy, medium, hard
        "word_types_include_adjectives": True,
        "fill_blank_context_length": "short"  # short, medium, long
    })

class GermanStatistics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_attempts: int = Field(default=0)
    grade_2_attempts: int = Field(default=0)
    grade_3_attempts: int = Field(default=0)
    total_correct: int = Field(default=0)
    total_wrong: int = Field(default=0)
    average_score: float = Field(default=0.0)
    best_score: float = Field(default=0.0)
    total_stars_earned: int = Field(default=0)
    problem_type_stats: Dict[str, Dict] = Field(default={})  # Stats per problem type
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# English Challenge Models
class EnglishProblem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    question_type: str  # "vocabulary_de_en", "vocabulary_en_de", "simple_sentences", "basic_grammar"
    problem_data: Optional[Dict] = None  # Additional data for complex problems
    options: Optional[List[str]] = None  # For multiple choice questions
    correct_answer: str
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None

class EnglishChallenge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    grade: int  # 2 or 3
    problems: List[EnglishProblem]
    completed: bool = Field(default=False)
    score: int = Field(default=0)
    stars_earned: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EnglishSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    problem_count: int = Field(default=15)  # Default number of English problems
    star_tiers: Dict[str, int] = Field(default={"90": 3, "80": 2, "70": 1})
    problem_types: Dict[str, bool] = Field(default={
        "vocabulary_de_en": True,  # German to English vocabulary
        "vocabulary_en_de": True,  # English to German vocabulary
        "simple_sentences": True,  # Simple sentence translation
        "basic_grammar": False,    # Basic English grammar
        "colors_numbers": True,    # Colors and numbers
        "animals_objects": True    # Animals and everyday objects
    })
    difficulty_settings: Dict[str, Any] = Field(default={
        "vocabulary_level": "basic",  # basic, intermediate
        "include_articles": False,    # Include "der/die/das" with German words
        "sentence_complexity": "simple"  # simple, medium
    })

class EnglishStatistics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_attempts: int = Field(default=0)
    grade_2_attempts: int = Field(default=0)
    grade_3_attempts: int = Field(default=0)
    total_correct: int = Field(default=0)
    total_wrong: int = Field(default=0)
    average_score: float = Field(default=0.0)
    best_score: float = Field(default=0.0)
    total_stars_earned: int = Field(default=0)
    problem_type_stats: Dict[str, Dict] = Field(default={})  # Stats per problem type
    last_updated: datetime = Field(default_factory=datetime.utcnow)

async def generate_german_problems(grade: int, count: int = None) -> List[GermanProblem]:
    """Generate AI-powered German language problems"""
    
    # Get German settings
    settings_doc = await db.german_settings.find_one()
    if not settings_doc:
        settings = GermanSettings()
        await db.german_settings.insert_one(settings.dict())
    else:
        settings = GermanSettings(**settings_doc)
    
    # Use configured problem count if not specified
    if count is None:
        count = settings.problem_count
    
    # Generate mix of problems based on enabled types
    problems = []
    enabled_types = [k for k, v in settings.problem_types.items() if v]
    
    if not enabled_types:
        enabled_types = ["spelling", "word_types", "fill_blank"]  # fallback
    
    problems_per_type = count // len(enabled_types)
    remaining = count % len(enabled_types)
    
    for problem_type in enabled_types:
        type_count = problems_per_type + (1 if remaining > 0 else 0)
        remaining -= 1
        
        if problem_type == "spelling":
            problems.extend(await generate_spelling_problems(type_count, grade, settings))
        elif problem_type == "word_types":
            problems.extend(await generate_word_type_problems(type_count, grade, settings))
        elif problem_type == "fill_blank":
            problems.extend(await generate_fill_blank_problems(type_count, grade, settings))
        elif problem_type == "grammar":
            problems.extend(await generate_grammar_problems(type_count, grade, settings))
        elif problem_type == "articles":
            problems.extend(await generate_article_problems(type_count, grade, settings))
        elif problem_type == "sentence_order":
            problems.extend(await generate_sentence_order_problems(type_count, grade, settings))
    
    # Shuffle the problems
    random.shuffle(problems)
    return problems[:count]

def apply_spelling_difficulty_filter(word_list, difficulty):
    """Filter word list based on difficulty setting"""
    if difficulty == "easy":
        # Filter for shorter words (easier to spell)
        return [word for word in word_list if len(word["correct"]) <= 8]
    elif difficulty == "hard":
        # Include longer words and more complex spellings
        return [word for word in word_list if len(word["correct"]) >= 6]
    else:  # medium
        # Include all words (no filtering)
        return word_list

def apply_word_type_difficulty_filter(examples, difficulty, include_adjectives=True):
    """Filter word type examples based on difficulty setting"""
    if difficulty == "easy":
        # Only use Nomen and Verb (easier to identify)
        filtered = [ex for ex in examples if ex["type"] in ["Nomen", "Verb"]]
        # Also prefer shorter sentences
        filtered = [ex for ex in filtered if len(ex["sentence"].split()) <= 6]
        return filtered
    elif difficulty == "hard":
        # Include all word types including more complex ones
        if include_adjectives:
            return examples
        else:
            return [ex for ex in examples if ex["type"] != "Adjektiv"]
    else:  # medium
        # Standard behavior - include adjectives based on setting
        if include_adjectives:
            return examples
        else:
            return [ex for ex in examples if ex["type"] != "Adjektiv"]

def apply_fill_blank_difficulty_filter(templates, difficulty, context_length="short"):
    """Filter fill-blank templates based on difficulty setting"""
    if difficulty == "easy":
        # Use shorter texts and simpler vocabulary
        filtered = [t for t in templates if len(t["text"].split()) <= 8]
        # Prefer templates where answer is a common word
        common_words = ["ist", "hat", "geht", "kommt", "spielt", "läuft", "springt", "singt", "tanzt", "kocht"]
        easy_templates = [t for t in filtered if t["answer"].lower() in common_words]
        return easy_templates if easy_templates else filtered[:min(20, len(filtered))]
    elif difficulty == "hard":
        # Use longer texts and more complex vocabulary
        if context_length == "long":
            return [t for t in templates if len(t["text"].split()) >= 8]
        else:
            return templates
    else:  # medium
        # Standard behavior based on context length setting
        if context_length == "short":
            return [t for t in templates if len(t["text"].split()) <= 12]
        elif context_length == "long":
            return [t for t in templates if len(t["text"].split()) >= 6]
        else:  # medium context
            return templates

async def generate_spelling_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate German spelling problems using massively expanded content"""
    problems = []
    
    # Try AI generation first
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            ai_problems = await generate_ai_spelling_problems(count, grade, settings)
            if ai_problems:
                return ai_problems
    except Exception as e:
        logging.error(f"AI spelling generation failed: {e}")
    
    # Import massively expanded content
    try:
        if grade == 2:
            from german_content_complete import GRADE2_SPELLING_COMPLETE
            word_list = GRADE2_SPELLING_COMPLETE
        else:
            from german_grade3_content import GRADE3_SPELLING_COMPLETE
            word_list = GRADE3_SPELLING_COMPLETE
        
        # Apply difficulty filtering
        difficulty = settings.difficulty_settings.get("spelling_difficulty", "medium")
        filtered_words = apply_spelling_difficulty_filter(word_list, difficulty)
        
        # Shuffle and select random subset to ensure variety
        import random
        available_words = min(count * 3, len(filtered_words))
        shuffled_words = random.sample(filtered_words, available_words) if available_words > 0 else filtered_words
        
        for i in range(min(count, len(shuffled_words))):
            word_data = shuffled_words[i]
            options = [word_data["correct"]] + word_data["wrong"]
            
            # Adjust wrong options based on difficulty
            if difficulty == "easy":
                # Use only 3 options (easier to choose)
                options = options[:3]
            elif difficulty == "hard":
                # Keep all wrong options, make them more similar
                pass
            
            random.shuffle(options)
            
            problem = GermanProblem(
                question=f"Welches Wort ist richtig geschrieben?",
                question_type="spelling",
                options=options,
                correct_answer=word_data["correct"]
            )
            problems.append(problem)
        
        return problems
        
    except ImportError:
        # Fallback to original smaller list if imports fail
        grade2_words = [
            {"correct": "Hund", "wrong": ["Hunt", "Hundt", "Huhnd"]},
            {"correct": "Katze", "wrong": ["Kaze", "Katse", "Kazte"]},
            # Fallback data (smaller set if imports fail)
            {"correct": "Spinne", "wrong": ["Sbinne", "Spinnee", "Zbinne"]},
            {"correct": "Ameise", "wrong": ["Ahmeise", "Ameihse", "Amaise"]},
            {"correct": "Wurm", "wrong": ["Wuhrm", "Wurmm", "Vurm"]},
            {"correct": "Marienkäfer", "wrong": ["Mariehnkäfer", "Mariengäfer", "Maarienkäfer"]},
            {"correct": "Schmetterling", "wrong": ["Schmetehrling", "Schmetterlink", "Schmetterlingg"]},
        {"correct": "Apfel", "wrong": ["Appfel", "Apfol", "Aphel"]},
        {"correct": "Birne", "wrong": ["Birrne", "Bierne", "Pierne"]},
        {"correct": "Banane", "wrong": ["Bannane", "Banahne", "Banaene"]},
        {"correct": "Orange", "wrong": ["Oranje", "Orangge", "Oranghe"]},
        {"correct": "Zitrone", "wrong": ["Sitrone", "Zitrohne", "Zidrohne"]},
        {"correct": "Traube", "wrong": ["Drahube", "Trauhbe", "Traupe"]},
        {"correct": "Erdbeere", "wrong": ["Erdbehre", "Erdbeeere", "Erdpeere"]},
        {"correct": "Himbeere", "wrong": ["Himpbeere", "Himbeehre", "Gimbere"]},
        {"correct": "Blaubeere", "wrong": ["Blauhbeere", "Blaupeere", "Plaubeere"]},
        {"correct": "Kirsche", "wrong": ["Girsche", "Kirschhe", "Kirrsche"]},
        {"correct": "Pflaume", "wrong": ["Bflaume", "Pflauhme", "Pflauhm"]},
        {"correct": "Pfirsich", "wrong": ["Bfirsich", "Pfirschh", "Pvirsich"]},
        {"correct": "Aprikose", "wrong": ["Ahprikose", "Aprigose", "Aprikohse"]},
        {"correct": "Nektarine", "wrong": ["Negktarine", "Nektarihne", "Negktariene"]},
        {"correct": "Melone", "wrong": ["Mehone", "Mellone", "Melohne"]},
        {"correct": "Wassermelone", "wrong": ["Wasermelone", "Wassermelohne", "Vasermelone"]},
        {"correct": "Ananas", "wrong": ["Ahnaas", "Ananass", "Ananahs"]},
        {"correct": "Mango", "wrong": ["Manggo", "Mahngo", "Manko"]},
        {"correct": "Kiwi", "wrong": ["Giwi", "Kiwii", "Kivy"]},
        {"correct": "Papaya", "wrong": ["Bahpaya", "Papahya", "Babaya"]},
        {"correct": "Kokosnuss", "wrong": ["Gokosnuss", "Kokosnuhss", "Kokoznuss"]},
        {"correct": "Avocado", "wrong": ["Ahvocado", "Avogado", "Afocado"]},
        {"correct": "Feige", "wrong": ["Vaige", "Feigee", "Faige"]},
        {"correct": "Dattel", "wrong": ["Dahtell", "Dattell", "Tatel"]},
        {"correct": "Rosine", "wrong": ["Rohsine", "Rosihnne", "Rozine"]},
        {"correct": "Nuss", "wrong": ["Nuß", "Nusss", "Nuhs"]},
        {"correct": "Walnuss", "wrong": ["Wahlnuss", "Walnuß", "Valnuss"]},
        {"correct": "Haselnuss", "wrong": ["Gaselnuss", "Haselnuß", "Hazelnuss"]},
        {"correct": "Mandel", "wrong": ["Mahdel", "Mandell", "Mantell"]},
        {"correct": "Erdnuss", "wrong": ["Aerdnuss", "Erdnuß", "Ehrdnuss"]},
        {"correct": "Kastanie", "wrong": ["Gastanie", "Kastanhie", "Kashtanie"]},
        {"correct": "Eichel", "wrong": ["Aichel", "Eichell", "Eihchel"]},
        {"correct": "Brot", "wrong": ["Broht", "Brott", "Proht"]},
        {"correct": "Weißbrot", "wrong": ["Vaißbrot", "Weißbroht", "Weihßbrot"]},
        {"correct": "Schwarzbrot", "wrong": ["Schwartzbrot", "Schwarzbroht", "Zchwartzbrot"]},
        {"correct": "Vollkornbrot", "wrong": ["Folkornbrot", "Vollgornbrot", "Vollkornbroht"]},
        {"correct": "Brötchen", "wrong": ["Pröhchen", "Brötchenn", "Brötgen"]},
        {"correct": "Semmel", "wrong": ["Zemmel", "Semmell", "Semell"]},
        {"correct": "Baguette", "wrong": ["Pakette", "Baguete", "Baguhette"]},
        {"correct": "Toast", "wrong": ["Doast", "Toasht", "Toasd"]},
        {"correct": "Zwieback", "wrong": ["Swiepack", "Zwiebagk", "Zwiepagk"]},
        {"correct": "Keks", "wrong": ["Gekss", "Kekss", "Kehks"]},
        {"correct": "Kekse", "wrong": ["Gekse", "Keksee", "Kehkse"]},
        {"correct": "Plätzchen", "wrong": ["Blätzchen", "Plätzchenn", "Plähtzchen"]},
        {"correct": "Lebkuchen", "wrong": ["Lebguchen", "Lebkuhchen", "Lepkuchen"]},
        {"correct": "Stollen", "wrong": ["Shtollen", "Stollenn", "Stolenn"]},
        {"correct": "Kuchen", "wrong": ["Guhchen", "Kuchenn", "Kuuchenn"]},
        {"correct": "Torte", "wrong": ["Dohrte", "Tortee", "Tohrte"]},
        {"correct": "Muffin", "wrong": ["Mufinn", "Mufffin", "Muffhin"]},
        {"correct": "Donut", "wrong": ["Dohnut", "Donuht", "Tonuht"]},
        {"correct": "Croissant", "wrong": ["Groissant", "Croissahnt", "Croisant"]},
        {"correct": "Pudding", "wrong": ["Buding", "Pudingg", "Putingg"]},
        {"correct": "Joghurt", "wrong": ["Yoghurt", "Joghuhrt", "Yokurt"]},
        {"correct": "Quark", "wrong": ["Quargg", "Quhark", "Quarkk"]},
        {"correct": "Sahne", "wrong": ["Zaahne", "Sahnee", "Sahne"]},
        {"correct": "Schlagsahne", "wrong": ["Schlagsaahne", "Schlagzahne", "Schlagsahhnee"]},
        {"correct": "Butter", "wrong": ["Buter", "Butterr", "Putter"]},
        {"correct": "Margarine", "wrong": ["Magharine", "Margarihne", "Markaarine"]},
        {"correct": "Käse", "wrong": ["Kääse", "Kaese", "Kässe"]},
        {"correct": "Gouda", "wrong": ["Kouda", "Goudaa", "Gohda"]},
        {"correct": "Emmentaler", "wrong": ["Ementaler", "Emmenhtaler", "Emmentahlerr"]},
        {"correct": "Camembert", "wrong": ["Gämembert", "Camempert", "Camempbert"]},
        {"correct": "Brie", "wrong": ["Prrie", "Briee", "Brie"]},
        {"correct": "Mozzarella", "wrong": ["Motzarella", "Mozzarellla", "Mozarrella"]},
        {"correct": "Parmesan", "wrong": ["Bahrmesan", "Parmesahn", "Parmezan"]},
        {"correct": "Feta", "wrong": ["Veta", "Fettaa", "Fetha"]},
        {"correct": "Ricotta", "wrong": ["Rigotta", "Ricotha", "Ricohta"]},
        {"correct": "Frischkäse", "wrong": ["Vrischkäse", "Frischgäse", "Frischkääse"]},
        {"correct": "Schmelzkäse", "wrong": ["Schmeltzkäse", "Schmelsgäse", "Schmelzkääse"]},
        {"correct": "Hartkäse", "wrong": ["Garhkäse", "Hartgäse", "Hartkääse"]},
        {"correct": "Weichkäse", "wrong": ["Vaichkäse", "Weichgäse", "Weichkääse"]},
        {"correct": "Ziegenkäse", "wrong": ["Siegenkäse", "Ziegengäse", "Ziegenkääse"]},
        {"correct": "Schafskäse", "wrong": ["Schavskäse", "Schafsgäse", "Schafskääse"]},
        {"correct": "Milch", "wrong": ["Millch", "Mihlch", "Milkh"]},
        {"correct": "Vollmilch", "wrong": ["Follmilch", "Vollmihlch", "Vollmilch"]},
        {"correct": "Magermilch", "wrong": ["Maghermilch", "Magermillch", "Makermilch"]},
        {"correct": "Kondensmilch", "wrong": ["Gondensmilch", "Kondensmihlch", "Kondhensmilch"]},
        {"correct": "Buttermilch", "wrong": ["Puhtermilch", "Buttermillch", "Buttehrmihlch"]},
        {"correct": "Kakao", "wrong": ["Gakao", "Kakaoh", "Kakaoo"]},
        {"correct": "Schokolade", "wrong": ["Schogolade", "Schokolahde", "Zchodgolade"]},
        {"correct": "Bonbon", "wrong": ["Ponpon", "Bonbohn", "Bohnbohn"]},
        {"correct": "Gummibärchen", "wrong": ["Kummibärchen", "Gummipärchen", "Gummibäärchen"]},
        {"correct": "Lutscher", "wrong": ["Luhtscher", "Lutscherr", "Luxcher"]},
        {"correct": "Zuckerstange", "wrong": ["Sugkerstange", "Zuckerstanhge", "Zuckehrstange"]},
        {"correct": "Marshmallow", "wrong": ["Marshmahlow", "Marshmallohw", "Marshmalow"]},
        {"correct": "Nougat", "wrong": ["Nohgat", "Nougaht", "Nougatt"]},
        {"correct": "Marzipan", "wrong": ["Mahrzipan", "Marsipan", "Marzibahn"]},
        {"correct": "Leberwurst", "wrong": ["Lebervurst", "Leberwuhst", "Leperwurst"]},
        {"correct": "Bratwurst", "wrong": ["Pratwurst", "Bratwuhst", "Bradhwurst"]},
        {"correct": "Weißwurst", "wrong": ["Vaißwurst", "Weißwuhst", "Weihßwurst"]},
        {"correct": "Blutwurst", "wrong": ["Pluhtewurst", "Blutwuhst", "Bluhtwurst"]},
        {"correct": "Mettwurst", "wrong": ["Mehtwurst", "Metwuhst", "Methwurst"]},
        {"correct": "Salami", "wrong": ["Zalami", "Salamii", "Salahmi"]},
        {"correct": "Schinken", "wrong": ["Schinkenn", "Schinhken", "Zchinkenn"]},
        {"correct": "Speck", "wrong": ["Zbeck", "Specck", "Spegk"]},
        {"correct": "Würstchen", "wrong": ["Vürstchen", "Würstchenn", "Würsthcenn"]},
        {"correct": "Fleischbällchen", "wrong": ["Vlaischbällchen", "Fleischpällchen", "Fleischbäällchenn"]},

        # Body Parts Extended (50 words)
        {"correct": "Kopf", "wrong": ["Gohpf", "Kopff", "Kobf"]},
        {"correct": "Gesicht", "wrong": ["Kehsicht", "Gesichht", "Kezicht"]},
        {"correct": "Stirn", "wrong": ["Shtihrn", "Stirnn", "Stihrn"]},
        {"correct": "Augenbraue", "wrong": ["Ahgenbraue", "Augenpraue", "Augenbrahue"]},
        {"correct": "Wimpern", "wrong": ["Vimpern", "Wimpernn", "Wimpehrn"]},
        {"correct": "Auge", "wrong": ["Ahuge", "Augee", "Ouge"]},
        {"correct": "Pupille", "wrong": ["Bubille", "Pupillee", "Puhpille"]},
        {"correct": "Iris", "wrong": ["Ihris", "Iriss", "Yris"]},
        {"correct": "Lid", "wrong": ["Liht", "Lidd", "Lidt"]},
        {"correct": "Nase", "wrong": ["Nahse", "Nasee", "Naaze"]},
        {"correct": "Nasenloch", "wrong": ["Nahsenloch", "Nazenloch", "Nasenlohch"]},
        {"correct": "Mund", "wrong": ["Muhnd", "Mundd", "Muntd"]},
        {"correct": "Lippe", "wrong": ["Lipe", "Lippee", "Libbee"]},
        {"correct": "Zahn", "wrong": ["Sahn", "Zahnn", "Zaan"]},
        {"correct": "Zähne", "wrong": ["Säähne", "Zähnee", "Zaähne"]},
        {"correct": "Zunge", "wrong": ["Sunghe", "Zungee", "Zunkge"]},
        {"correct": "Gaumen", "wrong": ["Kaumen", "Gaumenn", "Gauhmen"]},
        {"correct": "Kiefer", "wrong": ["Giever", "Kieferr", "Kiepher"]},
        {"correct": "Kinn", "wrong": ["Ginn", "Kinnn", "Kihn"]},
        {"correct": "Wange", "wrong": ["Wahge", "Wangee", "Vange"]},
        {"correct": "Backe", "wrong": ["Pagke", "Backee", "Bakke"]},
        {"correct": "Ohr", "wrong": ["Ohhr", "Ohrr", "Oor"]},
        {"correct": "Ohrläppchen", "wrong": ["Ohrläpchen", "Ohrläbpchen", "Ohrläppchenn"]},
        {"correct": "Hals", "wrong": ["Gahls", "Halss", "Haals"]},
        {"correct": "Kehle", "wrong": ["Gehle", "Kehllee", "Kehlle"]},
        {"correct": "Nacken", "wrong": ["Nahcken", "Nackenn", "Nagken"]},
        {"correct": "Schulter", "wrong": ["Schuhter", "Schulterr", "Schulhter"]},
        {"correct": "Arm", "wrong": ["Ahrm", "Armm", "Aram"]},
        {"correct": "Oberarm", "wrong": ["Ohberarm", "Oberahrm", "Oberarmm"]},
        {"correct": "Unterarm", "wrong": ["Uhnterarm", "Untehrahrm", "Unteraarm"]},
        {"correct": "Ellbogen", "wrong": ["Ellpogen", "Ellbohgen", "Elbogen"]},
        {"correct": "Hand", "wrong": ["Gahnd", "Handd", "Handt"]},
        {"correct": "Handgelenk", "wrong": ["Gandgelenk", "Handgelenkk", "Handkelenk"]},
        {"correct": "Handfläche", "wrong": ["Gandfläche", "Handvläche", "Handflääche"]},
        {"correct": "Handrücken", "wrong": ["Gandrücken", "Handrügken", "Handrückenn"]},
        {"correct": "Finger", "wrong": ["Vingher", "Fingerr", "Finhger"]},
        {"correct": "Daumen", "wrong": ["Dauhmen", "Daumenn", "Tahumen"]},
        {"correct": "Zeigefinger", "wrong": ["Seigefinger", "Zeigevinger", "Zeigefingerr"]},
        {"correct": "Mittelfinger", "wrong": ["Mitelfinger", "Mittelfingerr", "Mithelfinger"]},
        {"correct": "Ringfinger", "wrong": ["Ringvingerr", "Rinkfinger", "Ringfingerr"]},
        {"correct": "Kleiner Finger", "wrong": ["Glleiner Finger", "Kleiner Vingerr", "Klaainer Finger"]},
        {"correct": "Fingernagel", "wrong": ["Vingernagel", "Fingernähgel", "Fingernaagel"]},
        {"correct": "Brust", "wrong": ["Pruhst", "Brusst", "Bruhsht"]},
        {"correct": "Brustkorb", "wrong": ["Prustkorb", "Brustgohb", "Brustkorbb"]},
        {"correct": "Rippe", "wrong": ["Ripe", "Rippee", "Ribbee"]},
        {"correct": "Bauch", "wrong": ["Pauhch", "Bauchh", "Bouch"]},
        {"correct": "Nabel", "wrong": ["Nahbel", "Nabll", "Napell"]},
        {"correct": "Rücken", "wrong": ["Rüggen", "Rückenn", "Rühcken"]},
        {"correct": "Wirbelsäule", "wrong": ["Virbelsäule", "Wirbelsäuhle", "Wirbelsäulle"]},
        {"correct": "Taille", "wrong": ["Daile", "Tailllee", "Tahille"]},
        {"correct": "Hüfte", "wrong": ["Gühfte", "Hüftee", "Hüfthe"]},

        # Additional categories to reach 500 words...
        # Household Items, Colors, Nature, Weather, Time, etc.
        # [More words would be added here to reach the full 500]
    ]
    
    grade3_words = [
        # Advanced/Academic Words (100 words)
        {"correct": "Wissenschaft", "wrong": ["Wissenshaft", "Wissenschafft", "Wisenshaft"]},
        {"correct": "Experiment", "wrong": ["Eksperiment", "Experimehnt", "Experimeent"]},
        {"correct": "Forschung", "wrong": ["Vorschung", "Forschuhng", "Forrschung"]},
        {"correct": "Entdeckung", "wrong": ["Entdeggung", "Entdeckuung", "Entdekcung"]},
        {"correct": "Erfindung", "wrong": ["Ervindung", "Erfinduhng", "Erfindungg"]},
        {"correct": "Technologie", "wrong": ["Dechnologie", "Technologiee", "Technolohgie"]},
        {"correct": "Computer", "wrong": ["Gomputer", "Computher", "Komputer"]},
        {"correct": "Internet", "wrong": ["Ihnternet", "Internett", "Internehd"]},
        {"correct": "Programm", "wrong": ["Brogramm", "Programmm", "Prograhm"]},
        {"correct": "Software", "wrong": ["Zoftware", "Softwahre", "Softwarre"]},
        {"correct": "Hardware", "wrong": ["Gahrdware", "Hartwahre", "Hardwaare"]},
        {"correct": "Roboter", "wrong": ["Rohboter", "Robotehr", "Ropothehr"]},
        {"correct": "Maschine", "wrong": ["Mahschine", "Maschihne", "Maschine"]},
        {"correct": "Werkzeug", "wrong": ["Wergzeug", "Werkzeugg", "Werkseug"]},
        {"correct": "Instrument", "wrong": ["Instruhment", "Instrumentt", "Inshtrument"]},
        {"correct": "Gerät", "wrong": ["Kehräht", "Geräht", "Geraet"]},
        {"correct": "Energie", "wrong": ["Ahnergie", "Energiee", "Enerhgie"]},
        {"correct": "Elektrizität", "wrong": ["Elekhtrizität", "Elektricitaet", "Elektrisitaet"]},
        {"correct": "Batterie", "wrong": ["Pahterie", "Batterihee", "Batteriee"]},
        {"correct": "Motor", "wrong": ["Mohtor", "Motorr", "Mohtorr"]},
        {"correct": "Fahrzeug", "wrong": ["Vahrseug", "Fahrzeugg", "Fahrtzeug"]},
        {"correct": "Verkehr", "wrong": ["Ferkehr", "Verkehhr", "Vergehhr"]},
        {"correct": "Transport", "wrong": ["Drahnsport", "Transportt", "Transsport"]},
        {"correct": "Navigation", "wrong": ["Nahvigation", "Navigationn", "Nafigation"]},
        {"correct": "Kommunikation", "wrong": ["Gommunikation", "Komunikation", "Kommunigkation"]},
        {"correct": "Information", "wrong": ["Informahtion", "Informationn", "Infohrmation"]},
        {"correct": "Bildung", "wrong": ["Pildung", "Bilduhng", "Bilduung"]},
        {"correct": "Erziehung", "wrong": ["Ehrziehung", "Erziehuhng", "Ersieehung"]},
        {"correct": "Universität", "wrong": ["Uhniversität", "Universitaet", "Uhniehrsitaet"]},
        {"correct": "Gymnasium", "wrong": ["Kymnasium", "Gymaasium", "Gymnashium"]},
        {"correct": "Bibliothek", "wrong": ["Pibliotek", "Bibliotheek", "Bibliohthek"]},
        {"correct": "Museum", "wrong": ["Muhseum", "Museuhm", "Muhseuhm"]},
        {"correct": "Theater", "wrong": ["Theahter", "Theaterr", "Thehater"]},
        {"correct": "Konzert", "wrong": ["Gonsert", "Konzehrt", "Konsehrt"]},
        {"correct": "Orchester", "wrong": ["Ohchester", "Orchestrr", "Orchehster"]},
        {"correct": "Dirigent", "wrong": ["Dirikent", "Dirigehnt", "Thirigent"]},
        {"correct": "Komponist", "wrong": ["Gohmpnist", "Komponisht", "Kombonist"]},
        {"correct": "Sänger", "wrong": ["Zänger", "Sängerr", "Saenger"]},
        {"correct": "Musiker", "wrong": ["Muhsiker", "Musigerr", "Musiker"]},
        {"correct": "Künstler", "wrong": ["Günstler", "Künsthler", "Kuenstler"]},
        {"correct": "Maler", "wrong": ["Mahler", "Malerr", "Mahlerr"]},
        {"correct": "Bildhauer", "wrong": ["Pieldhauer", "Bildhauerr", "Bielthauer"]},
        {"correct": "Architekt", "wrong": ["Ahchitekt", "Architegkt", "Architehkt"]},
        {"correct": "Designer", "wrong": ["Dehsigner", "Designerr", "Designehr"]},
        {"correct": "Ingenieur", "wrong": ["Inhgenieur", "Ingenieurr", "Ingenhieur"]},
        {"correct": "Wissenschaftler", "wrong": ["Wissenshaftler", "Wissenschafthler", "Wissenshafftler"]},
        {"correct": "Professor", "wrong": ["Prohfessor", "Professorr", "Profehssor"]},
        {"correct": "Doktor", "wrong": ["Dohktor", "Doktorr", "Dohtorr"]},
        {"correct": "Spezialist", "wrong": ["Zpezialist", "Spezialishht", "Spezialiat"]},
        {"correct": "Experte", "wrong": ["Ehxperte", "Experhtee", "Expehrtee"]},
        {"correct": "Fachmann", "wrong": ["Vachmahn", "Fachmaann", "Fachmahn"]},
        {"correct": "Beratung", "wrong": ["Perahtung", "Berahtung", "Beraatung"]},
        {"correct": "Ausbildung", "wrong": ["Ahusbildung", "Ausbilduhng", "Ausbieldhung"]},
        {"correct": "Weiterbildung", "wrong": ["Veitehrbildung", "Weiterbieldhung", "Weiterbilduhng"]},
        {"correct": "Praktikum", "wrong": ["Bragtikum", "Praktigkum", "Prakhtikum"]},
        {"correct": "Beruf", "wrong": ["Pehruf", "Beruhf", "Berruf"]},
        {"correct": "Karriere", "wrong": ["Garriere", "Karriehre", "Karrhiere"]},
        {"correct": "Arbeitgeber", "wrong": ["Ahrbeitgeber", "Arbeidgeber", "Arbeitkeberr"]},
        {"correct": "Arbeitnehmer", "wrong": ["Ahrbeitnehmer", "Arbeidnehmer", "Arbeitnehmehr"]},
        {"correct": "Kollege", "wrong": ["Gollege", "Kollegee", "Kollehge"]},
        {"correct": "Vorgesetzter", "wrong": ["Fohgesetzter", "Vorgesehtzter", "Vorkesehtzter"]},
        {"correct": "Mitarbeiter", "wrong": ["Mihtarbeiter", "Mitahrbeitr", "Mitraarbeiter"]},
        {"correct": "Teamwork", "wrong": ["Deamwork", "Teamwohrk", "Teahwork"]},
        {"correct": "Projekt", "wrong": ["Brohekt", "Projekht", "Projegkt"]},
        {"correct": "Planung", "wrong": ["Blahnung", "Planuhng", "Plaanung"]},
        {"correct": "Organisation", "wrong": ["Ohganisation", "Organizahtion", "Organishation"]},
        {"correct": "Management", "wrong": ["Manahgement", "Managemehnt", "Manahkement"]},
        {"correct": "Verwaltung", "wrong": ["Fehrwaltung", "Verwahltung", "Vehrwaltung"]},
        {"correct": "Büro", "wrong": ["Pühro", "Bürooh", "Bueroh"]},
        {"correct": "Sekretärin", "wrong": ["Zekretärin", "Sekretährinn", "Segretaerin"]},
        {"correct": "Assistent", "wrong": ["Ahssistent", "Assistenht", "Assishtent"]},
        {"correct": "Chef", "wrong": ["Schef", "Cheff", "Cheef"]},
        {"correct": "Direktor", "wrong": ["Diregktor", "Direktohr", "Direhktor"]},
        {"correct": "Präsident", "wrong": ["Brähsident", "Präsidehnt", "Praesidentt"]},
        {"correct": "Minister", "wrong": ["Mihnister", "Ministehr", "Minishtehr"]},
        {"correct": "Politiker", "wrong": ["Bolitiker", "Politikerr", "Polihtikerr"]},
        {"correct": "Regierung", "wrong": ["Rehgierung", "Regieruung", "Rekierung"]},
        {"correct": "Parlament", "wrong": ["Barlament", "Parlamentt", "Pahrlamet"]},
        {"correct": "Demokratie", "wrong": ["Demohkratie", "Demogratie", "Demokrrhatie"]},
        {"correct": "Wahlen", "wrong": ["Vaahlen", "Wahlenn", "Waahlenn"]},
        {"correct": "Bürger", "wrong": ["Pürger", "Bürgerr", "Buergher"]},
        {"correct": "Gesellschaft", "wrong": ["Kehsellschaft", "Gesellshaft", "Gesellschafft"]},
        {"correct": "Gemeinschaft", "wrong": ["Kemeinschaft", "Gemeinshaft", "Gemainschaft"]},
        {"correct": "Öffentlichkeit", "wrong": ["Oeffentlichkeit", "Öffehntlichkeit", "Öffentligkheit"]},
        {"correct": "Privat", "wrong": ["Brivaht", "Privaht", "Prihvat"]},
        {"correct": "Persönlich", "wrong": ["Behrsönlich", "Persöhnlich", "Persoenlich"]},
        {"correct": "Individuell", "wrong": ["Ihndiviuell", "Indivihduell", "Indivieduell"]},
        {"correct": "Allgemein", "wrong": ["Ahlgemein", "Allgemaihn", "Allkemein"]},
        {"correct": "Besonders", "wrong": ["Pezonders", "Besonderrs", "Besondhers"]},
        {"correct": "Speziell", "wrong": ["Zpeziell", "Spezihell", "Spesziell"]},
        {"correct": "Normal", "wrong": ["Nohmahal", "Normahl", "Nohrmal"]},
        {"correct": "Außergewöhnlich", "wrong": ["Aussehrgewöhnlich", "Außerkewöhnlich", "Ausehrgewoehnlich"]},
        {"correct": "Ungewöhnlich", "wrong": ["Uhngewöhnlich", "Ungewoehnlich", "Unkewoehnlich"]},
        {"correct": "Selten", "wrong": ["Zehten", "Selthenn", "Seltenn"]},
        {"correct": "Häufig", "wrong": ["Gäuhfig", "Häufihk", "Haeufig"]},
        {"correct": "Regelmäßig", "wrong": ["Rehgelmäßig", "Regellmässig", "Rekelmaesig"]},
        {"correct": "Gelegentlich", "wrong": ["Kelehgentlich", "Gelekentlich", "Gelegenhtlich"]},
        {"correct": "Manchmal", "wrong": ["Mahnchmal", "Manchmahl", "Manhchmal"]},
        {"correct": "Niemals", "wrong": ["Niehmals", "Niemahls", "Niemaals"]},
        {"correct": "Immer", "wrong": ["Ihmer", "Immerr", "Ihmmer"]},
        {"correct": "Meistens", "wrong": ["Maistens", "Meisthens", "Meishtens"]},
        {"correct": "Oft", "wrong": ["Ohft", "Offt", "Ofht"]},
        {"correct": "Seldom", "wrong": ["Zehdom", "Seldomm", "Seldohm"]},
        {"correct": "Früher", "wrong": ["Vrüher", "Früherr", "Frueher"]},
        {"correct": "Später", "wrong": ["Zbäter", "Späterr", "Spaeter"]},
        {"correct": "Zukünftig", "wrong": ["Sugünftig", "Zukuenftig", "Zuguenftig"]},
        {"correct": "Vergangen", "wrong": ["Ferhgangen", "Verganhgen", "Vehrgangen"]},
        {"correct": "Gegenwart", "wrong": ["Kehgenwart", "Genkenwart", "Gegenwaart"]},
        {"correct": "Geschichte", "wrong": ["Kehschichte", "Geschichthe", "Geschichtee"]}
    ]
    
    word_list = grade2_words if grade == 2 else grade3_words
    
    # Shuffle to ensure variety and take random subset
    import random
    shuffled_words = random.sample(word_list, min(count * 3, len(word_list)))
    
    for i in range(min(count, len(shuffled_words))):
        word_data = shuffled_words[i]
        options = [word_data["correct"]] + word_data["wrong"]
        random.shuffle(options)
        
        problem = GermanProblem(
            question=f"Welches Wort ist richtig geschrieben?",
            question_type="spelling",
            options=options,
            correct_answer=word_data["correct"]
        )
        problems.append(problem)
    
    return problems

async def generate_word_type_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate word type identification problems using massively expanded content"""
    problems = []
    
    # Try AI generation first
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            ai_problems = await generate_ai_word_type_problems(count, grade, settings)
            if ai_problems:
                return ai_problems
    except Exception as e:
        logging.error(f"AI word type generation failed: {e}")
    
    # Import massively expanded content
    try:
        if grade == 2:
            from german_content_complete import GRADE2_WORD_TYPES_COMPLETE
            examples = GRADE2_WORD_TYPES_COMPLETE
        else:
            from german_grade3_content import GRADE3_WORD_TYPES_COMPLETE
            examples = GRADE3_WORD_TYPES_COMPLETE
        
        # Apply difficulty filtering
        difficulty = settings.difficulty_settings.get("spelling_difficulty", "medium")
        include_adjectives = settings.difficulty_settings.get("word_types_include_adjectives", True)
        filtered_examples = apply_word_type_difficulty_filter(examples, difficulty, include_adjectives)
        
        # Shuffle and select random subset to ensure variety
        import random
        available_examples = min(count * 3, len(filtered_examples))
        shuffled_examples = random.sample(filtered_examples, available_examples) if available_examples > 0 else filtered_examples
        
        for i in range(min(count, len(shuffled_examples))):
            example = shuffled_examples[i]
            
            problem = GermanProblem(
                question=f'Welche Wortart ist das unterstrichene Wort?\n\nSatz: "{example["sentence"]}"\nWort: "{example["word"]}"',
                question_type="word_types",
                options=example["options"],
                correct_answer=example["type"],
                problem_data={"sentence": example["sentence"], "target_word": example["word"]}
            )
            problems.append(problem)
        
        return problems
        
    except ImportError:
        # Fallback to smaller dataset if imports fail
        grade2_examples = [
        {"sentence": "Der Hund bellt laut.", "word": "Hund", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Auto fährt schnell.", "word": "fährt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Blume ist schön.", "word": "schön", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Mama kocht Suppe.", "word": "kocht", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Ball ist rund.", "word": "Ball", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Papa liest ein Buch.", "word": "liest", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Haus ist groß.", "word": "groß", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Katze schläft.", "word": "Katze", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Baum wächst hoch.", "word": "Baum", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Wir spielen gern.", "word": "spielen", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Wetter ist warm.", "word": "warm", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Sonne scheint hell.", "word": "Sonne", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Vogel singt.", "word": "singt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Brot schmeckt gut.", "word": "gut", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Maus ist klein.", "word": "Maus", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Oma backt Kuchen.", "word": "backt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Apfel ist süß.", "word": "süß", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Kind lacht.", "word": "Kind", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Fisch schwimmt.", "word": "schwimmt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Milch ist weiß.", "word": "weiß", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Papa arbeitet viel.", "word": "arbeitet", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Stuhl ist alt.", "word": "alt", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Lampe leuchtet.", "word": "Lampe", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Wir tanzen zusammen.", "word": "tanzen", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Eis ist kalt.", "word": "kalt", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Tisch steht hier.", "word": "Tisch", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Mama singt schön.", "word": "singt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Blume duftet süß.", "word": "süß", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Hase hüpft.", "word": "Hase", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Opa erzählt Geschichten.", "word": "erzählt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Gras ist grün.", "word": "grün", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Uhr tickt.", "word": "Uhr", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Hund rennt schnell.", "word": "rennt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Meer ist blau.", "word": "blau", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Banane ist gelb.", "word": "Banane", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Wir malen Bilder.", "word": "malen", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Himmel ist blau.", "word": "blau", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Pferd galoppiert.", "word": "Pferd", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Kinder lachen.", "word": "lachen", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Rose ist rot.", "word": "rot", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Zug fährt.", "word": "Zug", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Oma kocht gerne.", "word": "kocht", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Buch ist dick.", "word": "dick", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Schule ist nah.", "word": "Schule", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Papa schreibt einen Brief.", "word": "schreibt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Wasser ist klar.", "word": "klar", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Löwe brüllt.", "word": "Löwe", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Wir kaufen ein.", "word": "kaufen", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Suppe ist heiß.", "word": "heiß", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Baby weint.", "word": "Baby", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Wind weht.", "word": "weht", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Fell ist weich.", "word": "weich", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]}
    ]
    
    grade3_examples = [
        {"sentence": "Die Lehrerin erklärt die Aufgabe sehr deutlich.", "word": "erklärt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das neue Fahrrad steht im Garten.", "word": "neue", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Mein Bruder spielt gerne Fußball.", "word": "Bruder", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
    ]
    
    examples = grade2_examples if grade == 2 else grade3_examples
    
    # Shuffle and select random subset to ensure variety
    import random
    shuffled_examples = random.sample(examples, min(count * 3, len(examples)))
    
    for i in range(min(count, len(shuffled_examples))):
        example = shuffled_examples[i]
        
        problem = GermanProblem(
            question=f'Welche Wortart ist das unterstrichene Wort?\n\nSatz: "{example["sentence"]}"\nWort: "{example["word"]}"',
            question_type="word_types",
            options=example["options"],
            correct_answer=example["type"],
            problem_data={"sentence": example["sentence"], "target_word": example["word"]}
        )
        problems.append(problem)
    
    return problems

async def generate_fill_blank_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate fill-in-the-blank problems using massively expanded content"""
    problems = []
    
    # Try AI generation first
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            ai_problems = await generate_ai_fill_blank_problems(count, grade, settings)
            if ai_problems:
                return ai_problems
    except Exception as e:
        logging.error(f"AI fill-blank generation failed: {e}")
    
    # Import massively expanded content
    try:
        if grade == 2:
            from german_content_complete import GRADE2_FILL_BLANK_COMPLETE
            templates = GRADE2_FILL_BLANK_COMPLETE
        else:
            from german_grade3_content import GRADE3_FILL_BLANK_COMPLETE
            templates = GRADE3_FILL_BLANK_COMPLETE
        
        # Apply difficulty filtering
        difficulty = settings.difficulty_settings.get("spelling_difficulty", "medium")
        context_length = settings.difficulty_settings.get("fill_blank_context_length", "short")
        filtered_templates = apply_fill_blank_difficulty_filter(templates, difficulty, context_length)
        
        # Shuffle and select random subset to ensure massive variety
        import random
        available_templates = min(count * 3, len(filtered_templates))
        shuffled_templates = random.sample(filtered_templates, available_templates) if available_templates > 0 else filtered_templates
        
        for i in range(min(count, len(shuffled_templates))):
            template = shuffled_templates[i]
            
            problem = GermanProblem(
                question=f"Setze das richtige Wort ein:\n\n{template['text']}",
                question_type="fill_blank",
                options=template["options"],
                correct_answer=template["answer"],
                problem_data={"original_text": template["text"]}
            )
            problems.append(problem)
        
        return problems
        
    except ImportError:
        # Fallback to smaller dataset if imports fail
        templates = [
            {"text": "Der ___ bellt laut.", "answer": "Hund", "options": ["Hund", "Katze", "Vogel"]},
            {"text": "Die ___ miaut leise.", "answer": "Katze", "options": ["Katze", "Hund", "Maus"]},
            {"text": "Mama ___ in der Küche.", "answer": "kocht", "options": ["kocht", "singt", "tanzt"]},
        ]
    
    # Shuffle and select random subset to ensure massive variety
    import random
    shuffled_templates = random.sample(templates, min(count * 3, len(templates)))
    
    for i in range(min(count, len(shuffled_templates))):
        template = shuffled_templates[i]
        
        problem = GermanProblem(
            question=f"Setze das richtige Wort ein:\n\n{template['text']}",
            question_type="fill_blank",
            options=template["options"],
            correct_answer=template["answer"],
            problem_data={"original_text": template["text"]}
        )
        problems.append(problem)
    
    return problems

async def generate_grammar_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate basic grammar problems"""
    problems = []
    
    grade2_grammar = [
        {"question": "Wie lautet die Mehrzahl von 'Hund'?", "answer": "Hunde", "options": ["Hunde", "Hunds", "Hunden"]},
        {"question": "Welcher Artikel gehört zu 'Haus'?", "answer": "das", "options": ["der", "die", "das"]},
        {"question": "Wie lautet die Mehrzahl von 'Kind'?", "answer": "Kinder", "options": ["Kinder", "Kinds", "Kindern"]},
        {"question": "Welcher Artikel gehört zu 'Schule'?", "answer": "die", "options": ["der", "die", "das"]}
    ]
    
    grade3_grammar = [
        {"question": "Welche Zeitform ist das: 'Ich bin gelaufen'?", "answer": "Perfekt", "options": ["Präsens", "Perfekt", "Präteritum"]},
        {"question": "Wie lautet die erste Person Singular von 'gehen' im Präteritum?", "answer": "ging", "options": ["gehe", "ging", "gegangen"]},
        {"question": "Welcher Fall ist 'dem Hund' (dem Hund geben)?", "answer": "Dativ", "options": ["Nominativ", "Akkusativ", "Dativ"]},
        {"question": "Wie lautet die Steigerung von 'gut'?", "answer": "besser", "options": ["guter", "besser", "gutster"]}
    ]
    
    grammar_list = grade2_grammar if grade == 2 else grade3_grammar
    
    for i in range(min(count, len(grammar_list))):
        grammar = random.choice(grammar_list)
        
        problem = GermanProblem(
            question=grammar["question"],
            question_type="grammar",
            options=grammar["options"],
            correct_answer=grammar["answer"]
        )
        problems.append(problem)
    
    return problems

async def generate_article_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate article identification problems"""
    problems = []
    
    article_words = [
        {"word": "Baum", "article": "der"},
        {"word": "Blume", "article": "die"},
        {"word": "Haus", "article": "das"},
        {"word": "Auto", "article": "das"},
        {"word": "Katze", "article": "die"},
        {"word": "Hund", "article": "der"},
        {"word": "Schule", "article": "die"},
        {"word": "Buch", "article": "das"}
    ]
    
    for i in range(min(count, len(article_words))):
        word_data = random.choice(article_words)
        
        problem = GermanProblem(
            question=f"Welcher Artikel gehört zu '{word_data['word']}'?",
            question_type="articles",
            options=["der", "die", "das"],
            correct_answer=word_data["article"]
        )
        problems.append(problem)
    
    return problems

async def generate_sentence_order_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate sentence ordering problems"""
    problems = []
    
    sentence_parts = [
        {"correct": "Der Hund bellt laut.", "scrambled": ["bellt", "Der", "laut", "Hund"]},
        {"correct": "Mama kocht das Essen.", "scrambled": ["kocht", "Essen", "Mama", "das"]},
        {"correct": "Wir gehen zur Schule.", "scrambled": ["gehen", "Schule", "Wir", "zur"]},
        {"correct": "Das Auto fährt schnell.", "scrambled": ["fährt", "Auto", "Das", "schnell"]}
    ]
    
    for i in range(min(count, len(sentence_parts))):
        sentence = random.choice(sentence_parts)
        
        problem = GermanProblem(
            question=f"Bringe die Wörter in die richtige Reihenfolge:\n{' - '.join(sentence['scrambled'])}",
            question_type="sentence_order",
            correct_answer=sentence["correct"],
            problem_data={"scrambled_words": sentence["scrambled"]}
        )
        problems.append(problem)
    
    return problems

# AI-powered German problem generation functions
async def generate_ai_spelling_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate AI spelling problems using static fallback content"""
    # For external deployment, use fallback content only
    return await generate_spelling_problems(count, grade, settings)

async def generate_ai_word_type_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate AI word type problems using static fallback content"""
    # For external deployment, use fallback content only
    return await generate_word_type_problems(count, grade, settings)

async def generate_ai_fill_blank_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate AI fill blank problems using static fallback content"""
    # For external deployment, use fallback content only
    return await generate_fill_blank_problems(count, grade, settings)

# English Challenge Generation Functions
async def generate_english_problems(grade: int, count: int = None) -> List[EnglishProblem]:
    """Generate AI-powered English language problems"""
    
    # Get English settings
    settings_doc = await db.english_settings.find_one()
    if not settings_doc:
        settings = EnglishSettings()
        await db.english_settings.insert_one(settings.dict())
    else:
        settings = EnglishSettings(**settings_doc)
    
    # Use configured problem count if not specified
    if count is None:
        count = settings.problem_count
    
    # Generate mix of problems based on enabled types
    problems = []
    enabled_types = [k for k, v in settings.problem_types.items() if v]
    
    if not enabled_types:
        enabled_types = ["vocabulary_de_en", "vocabulary_en_de", "simple_sentences"]  # fallback
    
    problems_per_type = count // len(enabled_types)
    remaining = count % len(enabled_types)
    
    for problem_type in enabled_types:
        type_count = problems_per_type + (1 if remaining > 0 else 0)
        remaining -= 1
        
        if problem_type == "vocabulary_de_en":
            problems.extend(await generate_vocabulary_de_en_problems(type_count, grade, settings))
        elif problem_type == "vocabulary_en_de":
            problems.extend(await generate_vocabulary_en_de_problems(type_count, grade, settings))
        elif problem_type == "simple_sentences":
            problems.extend(await generate_simple_sentence_problems(type_count, grade, settings))
        elif problem_type == "basic_grammar":
            problems.extend(await generate_basic_grammar_problems(type_count, grade, settings))
        elif problem_type == "colors_numbers":
            problems.extend(await generate_colors_numbers_problems(type_count, grade, settings))
        elif problem_type == "animals_objects":
            problems.extend(await generate_animals_objects_problems(type_count, grade, settings))
    
    # Shuffle the problems
    random.shuffle(problems)
    return problems[:count]

async def generate_vocabulary_de_en_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate German to English vocabulary problems using massively expanded content"""
    problems = []
    
    # Try AI generation first
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            ai_problems = await generate_ai_vocabulary_de_en_problems(count, grade, settings)
            if ai_problems:
                return ai_problems
    except Exception as e:
        logging.error(f"AI vocabulary DE->EN generation failed: {e}")
    
    # Import massively expanded content
    try:
        from english_content_expanded import ENGLISH_VOCABULARY_BASIC, ENGLISH_VOCABULARY_INTERMEDIATE
        
        if grade == 2 or settings.difficulty_settings.get("vocabulary_level") == "basic":
            vocab_list = ENGLISH_VOCABULARY_BASIC
        else:
            vocab_list = ENGLISH_VOCABULARY_BASIC + ENGLISH_VOCABULARY_INTERMEDIATE
    except ImportError:
        # Fallback to basic vocabulary if imports fail
        vocab_list = [
            {"english": "dog", "german": "Hund", "category": "animals"},
            {"english": "cat", "german": "Katze", "category": "animals"},
            {"english": "house", "german": "Haus", "category": "household"},
            {"english": "car", "german": "Auto", "category": "transport"},
            {"english": "tree", "german": "Baum", "category": "nature"},
            {"english": "water", "german": "Wasser", "category": "food"},
            {"english": "bread", "german": "Brot", "category": "food"},
            {"english": "apple", "german": "Apfel", "category": "food"},
            {"english": "school", "german": "Schule", "category": "places"},
            {"english": "book", "german": "Buch", "category": "objects"},
            {"english": "red", "german": "rot", "category": "colors"},
            {"english": "blue", "german": "blau", "category": "colors"},
            {"english": "big", "german": "groß", "category": "adjectives"},
            {"english": "small", "german": "klein", "category": "adjectives"},
            {"english": "good", "german": "gut", "category": "adjectives"},
            {"english": "ball", "german": "Ball", "category": "toys"},
            {"english": "mom", "german": "Mama", "category": "family"},
            {"english": "dad", "german": "Papa", "category": "family"},
            {"english": "child", "german": "Kind", "category": "family"},
            {"english": "friend", "german": "Freund", "category": "people"},
            {"english": "sun", "german": "Sonne", "category": "nature"},
            {"english": "moon", "german": "Mond", "category": "nature"},
            {"english": "flower", "german": "Blume", "category": "nature"},
            {"english": "bird", "german": "Vogel", "category": "animals"},
            {"english": "fish", "german": "Fisch", "category": "animals"},
            {"english": "mouse", "german": "Maus", "category": "animals"},
            {"english": "door", "german": "Tür", "category": "household"},
            {"english": "window", "german": "Fenster", "category": "household"},
            {"english": "table", "german": "Tisch", "category": "household"},
            {"english": "chair", "german": "Stuhl", "category": "household"},
            {"english": "warm", "german": "warm", "category": "adjectives"},
            {"english": "cold", "german": "kalt", "category": "adjectives"},
            {"english": "fast", "german": "schnell", "category": "adjectives"},
            {"english": "slow", "german": "langsam", "category": "adjectives"},
            {"english": "new", "german": "neu", "category": "adjectives"},
            {"english": "old", "german": "alt", "category": "adjectives"},
            {"english": "happy", "german": "glücklich", "category": "emotions"},
            {"english": "sad", "german": "traurig", "category": "emotions"},
            {"english": "milk", "german": "Milch", "category": "food"},
            {"english": "cheese", "german": "Käse", "category": "food"},
            {"english": "egg", "german": "Ei", "category": "food"},
            {"english": "meat", "german": "Fleisch", "category": "food"},
            {"english": "vegetable", "german": "Gemüse", "category": "food"},
            {"english": "fruit", "german": "Obst", "category": "food"},
            {"english": "banana", "german": "Banane", "category": "food"},
            {"english": "orange", "german": "Orange", "category": "food"},
            {"english": "lemon", "german": "Zitrone", "category": "food"},
            {"english": "grape", "german": "Traube", "category": "food"},
            {"english": "cherry", "german": "Kirsche", "category": "food"},
            {"english": "strawberry", "german": "Erdbeere", "category": "food"},
            {"english": "family", "german": "Familie", "category": "family"},
            {"english": "brother", "german": "Bruder", "category": "family"},
            {"english": "sister", "german": "Schwester", "category": "family"},
            {"english": "grandma", "german": "Oma", "category": "family"},
            {"english": "grandpa", "german": "Opa", "category": "family"},
            {"english": "aunt", "german": "Tante", "category": "family"},
            {"english": "uncle", "german": "Onkel", "category": "family"},
            {"english": "baby", "german": "Baby", "category": "family"},
            {"english": "boy", "german": "Junge", "category": "people"},
            {"english": "girl", "german": "Mädchen", "category": "people"},
            {"english": "man", "german": "Mann", "category": "people"},
            {"english": "woman", "german": "Frau", "category": "people"},
            {"english": "animal", "german": "Tier", "category": "animals"},
            {"english": "horse", "german": "Pferd", "category": "animals"},
            {"english": "cow", "german": "Kuh", "category": "animals"},
            {"english": "pig", "german": "Schwein", "category": "animals"},
            {"english": "sheep", "german": "Schaf", "category": "animals"},
            {"english": "goat", "german": "Ziege", "category": "animals"},
            {"english": "rabbit", "german": "Hase", "category": "animals"},
            {"english": "hamster", "german": "Hamster", "category": "animals"},
            {"english": "to play", "german": "spielen", "category": "verbs"},
            {"english": "to run", "german": "laufen", "category": "verbs"},
            {"english": "to go", "german": "gehen", "category": "verbs"},
            {"english": "to come", "german": "kommen", "category": "verbs"},
            {"english": "to eat", "german": "essen", "category": "verbs"},
            {"english": "to drink", "german": "trinken", "category": "verbs"},
            {"english": "to sleep", "german": "schlafen", "category": "verbs"},
            {"english": "to see", "german": "sehen", "category": "verbs"},
            {"english": "to hear", "german": "hören", "category": "verbs"},
            {"english": "to speak", "german": "sprechen", "category": "verbs"},
            {"english": "to read", "german": "lesen", "category": "verbs"},
            {"english": "to write", "german": "schreiben", "category": "verbs"},
            {"english": "to paint", "german": "malen", "category": "verbs"},
            {"english": "to sing", "german": "singen", "category": "verbs"},
            {"english": "to dance", "german": "tanzen", "category": "verbs"},
            {"english": "to jump", "german": "springen", "category": "verbs"},
            {"english": "to swim", "german": "schwimmen", "category": "verbs"},
            {"english": "to fly", "german": "fliegen", "category": "verbs"},
            {"english": "to drive", "german": "fahren", "category": "verbs"},
            {"english": "to work", "german": "arbeiten", "category": "verbs"},
            {"english": "to learn", "german": "lernen", "category": "verbs"},
            {"english": "to teach", "german": "lehren", "category": "verbs"},
            {"english": "to help", "german": "helfen", "category": "verbs"},
            {"english": "to buy", "german": "kaufen", "category": "verbs"},
            {"english": "to sell", "german": "verkaufen", "category": "verbs"},
            {"english": "to give", "german": "geben", "category": "verbs"},
            {"english": "to take", "german": "nehmen", "category": "verbs"},
            {"english": "to have", "german": "haben", "category": "verbs"},
            {"english": "to be", "german": "sein", "category": "verbs"},
            {"english": "to become", "german": "werden", "category": "verbs"},
            {"english": "to make", "german": "machen", "category": "verbs"},
            {"english": "to do", "german": "tun", "category": "verbs"},
            {"english": "can", "german": "können", "category": "modal_verbs"},
            {"english": "must", "german": "müssen", "category": "modal_verbs"},
            {"english": "want", "german": "wollen", "category": "modal_verbs"},
            {"english": "like", "german": "mögen", "category": "verbs"},
            {"english": "love", "german": "lieben", "category": "verbs"},
            {"english": "hate", "german": "hassen", "category": "verbs"},
            {"english": "need", "german": "brauchen", "category": "verbs"},
            {"english": "get", "german": "bekommen", "category": "verbs"},
            {"english": "lose", "german": "verlieren", "category": "verbs"},
            {"english": "find", "german": "finden", "category": "verbs"},
            {"english": "search", "german": "suchen", "category": "verbs"},
            {"english": "wait", "german": "warten", "category": "verbs"},
            {"english": "stay", "german": "bleiben", "category": "verbs"},
            {"english": "leave", "german": "verlassen", "category": "verbs"},
            {"english": "arrive", "german": "ankommen", "category": "verbs"},
            {"english": "begin", "german": "beginnen", "category": "verbs"},
            {"english": "stop", "german": "aufhören", "category": "verbs"},
            {"english": "continue", "german": "weitermachen", "category": "verbs"},
            {"english": "number", "german": "Nummer", "category": "numbers"},
            {"english": "one", "german": "eins", "category": "numbers"},
            {"english": "two", "german": "zwei", "category": "numbers"},
            {"english": "three", "german": "drei", "category": "numbers"},
            {"english": "four", "german": "vier", "category": "numbers"},
            {"english": "five", "german": "fünf", "category": "numbers"},
            {"english": "six", "german": "sechs", "category": "numbers"},
            {"english": "seven", "german": "sieben", "category": "numbers"},
            {"english": "eight", "german": "acht", "category": "numbers"},
            {"english": "nine", "german": "neun", "category": "numbers"},
            {"english": "ten", "german": "zehn", "category": "numbers"}
        ]
    
    # Generate wrong answers based on category and common mistakes
    def generate_wrong_answers(correct_word, category, vocab_list):
        """Generate plausible wrong answers for vocabulary questions"""
        wrong_answers = []
        
        # Get words from same category
        same_category = [item["english"] for item in vocab_list 
                        if item.get("category") == category and item["english"] != correct_word]
        
        # Add 2-3 words from same category if available
        if same_category:
            wrong_answers.extend(random.sample(same_category, min(2, len(same_category))))
        
        # Add some common distractors based on category
        common_distractors = {
            "animals": ["cat", "dog", "bird", "fish", "mouse", "horse", "cow"],
            "food": ["bread", "milk", "apple", "water", "cheese", "meat"],
            "colors": ["red", "blue", "green", "yellow", "black", "white"],
            "family": ["mom", "dad", "brother", "sister", "child", "baby"],
            "household": ["house", "door", "window", "table", "chair", "bed"],
            "verbs": ["go", "come", "eat", "drink", "sleep", "play", "work"],
            "numbers": ["one", "two", "three", "four", "five", "six", "seven"],
            "adjectives": ["big", "small", "good", "bad", "new", "old", "fast"]
        }
        
        if category in common_distractors:
            category_distractors = [word for word in common_distractors[category] 
                                  if word != correct_word and word not in wrong_answers]
            wrong_answers.extend(random.sample(category_distractors, 
                                             min(2, len(category_distractors))))
        
        # Ensure we have exactly 3 wrong answers
        while len(wrong_answers) < 3:
            # Add random words from other categories
            random_word = random.choice(vocab_list)["english"]
            if random_word != correct_word and random_word not in wrong_answers:
                wrong_answers.append(random_word)
        
        return wrong_answers[:3]
    
    # Shuffle and select random subset to ensure variety
    shuffled_vocab = random.sample(vocab_list, min(count * 2, len(vocab_list)))
    
    for i in range(min(count, len(shuffled_vocab))):
        vocab_item = shuffled_vocab[i]
        
        # Generate wrong answers
        wrong_answers = generate_wrong_answers(
            vocab_item["english"], 
            vocab_item.get("category", "general"), 
            vocab_list
        )
        
        options = [vocab_item["english"]] + wrong_answers
        random.shuffle(options)
        
        problem = EnglishProblem(
            question=f"Was bedeutet '{vocab_item['german']}' auf Englisch?",
            question_type="vocabulary_de_en",
            options=options,
            correct_answer=vocab_item["english"],
            problem_data={
                "german_word": vocab_item["german"],
                "category": vocab_item.get("category", "general")
            }
        )
        problems.append(problem)
    
    return problems

async def generate_vocabulary_en_de_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate English to German vocabulary problems"""
    problems = []
    
    # Try AI generation first
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            ai_problems = await generate_ai_vocabulary_en_de_problems(count, grade, settings)
            if ai_problems:
                return ai_problems
    except Exception as e:
        logging.error(f"AI vocabulary EN->DE generation failed: {e}")
    
    # Use same vocabulary list but reverse the question
    grade2_vocabulary = [
        {"german": "Hund", "english": "dog", "wrong": ["Katze", "Vogel", "Fisch"]},
        {"german": "Katze", "english": "cat", "wrong": ["Hund", "Maus", "Vogel"]},
        {"german": "Auto", "english": "car", "wrong": ["Bus", "Zug", "Fahrrad"]},
        {"german": "Haus", "english": "house", "wrong": ["Baum", "Auto", "Buch"]},
        {"german": "Baum", "english": "tree", "wrong": ["Blume", "Gras", "Haus"]},
        {"german": "Wasser", "english": "water", "wrong": ["Milch", "Saft", "Tee"]},
        {"german": "Brot", "english": "bread", "wrong": ["Kuchen", "Apfel", "Käse"]},
        {"german": "Apfel", "english": "apple", "wrong": ["Banane", "Orange", "Traube"]},
        {"german": "Schule", "english": "school", "wrong": ["Haus", "Park", "Laden"]},
        {"german": "Buch", "english": "book", "wrong": ["Stift", "Papier", "Tisch"]},
        {"german": "rot", "english": "red", "wrong": ["blau", "grün", "gelb"]},
        {"german": "blau", "english": "blue", "wrong": ["rot", "grün", "schwarz"]},
        {"german": "groß", "english": "big", "wrong": ["klein", "lang", "schnell"]},
        {"german": "klein", "english": "small", "wrong": ["groß", "hoch", "breit"]},
        {"german": "gut", "english": "good", "wrong": ["schlecht", "schnell", "langsam"]},
        {"german": "Ball", "english": "ball", "wrong": ["Spielzeug", "Spiel", "Stock"]},
        {"german": "Mama", "english": "mom", "wrong": ["Papa", "Schwester", "Bruder"]},
        {"german": "Papa", "english": "dad", "wrong": ["Mama", "Onkel", "Opa"]},
        {"german": "Kind", "english": "child", "wrong": ["Erwachsener", "Baby", "Eltern"]},
        {"german": "Freund", "english": "friend", "wrong": ["Feind", "Lehrer", "Arzt"]},
        {"german": "Sonne", "english": "sun", "wrong": ["Mond", "Stern", "Wolke"]},
        {"german": "Mond", "english": "moon", "wrong": ["Sonne", "Stern", "Planet"]},
        {"german": "Blume", "english": "flower", "wrong": ["Baum", "Gras", "Blatt"]},
        {"german": "Vogel", "english": "bird", "wrong": ["Fisch", "Katze", "Hund"]},
        {"german": "Fisch", "english": "fish", "wrong": ["Vogel", "Katze", "Maus"]},
        {"german": "Maus", "english": "mouse", "wrong": ["Katze", "Hund", "Vogel"]},
        {"german": "Tür", "english": "door", "wrong": ["Fenster", "Wand", "Dach"]},
        {"german": "Fenster", "english": "window", "wrong": ["Tür", "Wand", "Boden"]},
        {"german": "Tisch", "english": "table", "wrong": ["Stuhl", "Bett", "Sofa"]},
        {"german": "Stuhl", "english": "chair", "wrong": ["Tisch", "Bett", "Lampe"]},
        {"german": "warm", "english": "warm", "wrong": ["kalt", "heiß", "kühl"]},
        {"german": "kalt", "english": "cold", "wrong": ["warm", "heiß", "kühl"]},
        {"german": "schnell", "english": "fast", "wrong": ["langsam", "groß", "klein"]},
        {"german": "langsam", "english": "slow", "wrong": ["schnell", "rasch", "eilig"]},
        {"german": "neu", "english": "new", "wrong": ["alt", "gebraucht", "kaputt"]},
        {"german": "alt", "english": "old", "wrong": ["neu", "jung", "frisch"]},
        {"german": "glücklich", "english": "happy", "wrong": ["traurig", "wütend", "müde"]},
        {"german": "traurig", "english": "sad", "wrong": ["glücklich", "froh", "fröhlich"]},
        {"german": "Milch", "english": "milk", "wrong": ["Wasser", "Saft", "Tee"]},
        {"german": "Käse", "english": "cheese", "wrong": ["Brot", "Butter", "Fleisch"]},
        {"german": "Ei", "english": "egg", "wrong": ["Huhn", "Milch", "Brot"]},
        {"german": "Fleisch", "english": "meat", "wrong": ["Brot", "Obst", "Gemüse"]},
        {"german": "Gemüse", "english": "vegetable", "wrong": ["Obst", "Fleisch", "Brot"]},
        {"german": "Obst", "english": "fruit", "wrong": ["Gemüse", "Fleisch", "Brot"]},
        {"german": "Banane", "english": "banana", "wrong": ["Apfel", "Orange", "Traube"]},
        {"german": "Orange", "english": "orange", "wrong": ["Apfel", "Banane", "Zitrone"]},
        {"german": "Zitrone", "english": "lemon", "wrong": ["Orange", "Apfel", "Limette"]},
        {"german": "Traube", "english": "grape", "wrong": ["Beere", "Kirsche", "Pflaume"]},
        {"german": "Kirsche", "english": "cherry", "wrong": ["Traube", "Beere", "Pflaume"]},
        {"german": "Erdbeere", "english": "strawberry", "wrong": ["Kirsche", "Traube", "Beere"]},
        {"german": "Familie", "english": "family", "wrong": ["Freunde", "Leute", "Gruppe"]},
        {"german": "Bruder", "english": "brother", "wrong": ["Schwester", "Cousin", "Freund"]},
        {"german": "Schwester", "english": "sister", "wrong": ["Bruder", "Cousine", "Freundin"]},
        {"german": "Oma", "english": "grandma", "wrong": ["Mama", "Tante", "Schwester"]},
        {"german": "Opa", "english": "grandpa", "wrong": ["Papa", "Onkel", "Bruder"]},
        {"german": "Tante", "english": "aunt", "wrong": ["Mama", "Schwester", "Cousine"]},
        {"german": "Onkel", "english": "uncle", "wrong": ["Papa", "Bruder", "Cousin"]},
        {"german": "Baby", "english": "baby", "wrong": ["Kind", "Erwachsener", "Teenager"]},
        {"german": "Junge", "english": "boy", "wrong": ["Mädchen", "Mann", "Kind"]},
        {"german": "Mädchen", "english": "girl", "wrong": ["Junge", "Frau", "Kind"]},
        {"german": "Mann", "english": "man", "wrong": ["Frau", "Junge", "Person"]},
        {"german": "Frau", "english": "woman", "wrong": ["Mann", "Mädchen", "Person"]},
        {"german": "Tier", "english": "animal", "wrong": ["Pflanze", "Person", "Ding"]},
        {"german": "Pferd", "english": "horse", "wrong": ["Kuh", "Schwein", "Schaf"]},
        {"german": "Kuh", "english": "cow", "wrong": ["Pferd", "Schwein", "Ziege"]},
        {"german": "Schwein", "english": "pig", "wrong": ["Kuh", "Pferd", "Schaf"]},
        {"german": "Schaf", "english": "sheep", "wrong": ["Ziege", "Kuh", "Schwein"]},
        {"german": "Ziege", "english": "goat", "wrong": ["Schaf", "Kuh", "Pferd"]},
        {"german": "Hase", "english": "rabbit", "wrong": ["Maus", "Katze", "Hamster"]},
        {"german": "Hamster", "english": "hamster", "wrong": ["Maus", "Hase", "Ratte"]},
        {"german": "eins", "english": "one", "wrong": ["zwei", "drei", "vier"]},
        {"german": "zwei", "english": "two", "wrong": ["eins", "drei", "vier"]},
        {"german": "drei", "english": "three", "wrong": ["zwei", "vier", "fünf"]},
        {"german": "vier", "english": "four", "wrong": ["drei", "fünf", "sechs"]},
        {"german": "fünf", "english": "five", "wrong": ["vier", "sechs", "sieben"]},
        {"german": "sechs", "english": "six", "wrong": ["fünf", "sieben", "acht"]},
        {"german": "sieben", "english": "seven", "wrong": ["sechs", "acht", "neun"]},
        {"german": "acht", "english": "eight", "wrong": ["sieben", "neun", "zehn"]},
        {"german": "neun", "english": "nine", "wrong": ["acht", "zehn", "elf"]},
        {"german": "zehn", "english": "ten", "wrong": ["neun", "elf", "zwölf"]}
    ]
    
    grade3_vocabulary = [
        {"german": "Wissenschaft", "english": "science", "wrong": ["Kunst", "Geschichte", "Musik"]},
        {"german": "Experiment", "english": "experiment", "wrong": ["Test", "Spiel", "Lektion"]},
        {"german": "Forschung", "english": "research", "wrong": ["Studium", "Hausaufgabe", "Projekt"]},
        {"german": "Entdeckung", "english": "discovery", "wrong": ["Erfindung", "Schöpfung", "Fund"]},
        {"german": "Erfindung", "english": "invention", "wrong": ["Entdeckung", "Schöpfung", "Idee"]},
        {"german": "Technologie", "english": "technology", "wrong": ["Wissenschaft", "Computer", "Maschine"]},
        {"german": "Computer", "english": "computer", "wrong": ["Fernseher", "Radio", "Telefon"]},
        {"german": "Internet", "english": "internet", "wrong": ["Computer", "Website", "E-Mail"]},
        {"german": "Programm", "english": "program", "wrong": ["Computer", "Software", "Spiel"]},
        {"german": "Software", "english": "software", "wrong": ["Hardware", "Computer", "Programm"]},
        {"german": "Roboter", "english": "robot", "wrong": ["Maschine", "Computer", "Android"]},
        {"german": "Maschine", "english": "machine", "wrong": ["Roboter", "Werkzeug", "Gerät"]},
        {"german": "Werkzeug", "english": "tool", "wrong": ["Maschine", "Instrument", "Gerät"]},
        {"german": "Instrument", "english": "instrument", "wrong": ["Werkzeug", "Gerät", "Maschine"]},
        {"german": "Gerät", "english": "device", "wrong": ["Maschine", "Werkzeug", "Gadget"]},
        {"german": "Energie", "english": "energy", "wrong": ["Kraft", "Elektrizität", "Brennstoff"]},
        {"german": "Elektrizität", "english": "electricity", "wrong": ["Energie", "Kraft", "Batterie"]},
        {"german": "Batterie", "english": "battery", "wrong": ["Elektrizität", "Kraft", "Energie"]},
        {"german": "Motor", "english": "engine", "wrong": ["Maschine", "Motor", "Gerät"]},
        {"german": "Fahrzeug", "english": "vehicle", "wrong": ["Auto", "Transport", "Maschine"]}
    ]
    
    vocabulary_list = grade2_vocabulary if grade == 2 else grade3_vocabulary
    
    # Shuffle and select random subset to ensure variety
    import random
    shuffled_vocab = random.sample(vocabulary_list, min(count * 3, len(vocabulary_list)))
    
    for i in range(min(count, len(shuffled_vocab))):
        vocab = shuffled_vocab[i]
        options = [vocab["german"]] + vocab["wrong"]
        random.shuffle(options)
        
        problem = EnglishProblem(
            question=f"Was bedeutet '{vocab['english']}' auf Deutsch?",
            question_type="vocabulary_en_de",
            options=options,
            correct_answer=vocab["german"],
            problem_data={"english_word": vocab["english"]}
        )
        problems.append(problem)
    
    return problems

async def generate_simple_sentence_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate simple sentence translation problems using massively expanded content"""
    problems = []
    
    # Import massively expanded content
    try:
        from english_content_expanded import ENGLISH_SENTENCES_BASIC, ENGLISH_SENTENCES_INTERMEDIATE
        
        if grade == 2 or settings.difficulty_settings.get("sentence_level") == "basic":
            sentences = ENGLISH_SENTENCES_BASIC
        else:
            sentences = ENGLISH_SENTENCES_BASIC + ENGLISH_SENTENCES_INTERMEDIATE
    except ImportError:
        # Fallback to basic sentences if imports fail
        sentences = [
            {"german": "Ich gehe zur Schule.", "english": "I go to school.", "category": "daily_life", "wrong": ["I walk to school.", "I come to school.", "I run to school."]},
            {"german": "Das ist mein Haus.", "english": "This is my house.", "category": "family", "wrong": ["That is my house.", "This is my home.", "This is our house."]},
            {"german": "Die Katze ist klein.", "english": "The cat is small.", "category": "animals", "wrong": ["The cat is little.", "The cat is tiny.", "The cat is young."]},
            {"german": "Ich esse einen Apfel.", "english": "I eat an apple.", "category": "food", "wrong": ["I have an apple.", "I like an apple.", "I want an apple."]},
            {"german": "Meine Mutter kocht.", "english": "My mother cooks.", "category": "family", "wrong": ["My mother works.", "My mother helps.", "My mother cleans."]},
            {"german": "Der Hund ist braun.", "english": "The dog is brown.", "category": "animals", "wrong": ["The dog is big.", "The dog is nice.", "The dog is old."]},
            {"german": "Ich trinke Wasser.", "english": "I drink water.", "category": "food", "wrong": ["I need water.", "I like water.", "I want water."]},
            {"german": "Das Auto ist rot.", "english": "The car is red.", "category": "transport", "wrong": ["The car is new.", "The car is fast.", "The car is big."]},
            {"german": "Wir spielen zusammen.", "english": "We play together.", "category": "activities", "wrong": ["We work together.", "We learn together.", "We eat together."]},
            {"german": "Die Sonne scheint.", "english": "The sun shines.", "category": "weather", "wrong": ["The sun is hot.", "The sun is bright.", "The sun is yellow."]},
            {"german": "Ich lese ein Buch.", "english": "I read a book.", "category": "activities", "wrong": ["I have a book.", "I want a book.", "I like a book."]},
            {"german": "Der Ball ist rund.", "english": "The ball is round.", "category": "toys", "wrong": ["The ball is big.", "The ball is red.", "The ball is new."]},
            {"german": "Mama singt ein Lied.", "english": "Mom sings a song.", "category": "family", "wrong": ["Mom knows a song.", "Mom likes a song.", "Mom hears a song."]},
            {"german": "Es regnet heute.", "english": "It rains today.", "category": "weather", "wrong": ["It's wet today.", "It's cold today.", "It's cloudy today."]},
            {"german": "Ich bin müde.", "english": "I am tired.", "category": "feelings", "wrong": ["I am sleepy.", "I am sad.", "I am sick."]},
            {"german": "Der Baum ist hoch.", "english": "The tree is tall.", "category": "nature", "wrong": ["The tree is big.", "The tree is old.", "The tree is green."]},
            {"german": "Wir haben Hunger.", "english": "We are hungry.", "category": "feelings", "wrong": ["We need food.", "We want food.", "We like food."]},
            {"german": "Das Wetter ist schön.", "english": "The weather is nice.", "category": "weather", "wrong": ["The weather is good.", "The weather is warm.", "The weather is sunny."]},
            {"german": "Ich helfe Papa.", "english": "I help Dad.", "category": "family", "wrong": ["I like Dad.", "I see Dad.", "I call Dad."]},
            {"german": "Die Blumen sind bunt.", "english": "The flowers are colorful.", "category": "nature", "wrong": ["The flowers are pretty.", "The flowers are nice.", "The flowers are small."]}
        ]
    
    # Shuffle and select random subset to ensure variety
    import random
    shuffled_sentences = random.sample(sentences, min(count * 3, len(sentences)))
    
    for i in range(min(count, len(shuffled_sentences))):
        sentence = shuffled_sentences[i]
        
        # Handle both old format (with "wrong" key) and new format (without "wrong" key)
        if "wrong" in sentence:
            options = [sentence["english"]] + sentence["wrong"]
        else:
            # Generate wrong options based on category or use generic ones
            wrong_options = [
                f"I {sentence['english'].split(' ', 1)[1] if ' ' in sentence['english'] else 'do something'}",
                f"We {sentence['english'].split(' ', 1)[1] if ' ' in sentence['english'] else 'do something'}",
                f"They {sentence['english'].split(' ', 1)[1] if ' ' in sentence['english'] else 'do something'}"
            ]
            options = [sentence["english"]] + wrong_options[:2]
        
        random.shuffle(options)
        
        problem = EnglishProblem(
            question=f"Wie übersetzt man diesen Satz ins Englische?\n\n'{sentence['german']}'",
            question_type="simple_sentences",
            options=options,
            correct_answer=sentence["english"],
            problem_data={"german_sentence": sentence["german"], "category": sentence.get("category", "general")}
        )
        problems.append(problem)
    
    return problems

async def generate_basic_grammar_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate basic English grammar problems"""
    problems = []
    
    grade2_grammar = [
        {"question": "Wähle die richtige Form: 'I ___ a student.'", "answer": "am", "options": ["am", "is", "are"]},
        {"question": "Wähle die richtige Form: 'She ___ happy.'", "answer": "is", "options": ["am", "is", "are"]},
        {"question": "Wähle die richtige Form: 'We ___ friends.'", "answer": "are", "options": ["am", "is", "are"]},
        {"question": "Wähle die richtige Form: 'The cat ___ sleeping.'", "answer": "is", "options": ["am", "is", "are"]},
        {"question": "Wähle die richtige Form: 'I ___ a dog.'", "answer": "have", "options": ["have", "has", "had"]},
        {"question": "Wähle die richtige Form: 'She ___ a book.'", "answer": "has", "options": ["have", "has", "had"]},
        {"question": "Wähle die richtige Form: 'We ___ two cats.'", "answer": "have", "options": ["have", "has", "had"]},
        {"question": "Wähle die richtige Form: 'He ___ to school.'", "answer": "goes", "options": ["go", "goes", "going"]},
        {"question": "Wähle die richtige Form: 'I ___ to school.'", "answer": "go", "options": ["go", "goes", "going"]},
        {"question": "Wähle die richtige Form: 'They ___ football.'", "answer": "play", "options": ["play", "plays", "playing"]}
    ]
    
    grade3_grammar = [
        {"question": "Wähle die richtige Zeit: 'Yesterday I ___ to the park.'", "answer": "went", "options": ["go", "went", "will go"]},
        {"question": "Wähle die richtige Zeit: 'Tomorrow we ___ shopping.'", "answer": "will go", "options": ["go", "went", "will go"]},
        {"question": "Wähle die richtige Zeit: 'She ___ her homework now.'", "answer": "is doing", "options": ["does", "did", "is doing"]},
        {"question": "Wähle die richtige Form: 'This book is ___ than that one.'", "answer": "better", "options": ["good", "better", "best"]},
        {"question": "Wähle die richtige Form: 'She is the ___ student in class.'", "answer": "best", "options": ["good", "better", "best"]},
        {"question": "Wähle die richtige Form: 'I have ___ books than you.'", "answer": "more", "options": ["much", "more", "most"]},
        {"question": "Wähle die richtige Form: 'Can you help ___?'", "answer": "me", "options": ["I", "me", "my"]},
        {"question": "Wähle die richtige Form: '___ book is this?'", "answer": "Whose", "options": ["Who", "Whose", "Which"]},
        {"question": "Wähle die richtige Form: '___ are you going?'", "answer": "Where", "options": ["What", "Where", "When"]},
        {"question": "Wähle die richtige Form: 'I don't have ___ money.'", "answer": "any", "options": ["some", "any", "no"]}
    ]
    
    grammar_list = grade2_grammar if grade == 2 else grade3_grammar
    
    for i in range(min(count, len(grammar_list))):
        grammar = random.choice(grammar_list)
        
        problem = EnglishProblem(
            question=grammar["question"],
            question_type="basic_grammar",
            options=grammar["options"],
            correct_answer=grammar["answer"]
        )
        problems.append(problem)
    
    return problems

async def generate_colors_numbers_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate colors and numbers problems"""
    problems = []
    
    colors_numbers = [
        {"german": "rot", "english": "red", "wrong": ["blue", "green", "yellow"]},
        {"german": "blau", "english": "blue", "wrong": ["red", "green", "black"]},
        {"german": "grün", "english": "green", "wrong": ["red", "blue", "yellow"]},
        {"german": "gelb", "english": "yellow", "wrong": ["red", "blue", "green"]},
        {"german": "schwarz", "english": "black", "wrong": ["white", "gray", "brown"]},
        {"german": "weiß", "english": "white", "wrong": ["black", "gray", "silver"]},
        {"german": "braun", "english": "brown", "wrong": ["black", "gray", "tan"]},
        {"german": "rosa", "english": "pink", "wrong": ["red", "purple", "orange"]},
        {"german": "lila", "english": "purple", "wrong": ["pink", "blue", "violet"]},
        {"german": "orange", "english": "orange", "wrong": ["red", "yellow", "pink"]},
        {"german": "eins", "english": "one", "wrong": ["two", "three", "four"]},
        {"german": "zwei", "english": "two", "wrong": ["one", "three", "four"]},
        {"german": "drei", "english": "three", "wrong": ["two", "four", "five"]},
        {"german": "vier", "english": "four", "wrong": ["three", "five", "six"]},
        {"german": "fünf", "english": "five", "wrong": ["four", "six", "seven"]},
        {"german": "sechs", "english": "six", "wrong": ["five", "seven", "eight"]},
        {"german": "sieben", "english": "seven", "wrong": ["six", "eight", "nine"]},
        {"german": "acht", "english": "eight", "wrong": ["seven", "nine", "ten"]},
        {"german": "neun", "english": "nine", "wrong": ["eight", "ten", "eleven"]},
        {"german": "zehn", "english": "ten", "wrong": ["nine", "eleven", "twelve"]}
    ]
    
    for i in range(min(count, len(colors_numbers))):
        item = random.choice(colors_numbers)
        options = [item["english"]] + item["wrong"]
        random.shuffle(options)
        
        problem = EnglishProblem(
            question=f"Was bedeutet '{item['german']}' auf Englisch?",
            question_type="colors_numbers",
            options=options,
            correct_answer=item["english"],
            problem_data={"german_word": item["german"]}
        )
        problems.append(problem)
    
    return problems

async def generate_animals_objects_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate animals and objects problems"""
    problems = []
    
    animals_objects = [
        {"german": "Hund", "english": "dog", "wrong": ["cat", "bird", "fish"]},
        {"german": "Katze", "english": "cat", "wrong": ["dog", "mouse", "bird"]},
        {"german": "Vogel", "english": "bird", "wrong": ["fish", "cat", "dog"]},
        {"german": "Fisch", "english": "fish", "wrong": ["bird", "cat", "mouse"]},
        {"german": "Pferd", "english": "horse", "wrong": ["cow", "pig", "sheep"]},
        {"german": "Kuh", "english": "cow", "wrong": ["horse", "pig", "goat"]},
        {"german": "Schwein", "english": "pig", "wrong": ["cow", "horse", "sheep"]},
        {"german": "Schaf", "english": "sheep", "wrong": ["goat", "cow", "pig"]},
        {"german": "Maus", "english": "mouse", "wrong": ["cat", "rat", "hamster"]},
        {"german": "Hase", "english": "rabbit", "wrong": ["mouse", "cat", "hamster"]},
        {"german": "Tisch", "english": "table", "wrong": ["chair", "bed", "sofa"]},
        {"german": "Stuhl", "english": "chair", "wrong": ["table", "bed", "lamp"]},
        {"german": "Bett", "english": "bed", "wrong": ["chair", "table", "sofa"]},
        {"german": "Lampe", "english": "lamp", "wrong": ["light", "candle", "torch"]},
        {"german": "Fenster", "english": "window", "wrong": ["door", "wall", "floor"]},
        {"german": "Tür", "english": "door", "wrong": ["window", "wall", "gate"]},
        {"german": "Auto", "english": "car", "wrong": ["bus", "train", "bike"]},
        {"german": "Bus", "english": "bus", "wrong": ["car", "train", "truck"]},
        {"german": "Zug", "english": "train", "wrong": ["bus", "car", "plane"]},
        {"german": "Flugzeug", "english": "airplane", "wrong": ["train", "car", "helicopter"]}
    ]
    
    for i in range(min(count, len(animals_objects))):
        item = random.choice(animals_objects)
        options = [item["english"]] + item["wrong"]
        random.shuffle(options)
        
        problem = EnglishProblem(
            question=f"Was bedeutet '{item['german']}' auf Englisch?",
            question_type="animals_objects",
            options=options,
            correct_answer=item["english"],
            problem_data={"german_word": item["german"]}
        )
        problems.append(problem)
    
    return problems

# AI-powered English problem generation functions
async def generate_ai_vocabulary_de_en_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate AI vocabulary DE-EN problems using static fallback content"""
    # For external deployment, use fallback content only
    return await generate_vocabulary_de_en_problems(count, grade, settings)

async def generate_ai_vocabulary_en_de_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate AI vocabulary EN-DE problems using static fallback content"""
    # For external deployment, use fallback content only
    return await generate_vocabulary_en_de_problems(count, grade, settings)

async def generate_ai_simple_sentence_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate AI simple sentence problems using static fallback content"""
    # For external deployment, use fallback content only
    return await generate_simple_sentence_problems(count, grade, settings)

# Helper functions
def get_current_week_start():
    today = datetime.now()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

async def generate_math_problems(problem_type: str, grade: int, count: int, settings: MathSettings) -> List[MathProblem]:
    """Generate math problems with specific type, grade, count and settings"""
    
    problems = []
    
    if problem_type == "addition":
        for i in range(count):
            if grade == 2:
                # Grade 2: Numbers up to 20
                a = random.randint(1, 15)
                b = random.randint(1, 20 - a)
                answer = a + b
                wrong_answers = [answer + 1, answer - 1, answer + 2]
            else:  # Grade 3
                # Grade 3: Numbers up to 100
                a = random.randint(10, 80)
                b = random.randint(1, 100 - a)
                answer = a + b
                wrong_answers = [answer + 5, answer - 5, answer + 10]
            
            options = [str(answer)] + [str(w) for w in wrong_answers]
            random.shuffle(options)
            
            problem = MathProblem(
                question=f"{a} + {b} = ?",
                question_type="addition",
                options=options,
                correct_answer=str(answer)
            )
            problems.append(problem)
    
    elif problem_type == "subtraction":
        for i in range(count):
            if grade == 2:
                a = random.randint(5, 20)
                b = random.randint(1, a)
                answer = a - b
                wrong_answers = [answer + 1, answer - 1, answer + 2]
            else:  # Grade 3
                a = random.randint(20, 100)
                b = random.randint(1, a)
                answer = a - b
                wrong_answers = [answer + 5, answer - 5, answer + 10]
            
            options = [str(answer)] + [str(w) for w in wrong_answers if w >= 0][:3]
            while len(options) < 4:
                options.append(str(random.randint(0, answer + 10)))
            random.shuffle(options)
            
            problem = MathProblem(
                question=f"{a} - {b} = ?",
                question_type="subtraction", 
                options=options,
                correct_answer=str(answer)
            )
            problems.append(problem)
    
    elif problem_type == "multiplication":
        for i in range(count):
            if grade == 2:
                a = random.randint(1, 5)
                b = random.randint(1, 5)
            else:  # Grade 3
                a = random.randint(2, 10)
                b = random.randint(2, 10)
            
            answer = a * b
            wrong_answers = [answer + a, answer - a, answer + b]
            
            options = [str(answer)] + [str(w) for w in wrong_answers if w > 0][:3]
            while len(options) < 4:
                options.append(str(random.randint(1, answer + 20)))
            random.shuffle(options)
            
            problem = MathProblem(
                question=f"{a} × {b} = ?",
                question_type="multiplication",
                options=options,
                correct_answer=str(answer)
            )
            problems.append(problem)
    
    elif problem_type == "word_problems":
        # Simple word problems
        word_templates = [
            ("Anna hat {a} Äpfel. Sie bekommt {b} weitere. Wie viele hat sie jetzt?", "addition"),
            ("Tim hat {a} Bonbons. Er gibt {b} weg. Wie viele bleiben?", "subtraction"),
            ("Es gibt {a} Gruppen mit je {b} Kindern. Wie viele Kinder sind das?", "multiplication")
        ]
        
        for i in range(count):
            template, operation = random.choice(word_templates)
            
            if operation == "addition":
                if grade == 2:
                    a, b = random.randint(3, 12), random.randint(2, 8)
                else:
                    a, b = random.randint(15, 45), random.randint(5, 25)
                answer = a + b
            elif operation == "subtraction":
                if grade == 2:
                    a = random.randint(5, 15)
                    b = random.randint(2, a)
                else:
                    a = random.randint(20, 60)
                    b = random.randint(5, a)
                answer = a - b
            else:  # multiplication
                if grade == 2:
                    a, b = random.randint(2, 4), random.randint(2, 5)
                else:
                    a, b = random.randint(3, 8), random.randint(2, 7)
                answer = a * b
            
            question = template.format(a=a, b=b)
            wrong_answers = [answer + 1, answer - 1, answer + 2]
            options = [str(answer)] + [str(w) for w in wrong_answers if w > 0][:3]
            while len(options) < 4:
                options.append(str(random.randint(1, answer + 10)))
            random.shuffle(options)
            
            problem = MathProblem(
                question=question,
                question_type="word_problems",
                options=options,
                correct_answer=str(answer)
            )
            problems.append(problem)
    
    return problems

def generate_german_word_problems(count: int, grade: int, settings: MathSettings) -> List[MathProblem]:
    """Generate German word problems using templates"""
    problems = []
    
    # Grade 2 templates
    grade2_templates = [
        {
            "template": "Anna hat {a} Äpfel. Sie gibt {b} Äpfel an ihre Freundin. Wie viele Äpfel hat Anna noch?",
            "operation": "subtract",
            "max_a": min(20, settings.max_number),
            "min_a": 5
        },
        {
            "template": "Tom sammelt {a} Sticker am Montag und {b} Sticker am Dienstag. Wie viele Sticker hat er insgesamt?",
            "operation": "add",
            "max_a": min(15, settings.max_number // 2),
            "min_a": 1
        },
        {
            "template": "Lisa hat {a} Bonbons. Sie bekommt noch {b} Bonbons geschenkt. Wie viele Bonbons hat sie jetzt?",
            "operation": "add",
            "max_a": min(15, settings.max_number // 2),
            "min_a": 1
        },
        {
            "template": "Max hat {a} Spielzeugautos. Er verliert {b} Autos im Sandkasten. Wie viele Autos hat er noch?",
            "operation": "subtract",
            "max_a": min(20, settings.max_number),
            "min_a": 5
        },
        {
            "template": "Im Garten wachsen {a} rote und {b} gelbe Blumen. Wie viele Blumen sind das zusammen?",
            "operation": "add",
            "max_a": min(15, settings.max_number // 2),
            "min_a": 1
        }
    ]
    
    # Grade 3 templates (more complex)
    grade3_templates = [
        {
            "template": "Sarah hat {a} Euro Taschengeld. Sie kauft ein Buch für {b} Euro. Wie viel Geld hat sie noch?",
            "operation": "subtract",
            "max_a": min(50, settings.max_number),
            "min_a": 10
        },
        {
            "template": "Ein Paket mit {a} Keksen wird gleichmäßig auf {b} Kinder verteilt. Wie viele Kekse bekommt jedes Kind?",
            "operation": "divide",
            "max_a": min(30, settings.max_number),
            "divisors": [2, 3, 4, 5, 6]
        },
        {
            "template": "Jede Packung enthält {a} Stifte. Wie viele Stifte sind in {b} Packungen?",
            "operation": "multiply",
            "max_a": min(12, settings.max_multiplication),
            "max_b": min(8, 100 // 12)
        },
        {
            "template": "Tim läuft jeden Tag {a} Minuten. Wie lange läuft er in {b} Tagen insgesamt?",
            "operation": "multiply",
            "max_a": min(20, settings.max_number // 5),
            "max_b": min(5, 100 // 20)
        },
        {
            "template": "Eine Klasse hat {a} Schüler. Sie werden in {b} gleich große Gruppen eingeteilt. Wie viele Schüler sind in jeder Gruppe?",
            "operation": "divide",
            "max_a": min(30, settings.max_number),
            "divisors": [2, 3, 4, 5, 6]
        }
    ]
    
    templates = grade2_templates if grade == 2 else grade3_templates
    
    for i in range(count):
        template_data = random.choice(templates)
        
        try:
            if template_data["operation"] == "add":
                max_a = template_data["max_a"]
                min_a = template_data["min_a"]
                a = random.randint(min_a, max_a)
                b = random.randint(1, min(max_a, 100 - a))  # Ensure sum ≤ 100
                answer = a + b
                
            elif template_data["operation"] == "subtract":
                max_a = template_data["max_a"] 
                min_a = template_data["min_a"]
                a = random.randint(min_a, max_a)
                b = random.randint(1, a - 1)  # Ensure positive result
                answer = a - b
                
            elif template_data["operation"] == "multiply":
                max_a = template_data["max_a"]
                max_b = template_data.get("max_b", min(10, 100 // max_a))
                a = random.randint(2, max_a)
                b = random.randint(2, max_b)
                answer = a * b
                if answer > 100:  # Skip if result too large
                    continue
                    
            elif template_data["operation"] == "divide":
                divisors = template_data["divisors"]
                b = random.choice(divisors)
                answer = random.randint(2, min(20, 100 // b))  # Quotient
                a = answer * b  # Ensure exact division
                
            # Create the problem
            question = template_data["template"].format(a=a, b=b)
            problem = MathProblem(
                question=question,
                question_type="text",
                correct_answer=str(answer)
            )
            problems.append(problem)
            
        except Exception as e:
            logging.warning(f"Error generating word problem: {e}")
            continue
    
    return problems

def generate_clock_problems(count: int, settings: MathSettings) -> List[MathProblem]:
    """Generate clock reading problems with SVG data"""
    problems = []
    clock_settings = settings.clock_settings
    
    for i in range(count):
        hours = random.randint(1, 12)
        
        if clock_settings.get("include_five_minute_intervals", False):
            minutes = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
        elif clock_settings.get("include_quarter_hours", True):
            minutes = random.choice([0, 15, 30, 45])
        elif clock_settings.get("include_half_hours", True):
            minutes = random.choice([0, 30])
        else:
            minutes = 0
        
        # Create time string
        time_str = f"{hours}:{minutes:02d}"
        if minutes == 30:
            time_str = f"{hours}:30"
        elif minutes == 0:
            time_str = f"{hours}:00"
        elif minutes == 15:
            time_str = f"{hours}:15"
        elif minutes == 45:
            time_str = f"{hours}:45"
        
        problem = MathProblem(
            question="Wie viel Uhr zeigt die Uhr an?",
            question_type="clock",
            clock_data={"hours": hours, "minutes": minutes},
            correct_answer=time_str
        )
        problems.append(problem)
    
    return problems

def generate_currency_problems(count: int, settings: MathSettings) -> List[MathProblem]:
    """Generate currency math problems"""
    problems = []
    currency_settings = settings.currency_settings
    symbol = currency_settings.get("currency_symbol", "€")
    max_amount = currency_settings.get("max_amount", 20.00)
    
    for i in range(count):
        operation = random.choice(["add", "subtract"])
        
        if operation == "add":
            amount1 = round(random.uniform(0.50, max_amount/2), 2)
            amount2 = round(random.uniform(0.50, max_amount - amount1), 2)
            result = round(amount1 + amount2, 2)
            question = f"Was kostet es insgesamt: {amount1:.2f}{symbol} + {amount2:.2f}{symbol}?"
        else:  # subtract
            amount1 = round(random.uniform(5.00, max_amount), 2)
            amount2 = round(random.uniform(0.50, amount1), 2)
            result = round(amount1 - amount2, 2)
            question = f"Wie viel Wechselgeld bekommst du: {amount1:.2f}{symbol} - {amount2:.2f}{symbol}?"
        
        problem = MathProblem(
            question=question,
            question_type="currency",
            currency_data={"amounts": [amount1, amount2], "operation": operation},
            correct_answer=f"{result:.2f}"
        )
        problems.append(problem)
    
    return problems

async def generate_ai_math_problems(problem_type: str, grade: int, count: int, settings: MathSettings) -> List[MathProblem]:
    """Generate AI math problems using static fallback content"""
    # For external deployment, use fallback content only
    return await generate_math_problems(problem_type, grade, count, settings)

async def generate_simple_math_problems(grade: int, count: int, settings: MathSettings) -> List[MathProblem]:
    """Fallback simple math problem generation"""
    problems = []
    for i in range(count):
        if i % 3 == 0:  # Addition
            a = random.randint(1, min(50, settings.max_number // 2))
            b = random.randint(1, min(50, 100 - a))  # Ensure sum doesn't exceed 100
            problems.append(MathProblem(question=f"What is {a} + {b}?", correct_answer=str(a + b)))
        elif i % 3 == 1:  # Subtraction
            a = random.randint(10, min(100, settings.max_number))
            b = random.randint(1, a)
            problems.append(MathProblem(question=f"What is {a} - {b}?", correct_answer=str(a - b)))
        else:  # Multiplication
            a = random.randint(1, min(10, settings.max_multiplication))
            b = random.randint(1, min(10, 100 // a))  # Ensure product doesn't exceed 100
            problems.append(MathProblem(question=f"What is {a} × {b}?", correct_answer=str(a * b)))
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
        total_stars_earned = sum(star["stars"] for star in stars)
        
        progress_obj = WeeklyProgress(
            week_start=week_start, 
            total_stars_earned=total_stars_earned,
            total_stars_used=0,
            available_stars=0,
            stars_in_safe=0
        )
        await db.weekly_progress.insert_one(progress_obj.dict())
        
        # Add computed property manually for response
        result = progress_obj.dict()
        result["total_stars"] = progress_obj.total_stars
        return result
    
    # Recalculate total stars from tasks
    stars = await db.daily_stars.find({"week_start": week_start}).to_list(1000)
    total_stars_earned = sum(star["stars"] for star in stars)
    
    # Create a clean dict without MongoDB ObjectId
    clean_progress = {
        "id": progress.get("id", str(uuid.uuid4())),
        "week_start": progress["week_start"],
        "total_stars_earned": total_stars_earned,
        "total_stars_used": progress.get("total_stars_used", 0),
        "available_stars": progress.get("available_stars", 0),
        "stars_in_safe": progress.get("stars_in_safe", 0)
    }
    
    # Add computed total_stars field
    clean_progress["total_stars"] = clean_progress["total_stars_earned"] - clean_progress["total_stars_used"]
    
    # Update the database with clean data
    await db.weekly_progress.replace_one({"week_start": week_start}, clean_progress)
    return clean_progress

@api_router.post("/progress/add-to-safe")
async def add_stars_to_safe(stars: int):
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    
    if not progress:
        raise HTTPException(status_code=404, detail="No progress found for current week")
    
    # Calculate available stars (earned - used)
    total_stars_earned = progress.get("total_stars_earned", 0)
    total_stars_used = progress.get("total_stars_used", 0)
    available_for_transfer = total_stars_earned - total_stars_used
    
    # Validation: Can only add stars that haven't been used yet
    if stars > available_for_transfer:
        raise HTTPException(status_code=400, detail=f"Not enough stars to add to safe. Available: {available_for_transfer}, Requested: {stars}")
    
    # Create clean progress dict
    clean_progress = {
        "id": progress.get("id", str(uuid.uuid4())),
        "week_start": progress["week_start"],
        "total_stars_earned": total_stars_earned,
        "total_stars_used": total_stars_used + stars,  # Track that these stars are now "used"
        "available_stars": progress.get("available_stars", 0),
        "stars_in_safe": progress.get("stars_in_safe", 0) + stars
    }
    
    # Add computed total_stars field for response
    clean_progress["total_stars"] = clean_progress["total_stars_earned"] - clean_progress["total_stars_used"]
    
    await db.weekly_progress.replace_one({"week_start": week_start}, clean_progress)
    return clean_progress

@api_router.post("/progress/withdraw-from-safe")
async def withdraw_stars_from_safe(stars: int):
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    
    if not progress:
        raise HTTPException(status_code=404, detail="No progress found for current week")
    
    if stars > progress["stars_in_safe"]:
        raise HTTPException(status_code=400, detail="Not enough stars in safe")
    
    progress["stars_in_safe"] -= stars
    progress["available_stars"] = progress.get("available_stars", 0) + stars
    
    await db.weekly_progress.replace_one({"week_start": week_start}, progress)
    return WeeklyProgress(**progress)

@api_router.delete("/rewards/all")
async def delete_all_rewards():
    """Delete all rewards"""
    result = await db.rewards.delete_many({})
    return {"message": f"All rewards deleted ({result.deleted_count} rewards removed)"}

@api_router.post("/progress/reset-safe")
async def reset_safe_only():
    """Reset only the stars in safe, keep everything else"""
    week_start = get_current_week_start()
    
    # Reset only safe stars
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    if progress:
        progress["stars_in_safe"] = 0
        await db.weekly_progress.replace_one({"week_start": week_start}, progress)
    
    return {"message": "Safe stars reset successfully (all other stars preserved)"}

def convert_objectid_to_str(obj):
    """Convert MongoDB ObjectId to string for JSON serialization"""
    from bson import ObjectId
    
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj

@api_router.get("/backup/export")
async def export_all_data():
    """Export all app data as JSON backup"""
    try:
        # Get current week start
        week_start = get_current_week_start()
        
        # Collect all data
        backup_data = {
            "export_date": datetime.now().isoformat(),
            "app_version": "weekly_star_tracker_v1.0",
            "data": {}
        }
        
        # Export tasks
        tasks = await db.tasks.find().to_list(length=None)
        backup_data["data"]["tasks"] = convert_objectid_to_str(tasks)
        
        # Export daily stars
        daily_stars = await db.daily_stars.find().to_list(length=None)
        backup_data["data"]["daily_stars"] = convert_objectid_to_str(daily_stars)
        
        # Export weekly progress
        progress = await db.weekly_progress.find().to_list(length=None)
        backup_data["data"]["weekly_progress"] = convert_objectid_to_str(progress)
        
        # Export rewards
        rewards = await db.rewards.find().to_list(length=None)
        backup_data["data"]["rewards"] = convert_objectid_to_str(rewards)
        
        # Export settings
        math_settings = await db.math_settings.find_one()
        german_settings = await db.german_settings.find_one()
        english_settings = await db.english_settings.find_one()
        
        backup_data["data"]["settings"] = {
            "math": convert_objectid_to_str(math_settings),
            "german": convert_objectid_to_str(german_settings),
            "english": convert_objectid_to_str(english_settings)
        }
        
        # Export statistics
        math_stats = await db.math_statistics.find().to_list(length=None)
        german_stats = await db.german_statistics.find().to_list(length=None)
        english_stats = await db.english_statistics.find().to_list(length=None)
        
        backup_data["data"]["statistics"] = {
            "math": convert_objectid_to_str(math_stats),
            "german": convert_objectid_to_str(german_stats),
            "english": convert_objectid_to_str(english_stats)
        }
        
        return backup_data
        
    except Exception as e:
        logging.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@api_router.post("/backup/import")
async def import_all_data(backup_data: dict):
    """Import data from JSON backup"""
    try:
        # Validate backup format
        if "data" not in backup_data or "app_version" not in backup_data:
            raise HTTPException(status_code=400, detail="Invalid backup format")
        
        data = backup_data["data"]
        import_results = {
            "tasks": 0,
            "progress": 0, 
            "rewards": 0,
            "settings": 0,
            "statistics": 0,
            "errors": []
        }
        
        # Import tasks
        if "tasks" in data and data["tasks"]:
            try:
                # Clear existing tasks first
                await db.tasks.delete_many({})
                # Insert imported tasks
                if data["tasks"]:
                    await db.tasks.insert_many(data["tasks"])
                    import_results["tasks"] = len(data["tasks"])
            except Exception as e:
                import_results["errors"].append(f"Tasks import failed: {str(e)}")
        
        # Import daily stars
        if "daily_stars" in data and data["daily_stars"]:
            try:
                await db.daily_stars.delete_many({})
                if data["daily_stars"]:
                    await db.daily_stars.insert_many(data["daily_stars"])
                    import_results["daily_stars"] = len(data["daily_stars"])
            except Exception as e:
                import_results["errors"].append(f"Daily stars import failed: {str(e)}")
        
        # Import weekly progress
        if "weekly_progress" in data and data["weekly_progress"]:
            try:
                await db.weekly_progress.delete_many({})
                if data["weekly_progress"]:
                    await db.weekly_progress.insert_many(data["weekly_progress"])
                    import_results["progress"] = len(data["weekly_progress"])
            except Exception as e:
                import_results["errors"].append(f"Progress import failed: {str(e)}")
        
        # Import rewards
        if "rewards" in data and data["rewards"]:
            try:
                await db.rewards.delete_many({})
                if data["rewards"]:
                    await db.rewards.insert_many(data["rewards"])
                    import_results["rewards"] = len(data["rewards"])
            except Exception as e:
                import_results["errors"].append(f"Rewards import failed: {str(e)}")
        
        # Import settings
        if "settings" in data and data["settings"]:
            try:
                settings_count = 0
                if data["settings"].get("math"):
                    await db.math_settings.delete_many({})
                    await db.math_settings.insert_one(data["settings"]["math"])
                    settings_count += 1
                if data["settings"].get("german"):
                    await db.german_settings.delete_many({})
                    await db.german_settings.insert_one(data["settings"]["german"])
                    settings_count += 1
                if data["settings"].get("english"):
                    await db.english_settings.delete_many({})
                    await db.english_settings.insert_one(data["settings"]["english"])
                    settings_count += 1
                import_results["settings"] = settings_count
            except Exception as e:
                import_results["errors"].append(f"Settings import failed: {str(e)}")
        
        # Import statistics
        if "statistics" in data and data["statistics"]:
            try:
                stats_count = 0
                if data["statistics"].get("math"):
                    await db.math_statistics.delete_many({})
                    if data["statistics"]["math"]:
                        await db.math_statistics.insert_many(data["statistics"]["math"])
                        stats_count += len(data["statistics"]["math"])
                if data["statistics"].get("german"):
                    await db.german_statistics.delete_many({})
                    if data["statistics"]["german"]:
                        await db.german_statistics.insert_many(data["statistics"]["german"])
                        stats_count += len(data["statistics"]["german"])
                if data["statistics"].get("english"):
                    await db.english_statistics.delete_many({}) 
                    if data["statistics"]["english"]:
                        await db.english_statistics.insert_many(data["statistics"]["english"])
                        stats_count += len(data["statistics"]["english"])
                import_results["statistics"] = stats_count
            except Exception as e:
                import_results["errors"].append(f"Statistics import failed: {str(e)}")
        
        return {
            "message": "Import completed",
            "results": import_results,
            "import_date": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@api_router.post("/progress/reset-all-stars")
async def reset_all_stars():
    """Reset all stars everywhere - tasks, safe, available, everything"""
    week_start = get_current_week_start()
    
    # Clear all daily stars
    await db.daily_stars.delete_many({})
    
    # Reset all progress data
    progress = WeeklyProgress(
        week_start=week_start,
        total_stars=0,
        available_stars=0,
        stars_in_safe=0
    )
    await db.weekly_progress.replace_one(
        {"week_start": week_start}, 
        progress.dict(), 
        upsert=True
    )
    
    # Reset all claimed rewards to unclaimed
    await db.rewards.update_many(
        {"is_claimed": True}, 
        {"$set": {"is_claimed": False, "claimed_at": None}}
    )
    
    return {"message": "All stars reset successfully"}

@api_router.post("/progress/reset")
async def reset_weekly_progress():
    week_start = get_current_week_start()
    
    # Clear daily stars for current week
    await db.daily_stars.delete_many({"week_start": week_start})
    
    # Reset earned and available stars BUT KEEP SAFE STARS
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    if progress:
        # Reset all earned/used/available stars, keep safe stars
        progress["total_stars_earned"] = 0
        progress["total_stars_used"] = 0
        progress["available_stars"] = 0
        progress["total_stars"] = 0  # computed field
        # stars_in_safe remains unchanged!
        await db.weekly_progress.replace_one({"week_start": week_start}, progress)
    
    return {"message": "Weekly progress reset (safe stars preserved)"}

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
    
    # Check if enough available stars
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    
    available_stars = progress.get("available_stars", 0) if progress else 0
    
    if available_stars < reward["required_stars"]:
        raise HTTPException(status_code=400, detail="Not enough available stars")
    
    # Deduct stars and mark reward as claimed
    progress["available_stars"] -= reward["required_stars"]
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
    
    # Get settings to use configured problem count
    settings_doc = await db.math_settings.find_one()
    problem_count = settings_doc.get("problem_count", 30) if settings_doc else 30
    
    problems = await generate_math_problems(grade, problem_count)
    challenge = MathChallenge(grade=grade, problems=problems)
    
    await db.math_challenges.insert_one(challenge.dict())
    return challenge

@api_router.post("/math/challenge/{challenge_id}/submit")
async def submit_math_answers(challenge_id: str, answers: Dict[int, str]):
    challenge = await db.math_challenges.find_one({"id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge_obj = MathChallenge(**challenge)
    
    correct_count = 0
    total_problems = len(challenge_obj.problems)
    
    # Grade the answers
    for i, problem in enumerate(challenge_obj.problems):
        if i in answers:
            user_answer = str(answers[i]).strip().lower()
            problem.user_answer = user_answer
            
            # Different comparison logic based on problem type
            if problem.question_type == "currency":
                # For currency, allow answers like "5.50" or "5,50" 
                correct_answer = problem.correct_answer.replace(",", ".")
                user_answer_clean = user_answer.replace(",", ".")
                problem.is_correct = correct_answer == user_answer_clean
            elif problem.question_type == "clock":
                # For clock, allow multiple valid formats
                correct_time = problem.correct_answer
                # Normalize both answers (remove spaces, convert formats)
                problem.is_correct = normalize_time_answer(user_answer) == normalize_time_answer(correct_time)
            else:
                # For text problems, direct string comparison
                problem.is_correct = problem.correct_answer.lower() == user_answer
            
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
    
    # Update math statistics
    await update_math_statistics(challenge_obj.grade, correct_count, total_problems, percentage, stars_earned)
    
    # Add earned stars to weekly progress (as available stars for rewards)
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    if not progress:
        progress = {
            "week_start": week_start, 
            "total_stars_earned": 0,
            "total_stars_used": 0,
            "available_stars": stars_earned,
            "stars_in_safe": 0
        }
    else:
        if "available_stars" not in progress:
            progress["available_stars"] = 0
        progress["available_stars"] += stars_earned
    
    await db.weekly_progress.replace_one({"week_start": week_start}, progress, upsert=True)
    await db.math_challenges.replace_one({"id": challenge_id}, challenge_obj.dict())
    
    return {
        "challenge": challenge_obj,
        "correct_answers": correct_count,
        "total_problems": total_problems,
        "percentage": percentage,
        "stars_earned": stars_earned
    }

def normalize_time_answer(time_str: str) -> str:
    """Normalize time answers for comparison"""
    time_str = time_str.replace(" ", "").replace("uhr", "").replace("Uhr", "")
    
    # Handle formats like "3:30", "15:30", "3.30", etc.
    if ":" in time_str:
        parts = time_str.split(":")
    elif "." in time_str:
        parts = time_str.split(".")
    else:
        # Just a number, assume it's hours
        return f"{int(time_str)}:00"
    
    if len(parts) == 2:
        hours = int(parts[0])
        minutes = int(parts[1])
        # Convert 24h to 12h format if needed
        if hours > 12:
            hours = hours - 12
        return f"{hours}:{minutes:02d}"
    
    return time_str

async def update_math_statistics(grade: int, correct: int, total: int, percentage: float, stars_earned: int):
    """Update math challenge statistics"""
    stats = await db.math_statistics.find_one()
    
    if not stats:
        stats = MathStatistics().dict()
    
    stats["total_attempts"] += 1
    if grade == 2:
        stats["grade_2_attempts"] += 1
    else:
        stats["grade_3_attempts"] += 1
    
    stats["total_correct"] += correct
    stats["total_wrong"] += (total - correct)
    stats["total_stars_earned"] += stars_earned
    
    # Calculate new average
    stats["average_score"] = (stats["average_score"] * (stats["total_attempts"] - 1) + percentage) / stats["total_attempts"]
    
    # Update best score
    if percentage > stats["best_score"]:
        stats["best_score"] = percentage
    
    stats["last_updated"] = datetime.utcnow()
    
    await db.math_statistics.replace_one({}, stats, upsert=True)

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

@api_router.get("/math/statistics")
async def get_math_statistics():
    stats = await db.math_statistics.find_one()
    if not stats:
        stats = MathStatistics()
        await db.math_statistics.insert_one(stats.dict())
        return stats
    return MathStatistics(**stats)

@api_router.post("/math/statistics/reset")
async def reset_math_statistics():
    """Reset math statistics"""
    stats = MathStatistics()
    await db.math_statistics.replace_one({}, stats.dict(), upsert=True)
    return {"message": "Math statistics reset successfully"}

# German Challenge Endpoints
@api_router.post("/german/challenge/{grade}")
async def create_german_challenge(grade: int):
    if grade not in [2, 3]:
        raise HTTPException(status_code=400, detail="Grade must be 2 or 3")
    
    # Get settings to use configured problem count
    settings_doc = await db.german_settings.find_one()
    problem_count = settings_doc.get("problem_count", 20) if settings_doc else 20
    
    problems = await generate_german_problems(grade, problem_count)
    challenge = GermanChallenge(grade=grade, problems=problems)
    
    await db.german_challenges.insert_one(challenge.dict())
    return challenge

@api_router.post("/german/challenge/{challenge_id}/submit")
async def submit_german_answers(challenge_id: str, answers: Dict[int, str]):
    challenge = await db.german_challenges.find_one({"id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge_obj = GermanChallenge(**challenge)
    
    correct_count = 0
    total_problems = len(challenge_obj.problems)
    
    # Grade the answers
    for i, problem in enumerate(challenge_obj.problems):
        if i in answers:
            user_answer = str(answers[i]).strip()
            problem.user_answer = user_answer
            
            # Direct string comparison for German problems
            problem.is_correct = problem.correct_answer.lower().strip() == user_answer.lower().strip()
            
            if problem.is_correct:
                correct_count += 1
    
    # Calculate percentage and stars earned
    percentage = (correct_count / total_problems) * 100
    challenge_obj.score = percentage
    challenge_obj.completed = True
    
    # Get star tiers from settings
    settings = await db.german_settings.find_one()
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
    
    # Update German statistics
    await update_german_statistics(challenge_obj.grade, correct_count, total_problems, percentage, stars_earned, challenge_obj.problems)
    
    # Add earned stars to weekly progress (as available stars for rewards)
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    if not progress:
        progress = {
            "week_start": week_start, 
            "total_stars_earned": 0,
            "total_stars_used": 0,
            "available_stars": stars_earned,
            "stars_in_safe": 0
        }
    else:
        if "available_stars" not in progress:
            progress["available_stars"] = 0
        progress["available_stars"] += stars_earned
    
    await db.weekly_progress.replace_one({"week_start": week_start}, progress, upsert=True)
    await db.german_challenges.replace_one({"id": challenge_id}, challenge_obj.dict())
    
    return {
        "challenge": challenge_obj,
        "correct_answers": correct_count,
        "total_problems": total_problems,
        "percentage": percentage,
        "stars_earned": stars_earned
    }

async def update_german_statistics(grade: int, correct: int, total: int, percentage: float, stars_earned: int, problems: List[GermanProblem]):
    """Update German challenge statistics"""
    stats = await db.german_statistics.find_one()
    
    if not stats:
        stats = GermanStatistics().dict()
    
    stats["total_attempts"] += 1
    if grade == 2:
        stats["grade_2_attempts"] += 1
    else:
        stats["grade_3_attempts"] += 1
    
    stats["total_correct"] += correct
    stats["total_wrong"] += (total - correct)
    stats["total_stars_earned"] += stars_earned
    
    # Calculate new average
    stats["average_score"] = (stats["average_score"] * (stats["total_attempts"] - 1) + percentage) / stats["total_attempts"]
    
    # Update best score
    if percentage > stats["best_score"]:
        stats["best_score"] = percentage
    
    # Update problem type stats
    if "problem_type_stats" not in stats:
        stats["problem_type_stats"] = {}
    
    for problem in problems:
        problem_type = problem.question_type
        if problem_type not in stats["problem_type_stats"]:
            stats["problem_type_stats"][problem_type] = {
                "total_attempts": 0,
                "correct": 0,
                "wrong": 0
            }
        
        stats["problem_type_stats"][problem_type]["total_attempts"] += 1
        if problem.is_correct:
            stats["problem_type_stats"][problem_type]["correct"] += 1
        else:
            stats["problem_type_stats"][problem_type]["wrong"] += 1
    
    stats["last_updated"] = datetime.utcnow()
    
    await db.german_statistics.replace_one({}, stats, upsert=True)

@api_router.get("/german/settings")
async def get_german_settings():
    settings = await db.german_settings.find_one()
    if not settings:
        settings = GermanSettings()
        await db.german_settings.insert_one(settings.dict())
        return settings
    return GermanSettings(**settings)

@api_router.put("/german/settings")
async def update_german_settings(settings: GermanSettings):
    await db.german_settings.replace_one({}, settings.dict(), upsert=True)
    return settings

@api_router.get("/german/statistics")
async def get_german_statistics():
    stats = await db.german_statistics.find_one()
    if not stats:
        stats = GermanStatistics()
        await db.german_statistics.insert_one(stats.dict())
        return stats
    return GermanStatistics(**stats)

@api_router.post("/german/statistics/reset")
async def reset_german_statistics():
    """Reset German statistics"""
    stats = GermanStatistics()
    await db.german_statistics.replace_one({}, stats.dict(), upsert=True)
    return {"message": "German statistics reset successfully"}

# English Challenge Endpoints
@api_router.post("/english/challenge/{grade}")
async def create_english_challenge(grade: int):
    if grade not in [2, 3]:
        raise HTTPException(status_code=400, detail="Grade must be 2 or 3")
    
    # Get settings to use configured problem count
    settings_doc = await db.english_settings.find_one()
    problem_count = settings_doc.get("problem_count", 15) if settings_doc else 15
    
    problems = await generate_english_problems(grade, problem_count)
    challenge = EnglishChallenge(grade=grade, problems=problems)
    
    await db.english_challenges.insert_one(challenge.dict())
    return challenge

@api_router.post("/english/challenge/{challenge_id}/submit")
async def submit_english_answers(challenge_id: str, answers: Dict[int, str]):
    challenge = await db.english_challenges.find_one({"id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge_obj = EnglishChallenge(**challenge)
    
    correct_count = 0
    total_problems = len(challenge_obj.problems)
    
    # Grade the answers
    for i, problem in enumerate(challenge_obj.problems):
        if i in answers:
            user_answer = str(answers[i]).strip()
            problem.user_answer = user_answer
            
            # Direct string comparison for English problems
            problem.is_correct = problem.correct_answer.lower().strip() == user_answer.lower().strip()
            
            if problem.is_correct:
                correct_count += 1
    
    # Calculate percentage and stars earned
    percentage = (correct_count / total_problems) * 100
    challenge_obj.score = percentage
    challenge_obj.completed = True
    
    # Get star tiers from settings
    settings = await db.english_settings.find_one()
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
    
    # Update English statistics
    await update_english_statistics(challenge_obj.grade, correct_count, total_problems, percentage, stars_earned, challenge_obj.problems)
    
    # Add earned stars to weekly progress (as available stars for rewards)
    week_start = get_current_week_start()
    progress = await db.weekly_progress.find_one({"week_start": week_start})
    if not progress:
        progress = {
            "week_start": week_start, 
            "total_stars_earned": 0,
            "total_stars_used": 0,
            "available_stars": stars_earned,
            "stars_in_safe": 0
        }
    else:
        if "available_stars" not in progress:
            progress["available_stars"] = 0
        progress["available_stars"] += stars_earned
    
    await db.weekly_progress.replace_one({"week_start": week_start}, progress, upsert=True)
    await db.english_challenges.replace_one({"id": challenge_id}, challenge_obj.dict())
    
    return {
        "challenge": challenge_obj,
        "correct_answers": correct_count,
        "total_problems": total_problems,
        "percentage": percentage,
        "stars_earned": stars_earned
    }

async def update_english_statistics(grade: int, correct: int, total: int, percentage: float, stars_earned: int, problems: List[EnglishProblem]):
    """Update English challenge statistics"""
    stats = await db.english_statistics.find_one()
    
    if not stats:
        stats = EnglishStatistics().dict()
    
    stats["total_attempts"] += 1
    if grade == 2:
        stats["grade_2_attempts"] += 1
    else:
        stats["grade_3_attempts"] += 1
    
    stats["total_correct"] += correct
    stats["total_wrong"] += (total - correct)
    stats["total_stars_earned"] += stars_earned
    
    # Calculate new average
    stats["average_score"] = (stats["average_score"] * (stats["total_attempts"] - 1) + percentage) / stats["total_attempts"]
    
    # Update best score
    if percentage > stats["best_score"]:
        stats["best_score"] = percentage
    
    # Update problem type stats
    if "problem_type_stats" not in stats:
        stats["problem_type_stats"] = {}
    
    for problem in problems:
        problem_type = problem.question_type
        if problem_type not in stats["problem_type_stats"]:
            stats["problem_type_stats"][problem_type] = {
                "total_attempts": 0,
                "correct": 0,
                "wrong": 0
            }
        
        stats["problem_type_stats"][problem_type]["total_attempts"] += 1
        if problem.is_correct:
            stats["problem_type_stats"][problem_type]["correct"] += 1
        else:
            stats["problem_type_stats"][problem_type]["wrong"] += 1
    
    stats["last_updated"] = datetime.utcnow()
    
    await db.english_statistics.replace_one({}, stats, upsert=True)

@api_router.get("/english/settings")
async def get_english_settings():
    settings = await db.english_settings.find_one()
    if not settings:
        settings = EnglishSettings()
        await db.english_settings.insert_one(settings.dict())
        return settings
    return EnglishSettings(**settings)

@api_router.put("/english/settings")
async def update_english_settings(settings: EnglishSettings):
    await db.english_settings.replace_one({}, settings.dict(), upsert=True)
    return settings

@api_router.get("/english/statistics")
async def get_english_statistics():
    stats = await db.english_statistics.find_one()
    if not stats:
        stats = EnglishStatistics()
        await db.english_statistics.insert_one(stats.dict())
        return stats
    return EnglishStatistics(**stats)

@api_router.post("/english/statistics/reset")
async def reset_english_statistics():
    """Reset English statistics"""
    stats = EnglishStatistics()
    await db.english_statistics.replace_one({}, stats.dict(), upsert=True)
    return {"message": "English statistics reset successfully"}

@api_router.get("/cache/preload")
async def preload_challenges():
    """Preload challenges for offline usage"""
    try:
        cached_challenges = {
            "math": {},
            "german": {},
            "english": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache Math challenges for both grades
        for grade in [2, 3]:
            cached_challenges["math"][f"grade_{grade}"] = {
                "addition": await generate_math_problems("addition", grade, 10, MathSettings()),
                "subtraction": await generate_math_problems("subtraction", grade, 10, MathSettings()),
                "multiplication": await generate_math_problems("multiplication", grade, 10, MathSettings()),
                "word_problems": await generate_math_problems("word_problems", grade, 5, MathSettings())
            }
        
        # Cache German challenges  
        for grade in [2, 3]:
            cached_challenges["german"][f"grade_{grade}"] = {
                "spelling": await generate_spelling_problems(10, grade, GermanSettings()),
                "word_types": await generate_word_type_problems(8, grade, GermanSettings()),
                "fill_blank": await generate_fill_blank_problems(8, grade, GermanSettings())
            }
        
        # Cache English challenges
        for grade in [2, 3]:
            cached_challenges["english"][f"grade_{grade}"] = {
                "vocabulary_de_en": await generate_vocabulary_de_en_problems(10, grade, EnglishSettings()),
                "vocabulary_en_de": await generate_vocabulary_en_de_problems(10, grade, EnglishSettings()),
                "simple_sentences": await generate_simple_sentence_problems(8, grade, EnglishSettings())
            }
        
        # Convert MathProblem, GermanProblem, EnglishProblem objects to dicts for JSON serialization
        def serialize_problems(obj):
            if hasattr(obj, 'dict'):
                return obj.dict()
            elif isinstance(obj, list):
                return [serialize_problems(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize_problems(v) for k, v in obj.items()}
            else:
                return obj
        
        cached_challenges = serialize_problems(cached_challenges)
        
        return {
            "success": True,
            "cached_challenges": cached_challenges,
            "total_problems": sum([
                len(problems) for grade_data in cached_challenges["math"].values() 
                for problems in grade_data.values() if isinstance(problems, list)
            ]) + sum([
                len(problems) for grade_data in cached_challenges["german"].values()
                for problems in grade_data.values() if isinstance(problems, list)
            ]) + sum([
                len(problems) for grade_data in cached_challenges["english"].values()
                for problems in grade_data.values() if isinstance(problems, list)
            ]),
            "message": "Challenges preloaded successfully for offline usage"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to preload challenges"
        }

# Basic status endpoints
@api_router.get("/")
async def root():
    return {"message": "Weekly Star Tracker API Ready!"}

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Weekly Star Tracker Backend is running!", "status": "healthy", "api": "/api/"}

# Include the router
app.include_router(api_router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()