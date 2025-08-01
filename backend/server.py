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
    except ImportError:
        # Fallback to original smaller list if imports fail
        grade2_words = [
            {"correct": "Hund", "wrong": ["Hunt", "Hundt", "Huhnd"]},
            {"correct": "Katze", "wrong": ["Kaze", "Katse", "Kazte"]},
        {"correct": "Spinne", "wrong": ["Sbinne", "Spinnee", "Zbinne"]},
        {"correct": "Ameise", "wrong": ["Ahmeise", "Ameihse", "Amaise"]},
        {"correct": "Wurm", "wrong": ["Wuhrm", "Wurmm", "Vurm"]},
        {"correct": "Marienkäfer", "wrong": ["Mariehnkäfer", "Mariengäfer", "Maarienkäfer"]},
        {"correct": "Schmetterling", "wrong": ["Schmetehrling", "Schmetterlink", "Schmetterlingg"]},
        {"correct": "Libelle", "wrong": ["Libbelle", "Libehle", "Lipelle"]},
        {"correct": "Wespe", "wrong": ["Wesbpe", "Wehspe", "Wezspe"]},
        {"correct": "Hummel", "wrong": ["Hummell", "Gummel", "Hummmel"]},
        {"correct": "Grille", "wrong": ["Krille", "Grile", "Grielle"]},
        {"correct": "Heuschrecke", "wrong": ["Heuschregke", "Heuschreckke", "Geuschrecke"]},
        {"correct": "Elefant", "wrong": ["Elefandt", "Elehfant", "Elephannt"]},
        {"correct": "Löwe", "wrong": ["Löhwe", "Löwee", "Loewe"]},
        {"correct": "Tiger", "wrong": ["Diger", "Tigher", "Tieger"]},
        {"correct": "Bär", "wrong": ["Bähr", "Bärr", "Paer"]},
        {"correct": "Affe", "wrong": ["Ahffe", "Affee", "Apfe"]},
        {"correct": "Giraffe", "wrong": ["Kirafe", "Giraffe", "Girrafe"]},
        {"correct": "Zebra", "wrong": ["Sebra", "Zebraa", "Cebra"]},
        {"correct": "Nilpferd", "wrong": ["Nilbferd", "Nillpferd", "Nihlpferd"]},
        {"correct": "Krokodil", "wrong": ["Grocodil", "Krokodill", "Kroggodil"]},
        {"correct": "Schlange", "wrong": ["Schlangge", "Schlahge", "Schlanke"]},
        {"correct": "Schildkröte", "wrong": ["Schildkröhte", "Schildgröte", "Schiltkröte"]},
        {"correct": "Pinguin", "wrong": ["Binguin", "Pinguhin", "Pinkuin"]},
        {"correct": "Eisbär", "wrong": ["Eispär", "Eisbähr", "Aizbär"]},
        {"correct": "Seehund", "wrong": ["Sehund", "Seegundt", "Zeehund"]},
        {"correct": "Delfin", "wrong": ["Delphin", "Dellfin", "Telfin"]},
        {"correct": "Wal", "wrong": ["Wahl", "Wall", "Val"]},
        {"correct": "Hai", "wrong": ["Haai", "Haj", "Gay"]},
        {"correct": "Seestern", "wrong": ["Sehstern", "Seesterrn", "Zeestern"]},
        {"correct": "Krabbe", "wrong": ["Grabbee", "Krabbee", "Grappe"]},
        {"correct": "Muschel", "wrong": ["Muschell", "Muschel", "Muschel"]},

        # Food Items Extended (100 words)
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
    """Generate word type identification problems"""
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
    
    # Massively expanded fallback templates
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
        {"sentence": "Die Kinder laufen schnell zum Spielplatz.", "word": "laufen", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der schwierige Test ist endlich vorbei.", "word": "schwierige", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Unsere Nachbarin hat einen kleinen Hund.", "word": "Nachbarin", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Wetter wird morgen hoffentlich besser.", "word": "wird", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die alte Kirche steht mitten im Dorf.", "word": "alte", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Wissenschaftler forscht an neuen Medikamenten.", "word": "Wissenschaftler", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Schüler diskutieren über das interessante Thema.", "word": "diskutieren", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das komplizierte Problem wurde endlich gelöst.", "word": "komplizierte", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Bibliothekarin hilft beim Suchen der Bücher.", "word": "Bibliothekarin", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Meine Schwester studiert Medizin an der Universität.", "word": "studiert", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der wichtige Brief kam heute an.", "word": "wichtige", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Bürgermeister eröffnet das neue Schwimmbad.", "word": "Bürgermeister", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Touristen fotografieren die berühmte Sehenswürdigkeit.", "word": "fotografieren", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das moderne Museum zeigt zeitgenössische Kunst.", "word": "moderne", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Feuerwehrmann rettet die Katze vom Baum.", "word": "Feuerwehrmann", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Astronauten erforschen das Weltall.", "word": "erforschen", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das geheimnisvolle Schloss fasziniert die Besucher.", "word": "geheimnisvolle", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Geologin untersucht die Gesteinsproben.", "word": "Geologin", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Pianist komponiert eine neue Symphonie.", "word": "komponiert", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das elegante Kleid gefällt mir sehr gut.", "word": "elegante", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Mechaniker repariert das defekte Auto.", "word": "Mechaniker", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Architektin entwirft ein neues Gebäude.", "word": "entwirft", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das kreative Projekt begeistert alle Teilnehmer.", "word": "kreative", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Umweltschützer kämpft für saubere Luft.", "word": "Umweltschützer", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Journalistin berichtet über aktuelle Ereignisse.", "word": "berichtet", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das spannende Buch hält mich gefesselt.", "word": "spannende", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Tierarzt behandelt verletzte Tiere liebevoll.", "word": "Tierarzt", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Gärtnerin pflanzt bunte Blumen.", "word": "pflanzt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das frische Gemüse kommt vom Markt.", "word": "frische", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Künstler malt ein wunderschönes Bild.", "word": "Künstler", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Forscherin entdeckt eine neue Pflanzenart.", "word": "entdeckt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das seltene Tier lebt nur in diesem Gebiet.", "word": "seltene", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Polizist regelt den Verkehr sicher.", "word": "Polizist", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Köchin bereitet das Essen sorgfältig vor.", "word": "bereitet vor", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das köstliche Menü schmeckt allen Gästen.", "word": "köstliche", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Pilot fliegt sicher durch die Wolken.", "word": "Pilot", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Sekretärin organisiert wichtige Termine.", "word": "organisiert", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das effiziente System arbeitet fehlerfrei.", "word": "effiziente", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Handwerker renoviert das alte Haus.", "word": "Handwerker", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Musiklehrerin unterrichtet talentierte Schüler.", "word": "unterrichtet", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das melodische Lied berührt die Herzen.", "word": "melodische", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Verkäufer berät die Kunden freundlich.", "word": "Verkäufer", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Designerin gestaltet moderne Möbel.", "word": "gestaltet", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das innovative Konzept überzeugt die Investoren.", "word": "innovative", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Psychologe hilft Menschen bei Problemen.", "word": "Psychologe", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Übersetzerin übersetzt schwierige Texte.", "word": "übersetzt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das ausländische Dokument braucht eine Übersetzung.", "word": "ausländische", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Anwalt verteidigt seinen Mandanten.", "word": "Anwalt", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Richterin urteilt gerecht und fair.", "word": "urteilt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das faire Urteil überzeugt alle Beteiligten.", "word": "faire", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]}
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
    """Generate fill-in-the-blank problems with massive variety"""
    problems = []
    
    # Try AI generation first
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            ai_problems = await generate_ai_fill_blank_problems(count, grade, settings)
            if ai_problems:
                return ai_problems
    except Exception as e:
        logging.error(f"AI fill blank generation failed: {e}")
    
    # Massively expanded fallback templates
    grade2_blanks = [
        {"text": "Der ___ bellt laut.", "answer": "Hund", "options": ["Hund", "Katze", "Vogel"]},
        {"text": "Mama ___ in der Küche.", "answer": "kocht", "options": ["kocht", "singt", "tanzt"]},
        {"text": "Das Auto ist ___.", "answer": "rot", "options": ["rot", "groß", "neu"]},
        {"text": "Wir gehen in die ___.", "answer": "Schule", "options": ["Schule", "Kirche", "Bank"]},
        {"text": "Der Ball ist ___.", "answer": "rund", "options": ["rund", "eckig", "spitz"]},
        {"text": "Papa ___ die Zeitung.", "answer": "liest", "options": ["liest", "kauft", "wirft"]},
        {"text": "Die Sonne ___ hell.", "answer": "scheint", "options": ["scheint", "regnet", "schneit"]},
        {"text": "Im Garten wachsen ___.", "answer": "Blumen", "options": ["Blumen", "Steine", "Autos"]},
        {"text": "Die ___ ist warm.", "answer": "Suppe", "options": ["Suppe", "Tasse", "Wand"]},
        {"text": "Der Fisch ___ im Wasser.", "answer": "schwimmt", "options": ["schwimmt", "fliegt", "läuft"]},
        {"text": "Das Haus hat eine ___ Tür.", "answer": "braune", "options": ["braune", "runde", "laute"]},
        {"text": "Oma ___ uns eine Geschichte.", "answer": "erzählt", "options": ["erzählt", "kauft", "versteckt"]},
        {"text": "Der ___ fliegt hoch am Himmel.", "answer": "Vogel", "options": ["Vogel", "Stein", "Tisch"]},
        {"text": "Wir ___ gerne Eis.", "answer": "essen", "options": ["essen", "bauen", "malen"]},
        {"text": "Das Buch ist sehr ___.", "answer": "interessant", "options": ["interessant", "laut", "kalt"]},
        {"text": "Die Katze ___ auf dem Sofa.", "answer": "schläft", "options": ["schläft", "schwimmt", "fliegt"]},
        {"text": "Der ___ ist sehr süß.", "answer": "Apfel", "options": ["Apfel", "Stein", "Stuhl"]},
        {"text": "Wir ___ mit dem Bus zur Schule.", "answer": "fahren", "options": ["fahren", "schwimmen", "fliegen"]},
        {"text": "Das Wetter ist heute ___.", "answer": "schön", "options": ["schön", "quadratisch", "laut"]},
        {"text": "Der ___ macht miau.", "answer": "Kater", "options": ["Kater", "Hund", "Vogel"]},
        {"text": "Mama ___ schöne Lieder.", "answer": "singt", "options": ["singt", "isst", "baut"]},
        {"text": "Das ___ ist sehr kalt.", "answer": "Eis", "options": ["Eis", "Feuer", "Brot"]},
        {"text": "Wir ___ im Park spazieren.", "answer": "gehen", "options": ["gehen", "schwimmen", "fliegen"]},
        {"text": "Die ___ sind sehr bunt.", "answer": "Blumen", "options": ["Blumen", "Steine", "Dächer"]},
        {"text": "Papa ___ das Auto in die Garage.", "answer": "fährt", "options": ["fährt", "trägt", "wirft"]},
        {"text": "Der ___ schmeckt sehr gut.", "answer": "Kuchen", "options": ["Kuchen", "Sand", "Stein"]},
        {"text": "Die Kinder ___ fröhlich.", "answer": "lachen", "options": ["lachen", "schlafen", "weinen"]},
        {"text": "Das ___ läutet zur Pause.", "answer": "Klingel", "options": ["Klingel", "Auto", "Buch"]},
        {"text": "Opa ___ uns mit dem Auto ab.", "answer": "holt", "options": ["holt", "versteckt", "vergisst"]},
        {"text": "Die ___ leuchtet in der Nacht.", "answer": "Lampe", "options": ["Lampe", "Blume", "Suppe"]},
        {"text": "Wir ___ unsere Zähne.", "answer": "putzen", "options": ["putzen", "essen", "verstecken"]},
        {"text": "Der ___ klingelt laut.", "answer": "Wecker", "options": ["Wecker", "Ball", "Apfel"]},
        {"text": "Die Maus ist sehr ___.", "answer": "klein", "options": ["klein", "laut", "eckig"]},
        {"text": "Wir ___ Musik im Radio.", "answer": "hören", "options": ["hören", "sehen", "riechen"]},
        {"text": "Das ___ fährt auf der Straße.", "answer": "Fahrrad", "options": ["Fahrrad", "Vogel", "Fisch"]},
        {"text": "Die Blumen ___ sehr schön.", "answer": "duften", "options": ["duften", "bellen", "klingeln"]},
        {"text": "Der ___ trägt einen warmen Pullover.", "answer": "Junge", "options": ["Junge", "Baum", "Tisch"]},
        {"text": "Wir ___ ein Puzzle zusammen.", "answer": "bauen", "options": ["bauen", "trinken", "hören"]},
        {"text": "Die ___ schmeckt sehr lecker.", "answer": "Pizza", "options": ["Pizza", "Seife", "Kreide"]},
        {"text": "Papa ___ die Pflanzen im Garten.", "answer": "gießt", "options": ["gießt", "isst", "trägt"]},
        {"text": "Das ___ hopst über die Wiese.", "answer": "Kaninchen", "options": ["Kaninchen", "Auto", "Haus"]},
        {"text": "Die Kinder ___ auf dem Spielplatz.", "answer": "spielen", "options": ["spielen", "kochen", "schlafen"]},
        {"text": "Der ___ schwimmt im Teich.", "answer": "Fisch", "options": ["Fisch", "Hund", "Vogel"]},
        {"text": "Mama ___ das Abendessen vor.", "answer": "bereitet", "options": ["bereitet", "versteckt", "wirft"]},
        {"text": "Das ___ macht wau-wau.", "answer": "Hündchen", "options": ["Hündchen", "Auto", "Buch"]},
        {"text": "Wir ___ einen Schneemann.", "answer": "bauen", "options": ["bauen", "essen", "trinken"]},
        {"text": "Die ___ sind sehr weich.", "answer": "Kissen", "options": ["Kissen", "Steine", "Nägel"]},
        {"text": "Opa ___ in seinem Sessel.", "answer": "sitzt", "options": ["sitzt", "fliegt", "schwimmt"]},
        {"text": "Das ___ riecht sehr gut.", "answer": "Parfüm", "options": ["Parfüm", "Müll", "Rauch"]},
        {"text": "Die Kinder ___ um die Wette.", "answer": "rennen", "options": ["rennen", "schlafen", "sitzen"]},
        {"text": "Der ___ bringt uns die Post.", "answer": "Postbote", "options": ["Postbote", "Hund", "Ball"]},
        {"text": "Das ___ schwimmt auf dem See.", "answer": "Boot", "options": ["Boot", "Auto", "Haus"]},
        {"text": "Die ___ fliegt von Blume zu Blume.", "answer": "Biene", "options": ["Biene", "Katze", "Fisch"]},
        {"text": "Wir ___ Geschenke zu Weihnachten.", "answer": "bekommen", "options": ["bekommen", "verstecken", "werfen"]},
        {"text": "Der ___ wächst sehr hoch.", "answer": "Baum", "options": ["Baum", "Tisch", "Ball"]},
        {"text": "Die Sonne ___ am Morgen auf.", "answer": "geht", "options": ["geht", "schläft", "rennt"]},
        {"text": "Das ___ hat vier Räder.", "answer": "Auto", "options": ["Auto", "Vogel", "Fisch"]},
        {"text": "Wir ___ jeden Tag zur Schule.", "answer": "gehen", "options": ["gehen", "fliegen", "schwimmen"]},
        {"text": "Die ___ gibt uns Milch.", "answer": "Kuh", "options": ["Kuh", "Katze", "Maus"]},
        {"text": "Papa ___ die Wand bunt an.", "answer": "malt", "options": ["malt", "isst", "hört"]},
        {"text": "Das ___ hüpft im Garten herum.", "answer": "Kaninchen", "options": ["Kaninchen", "Auto", "Tisch"]},
        {"text": "Wir ___ im Sommer ins Schwimmbad.", "answer": "gehen", "options": ["gehen", "fliegen", "graben"]},
        {"text": "Die ___ bringt im Frühling ihre Jungen zur Welt.", "answer": "Katze", "options": ["Katze", "Lampe", "Tasse"]},
        {"text": "Der ___ hilft kranken Menschen.", "answer": "Arzt", "options": ["Arzt", "Ball", "Baum"]},
        {"text": "Das ___ fliegt hoch in den Wolken.", "answer": "Flugzeug", "options": ["Flugzeug", "Fisch", "Auto"]},
        {"text": "Wir ___ im Winter warme Kleidung.", "answer": "tragen", "options": ["tragen", "essen", "hören"]},
        {"text": "Die ___ gibt Licht in der Dunkelheit.", "answer": "Kerze", "options": ["Kerze", "Tasse", "Blume"]},
        {"text": "Papa ___ uns eine Gute-Nacht-Geschichte.", "answer": "liest", "options": ["liest", "kocht", "baut"]},
        {"text": "Das ___ macht tick-tack.", "answer": "Uhr", "options": ["Uhr", "Auto", "Buch"]},
        {"text": "Wir ___ bunte Bilder.", "answer": "malen", "options": ["malen", "essen", "hören"]},
        {"text": "Die ___ wärmt uns im Winter.", "answer": "Heizung", "options": ["Heizung", "Blume", "Tasse"]},
        {"text": "Der ___ baut sein Nest auf dem Baum.", "answer": "Vogel", "options": ["Vogel", "Hund", "Fisch"]},
        {"text": "Das ___ schmeckt süß und lecker.", "answer": "Bonbon", "options": ["Bonbon", "Salz", "Seife"]},
        {"text": "Wir ___ fröhliche Lieder.", "answer": "singen", "options": ["singen", "essen", "bauen"]},
        {"text": "Die ___ leuchten am Himmel.", "answer": "Sterne", "options": ["Sterne", "Steine", "Tische"]},
        {"text": "Papa ___ den Rasen im Garten.", "answer": "mäht", "options": ["mäht", "isst", "trägt"]},
        {"text": "Das ___ hat weiche Ohren.", "answer": "Kaninchen", "options": ["Kaninchen", "Auto", "Buch"]},
        {"text": "Wir ___ vorsichtig über die Straße.", "answer": "gehen", "options": ["gehen", "fliegen", "schwimmen"]},
        {"text": "Die ___ blühen im Frühling.", "answer": "Blumen", "options": ["Blumen", "Steine", "Autos"]},
        {"text": "Der ___ hilft beim Transport schwerer Sachen.", "answer": "Lastwagen", "options": ["Lastwagen", "Vogel", "Fisch"]},
        {"text": "Das ___ summt von Blüte zu Blüte.", "answer": "Bienchen", "options": ["Bienchen", "Auto", "Tisch"]},
        {"text": "Wir ___ gemeinsam zu Abend.", "answer": "essen", "options": ["essen", "fliegen", "bauen"]},
        {"text": "Die ___ kühlt uns an heißen Tagen.", "answer": "Klimaanlage", "options": ["Klimaanlage", "Heizung", "Kerze"]},
        {"text": "Papa ___ das Fahrrad in die Garage.", "answer": "stellt", "options": ["stellt", "isst", "singt"]}
    ]
    
    grade3_blanks = [
        {"text": "Die Schüler ___ ihre Hausaufgaben sehr sorgfältig.", "answer": "machen", "options": ["machen", "vergessen", "kaufen"]},
        {"text": "Nach dem Regen bildete sich ein ___ am Himmel.", "answer": "Regenbogen", "options": ["Regenbogen", "Flugzeug", "Stern"]},
        {"text": "Der ___ Lehrer erklärt die Aufgabe noch einmal.", "answer": "geduldige", "options": ["geduldige", "müde", "schnelle"]},
        {"text": "Meine Schwester ___ jeden Tag Klavier.", "answer": "übt", "options": ["übt", "verkauft", "repariert"]},
        {"text": "Im Winter ___ es oft und die Straßen werden glatt.", "answer": "schneit", "options": ["schneit", "blüht", "schwimmt"]},
        {"text": "Die ___ Geschichte hat mir sehr gut gefallen.", "answer": "spannende", "options": ["spannende", "langweilige", "kurze"]},
        {"text": "Opa ___ uns oft von früher.", "answer": "erzählt", "options": ["erzählt", "fragt", "vergisst"]},
        {"text": "Das ___ Buch liegt auf dem Tisch.", "answer": "dicke", "options": ["dicke", "kleine", "alte"]},
        {"text": "Die Wissenschaftler ___ eine neue Entdeckung.", "answer": "machten", "options": ["machten", "versteckten", "vergaßen"]},
        {"text": "Das ___ Museum öffnet um zehn Uhr.", "answer": "berühmte", "options": ["berühmte", "geschlossene", "leise"]},
        {"text": "Der Astronaut ___ ins Weltall.", "answer": "fliegt", "options": ["fliegt", "schwimmt", "gräbt"]},
        {"text": "Die ___ Musik gefällt mir sehr.", "answer": "klassische", "options": ["klassische", "laute", "stumme"]},
        {"text": "Mein Bruder ___ Informatik an der Universität.", "answer": "studiert", "options": ["studiert", "verkauft", "versteckt"]},
        {"text": "Das ___ Experiment war sehr erfolgreich.", "answer": "komplizierte", "options": ["komplizierte", "einfache", "langweilige"]},
        {"text": "Die Ärztin ___ den verletzten Patienten.", "answer": "behandelt", "options": ["behandelt", "ignoriert", "versteckt"]},
        {"text": "Das ___ Gebäude wurde letztes Jahr renoviert.", "answer": "historische", "options": ["historische", "neue", "kleine"]},
        {"text": "Der Detektiv ___ den Täter nach langer Suche.", "answer": "fand", "options": ["fand", "verlor", "versteckte"]},
        {"text": "Die ___ Aufführung begeisterte das Publikum.", "answer": "großartige", "options": ["großartige", "schlechte", "stumme"]},
        {"text": "Meine Tante ___ als Lehrerin in einer Grundschule.", "answer": "arbeitet", "options": ["arbeitet", "schläft", "spielt"]},
        {"text": "Das ___ Rätsel konnte niemand lösen.", "answer": "schwierige", "options": ["schwierige", "einfache", "bekannte"]},
        {"text": "Der Forscher ___ eine wichtige Entdeckung.", "answer": "publizierte", "options": ["publizierte", "versteckte", "vergaß"]},
        {"text": "Die ___ Statue steht mitten auf dem Platz.", "answer": "beeindruckende", "options": ["beeindruckende", "kleine", "versteckte"]},
        {"text": "Unser Nachbar ___ jeden Morgen joggen.", "answer": "geht", "options": ["geht", "schläft", "kocht"]},
        {"text": "Das ___ Konzert findet heute Abend statt.", "answer": "lang ersehnte", "options": ["lang ersehnte", "vergessene", "stumme"]},
        {"text": "Die Journalistin ___ über das wichtige Ereignis.", "answer": "berichtete", "options": ["berichtete", "schwieg", "lachte"]},
        {"text": "Das ___ Kunstwerk hängt in der Galerie.", "answer": "wertvolle", "options": ["wertvolle", "hässliche", "zerbrochene"]},
        {"text": "Der Pilot ___ das Flugzeug sicher.", "answer": "landete", "options": ["landete", "verlor", "versteckte"]},
        {"text": "Die ___ Reise führte uns durch drei Länder.", "answer": "abenteuerliche", "options": ["abenteuerliche", "kurze", "langweilige"]},
        {"text": "Meine Cousine ___ Medizin studieren.", "answer": "möchte", "options": ["möchte", "hasst", "vergisst"]},
        {"text": "Das ___ Restaurant serviert internationale Küche.", "answer": "elegante", "options": ["elegante", "geschlossene", "schmutzige"]},
        {"text": "Der Architekt ___ ein modernes Bürogebäude.", "answer": "entwarf", "options": ["entwarf", "zerstörte", "versteckte"]},
        {"text": "Die ___ Bibliothek hat über eine Million Bücher.", "answer": "riesige", "options": ["riesige", "kleine", "leere"]},
        {"text": "Unser Lehrer ___ uns komplizierte Mathematik.", "answer": "erklärt", "options": ["erklärt", "versteckt", "vergisst"]},
        {"text": "Das ___ Orchester spielt wunderschöne Musik.", "answer": "berühmte", "options": ["berühmte", "stumme", "schlechte"]},
        {"text": "Die Tierärztin ___ kranke Tiere liebevoll.", "answer": "pflegt", "options": ["pflegt", "ignoriert", "versteckt"]},
        {"text": "Das ___ Schloss zieht viele Touristen an.", "answer": "märchenhafte", "options": ["märchenhafte", "hässliche", "versteckte"]},
        {"text": "Mein Onkel ___ ein erfolgreiches Unternehmen.", "answer": "leitet", "options": ["leitet", "zerstört", "versteckt"]},
        {"text": "Die ___ Erfindung veränderte die Welt.", "answer": "revolutionäre", "options": ["revolutionäre", "nutzlose", "vergessene"]},
        {"text": "Der Gärtner ___ wunderschöne Blumenbeete.", "answer": "gestaltet", "options": ["gestaltet", "zerstört", "ignoriert"]},
        {"text": "Das ___ Theater zeigt klassische Stücke.", "answer": "renommierte", "options": ["renommierte", "geschlossene", "langweilige"]},
        {"text": "Die Fotografin ___ atemberaubende Landschaften.", "answer": "fotografiert", "options": ["fotografiert", "zerstört", "versteckt"]},
        {"text": "Das ___ Projekt wurde erfolgreich abgeschlossen.", "answer": "ambitionierte", "options": ["ambitionierte", "gescheiterte", "vergessene"]},
        {"text": "Der Mechaniker ___ defekte Motoren geschickt.", "answer": "repariert", "options": ["repariert", "zerstört", "versteckt"]},
        {"text": "Die ___ Ausstellung zieht Kunstliebhaber an.", "answer": "außergewöhnliche", "options": ["außergewöhnliche", "langweilige", "versteckte"]},
        {"text": "Unser Hausarzt ___ uns seit vielen Jahren.", "answer": "betreut", "options": ["betreut", "ignoriert", "vergisst"]},
        {"text": "Das ___ Gebäude wurde zum Denkmal erklärt.", "answer": "historische", "options": ["historische", "neue", "hässliche"]},
        {"text": "Die Köchin ___ exquisite Menüs für das Restaurant.", "answer": "kreiert", "options": ["kreiert", "zerstört", "versteckt"]},
        {"text": "Das ___ System arbeitet vollautomatisch.", "answer": "hochmoderne", "options": ["hochmoderne", "kaputte", "alte"]},
        {"text": "Der Psychologe ___ Menschen bei seelischen Problemen.", "answer": "unterstützt", "options": ["unterstützt", "ignoriert", "versteckt"]},
        {"text": "Die ___ Forschung bringt neue Erkenntnisse.", "answer": "intensive", "options": ["intensive", "nutzlose", "vergessene"]},
        {"text": "Der Dirigent ___ das Orchester meisterhaft.", "answer": "leitet", "options": ["leitet", "stört", "ignoriert"]},
        {"text": "Die ___ Technologie revolutioniert unser Leben.", "answer": "innovative", "options": ["innovative", "veraltete", "nutzlose"]},
        {"text": "Meine Nachbarin ___ als Übersetzerin.", "answer": "arbeitet", "options": ["arbeitet", "schläft", "versteckt"]},
        {"text": "Das ___ Gemälde hängt im berühmten Museum.", "answer": "kostbare", "options": ["kostbare", "hässliche", "zerrissene"]},
        {"text": "Der Ingenieur ___ innovative Maschinen.", "answer": "entwickelt", "options": ["entwickelt", "zerstört", "versteckt"]},
        {"text": "Die ___ Landschaft lädt zum Wandern ein.", "answer": "malerische", "options": ["malerische", "hässliche", "gefährliche"]},
        {"text": "Unser Trainer ___ das Team motiviert.", "answer": "führt", "options": ["führt", "verwirrt", "ignoriert"]},
        {"text": "Das ___ Mikroskop zeigt kleinste Details.", "answer": "leistungsstarke", "options": ["leistungsstarke", "kaputte", "nutzlose"]},
        {"text": "Die Designerin ___ moderne Kleidung.", "answer": "entwirft", "options": ["entwirft", "zerstört", "versteckt"]},
        {"text": "Das ___ Teleskop blickt in die Sterne.", "answer": "präzise", "options": ["präzise", "kaputte", "nutzlose"]},
        {"text": "Der Biologe ___ seltene Tierarten.", "answer": "erforscht", "options": ["erforscht", "jagt", "versteckt"]},
        {"text": "Die ___ Medizin hilft vielen Patienten.", "answer": "moderne", "options": ["moderne", "veraltete", "gefährliche"]},
        {"text": "Unser Bürgermeister ___ wichtige Entscheidungen.", "answer": "trifft", "options": ["trifft", "vermeidet", "vergisst"]},
        {"text": "Das ___ Labor führt wichtige Experimente durch.", "answer": "hochmoderne", "options": ["hochmoderne", "veraltete", "geschlossene"]},
        {"text": "Die Chemikerin ___ neue Substanzen.", "answer": "analysiert", "options": ["analysiert", "versteckt", "zerstört"]},
        {"text": "Das ___ Computerprogramm löst komplexe Probleme.", "answer": "intelligente", "options": ["intelligente", "defekte", "einfache"]},
        {"text": "Der Umweltschützer ___ die Natur.", "answer": "bewahrt", "options": ["bewahrt", "zerstört", "ignoriert"]},
        {"text": "Die ___ Solaranlage produziert saubere Energie.", "answer": "effiziente", "options": ["effiziente", "kaputte", "nutzlose"]},
        {"text": "Unser Nachbar ___ ein elektrisches Auto.", "answer": "fährt", "options": ["fährt", "zerstört", "versteckt"]},
        {"text": "Das ___ Recycling-System schont die Umwelt.", "answer": "durchdachte", "options": ["durchdachte", "nutzlose", "schädliche"]},
        {"text": "Die Meeresbiologin ___ das Leben unter Wasser.", "answer": "untersucht", "options": ["untersucht", "ignoriert", "zerstört"]},
        {"text": "Das ___ Windrad erzeugt erneuerbare Energie.", "answer": "riesige", "options": ["riesige", "winzige", "kaputte"]},
        {"text": "Der Roboter ___ präzise Aufgaben.", "answer": "erledigt", "options": ["erledigt", "vergisst", "zerstört"]},
        {"text": "Die ___ Artificial Intelligence lernt ständig dazu.", "answer": "fortschrittliche", "options": ["fortschrittliche", "primitive", "kaputte"]},
        {"text": "Unser Smartphone ___ uns überall hin.", "answer": "begleitet", "options": ["begleitet", "hindert", "verwirrt"]},
        {"text": "Das ___ Internet verbindet die ganze Welt.", "answer": "globale", "options": ["globale", "lokale", "kaputte"]},
        {"text": "Die Datenwissenschaftlerin ___ komplexe Muster.", "answer": "entdeckt", "options": ["entdeckt", "versteckt", "ignoriert"]},
        {"text": "Das ___ Elektroauto fährt völlig lautlos.", "answer": "moderne", "options": ["moderne", "alte", "kaputte"]},
        {"text": "Der Programmierer ___ nützliche Apps.", "answer": "entwickelt", "options": ["entwickelt", "löscht", "versteckt"]},
        {"text": "Die ___ Drohne überwacht das Gebiet.", "answer": "ferngesteuerte", "options": ["ferngesteuerte", "kaputte", "versteckte"]},
        {"text": "Unser 3D-Drucker ___ komplizierte Objekte.", "answer": "erstellt", "options": ["erstellt", "zerstört", "versteckt"]},
        {"text": "Das ___ Satellitensystem navigiert genau.", "answer": "präzise", "options": ["präzise", "ungenaue", "kaputte"]},
        {"text": "Die Quantenphysikerin ___ die Geheimnisse des Universums.", "answer": "entschlüsselt", "options": ["entschlüsselt", "ignoriert", "versteckt"]},
        {"text": "Das ___ Hologramm schwebt in der Luft.", "answer": "beeindruckende", "options": ["beeindruckende", "langweilige", "unsichtbare"]}
    ]
    
    blanks = grade2_blanks if grade == 2 else grade3_blanks
    
    # Shuffle and select random subset to ensure massive variety
    import random
    shuffled_blanks = random.sample(blanks, min(count * 3, len(blanks)))
    
    for i in range(min(count, len(shuffled_blanks))):
        blank = shuffled_blanks[i]
        
        problem = GermanProblem(
            question=f"Setze das richtige Wort ein:\n\n{blank['text']}",
            question_type="fill_blank",
            options=blank["options"],
            correct_answer=blank["answer"],
            problem_data={"original_text": blank["text"]}
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
    """Generate spelling problems using AI"""
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    system_message = f"""Du bist ein Deutsch-Lehrer für Kinder. Erstelle genau {count} Rechtschreibaufgaben für Klasse {grade}.

AUFGABENFORMAT:
- Multiple Choice Fragen zur richtigen Schreibweise
- Eine richtige Antwort und 2-3 falsche Alternativen
- Altersgerechte Wörter für Klasse {grade}
- Typische Rechtschreibfehler als falsche Optionen

Gib NUR ein JSON-Array zurück in genau diesem Format:
[{{"question": "Welches Wort ist richtig geschrieben?", "options": ["Hund", "Hunt", "Hundt"], "correct_answer": "Hund"}}]

Fokussiere auf häufige Rechtschreibfehler und verwende bekannte Wörter."""

    try:
        chat = LlmChat(
            api_key=openai_key,
            session_id=f"german-spelling-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Generiere {count} Rechtschreibaufgaben für Klasse {grade}")
        response = await chat.send_message(user_message)
        
        problems_data = json.loads(response.strip())
        problems = []
        
        for problem_data in problems_data[:count]:
            problem = GermanProblem(
                question=problem_data["question"],
                question_type="spelling",
                options=problem_data["options"],
                correct_answer=problem_data["correct_answer"]
            )
            problems.append(problem)
        
        return problems
        
    except Exception as e:
        logging.error(f"Error generating AI spelling problems: {e}")
        return []

async def generate_ai_word_type_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate word type problems using AI"""
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    system_message = f"""Du bist ein Deutsch-Lehrer für Kinder. Erstelle genau {count} Wortarten-Aufgaben für Klasse {grade}.

AUFGABENFORMAT:
- Identifikation von Nomen, Verben, Adjektiven in Sätzen
- Einfache, altersgerechte Sätze
- Klare Markierung des zu identifizierenden Wortes
- Multiple Choice mit den drei Hauptwortarten

Gib NUR ein JSON-Array zurück:
[{{"question": "Welche Wortart ist das unterstrichene Wort?\\n\\nSatz: \\"Der Hund bellt laut.\\"\\nWort: \\"Hund\\"", "options": ["Nomen", "Verb", "Adjektiv"], "correct_answer": "Nomen"}}]"""

    try:
        chat = LlmChat(
            api_key=openai_key,
            session_id=f"german-wordtype-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Generiere {count} Wortarten-Aufgaben für Klasse {grade}")
        response = await chat.send_message(user_message)
        
        problems_data = json.loads(response.strip())
        problems = []
        
        for problem_data in problems_data[:count]:
            problem = GermanProblem(
                question=problem_data["question"],
                question_type="word_types",
                options=problem_data["options"],
                correct_answer=problem_data["correct_answer"]
            )
            problems.append(problem)
        
        return problems
        
    except Exception as e:
        logging.error(f"Error generating AI word type problems: {e}")
        return []

async def generate_ai_fill_blank_problems(count: int, grade: int, settings: GermanSettings) -> List[GermanProblem]:
    """Generate fill-in-the-blank problems using AI"""
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    system_message = f"""Du bist ein Deutsch-Lehrer für Kinder. Erstelle genau {count} Lückentext-Aufgaben für Klasse {grade}.

AUFGABENFORMAT:
- Einfache Sätze mit einer Lücke
- Das fehlende Wort soll logisch und eindeutig sein
- Multiple Choice mit einer richtigen und 2 falschen Antworten
- Altersgerechte Themen und Wörter

Gib NUR ein JSON-Array zurück:
[{{"question": "Setze das richtige Wort ein:\\n\\nDer ___ bellt laut.", "options": ["Hund", "Katze", "Vogel"], "correct_answer": "Hund"}}]"""

    try:
        chat = LlmChat(
            api_key=openai_key,
            session_id=f"german-fillblank-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Generiere {count} Lückentext-Aufgaben für Klasse {grade}")
        response = await chat.send_message(user_message)
        
        problems_data = json.loads(response.strip())
        problems = []
        
        for problem_data in problems_data[:count]:
            problem = GermanProblem(
                question=problem_data["question"],
                question_type="fill_blank",
                options=problem_data["options"],
                correct_answer=problem_data["correct_answer"]
            )
            problems.append(problem)
        
        return problems
        
    except Exception as e:
        logging.error(f"Error generating AI fill blank problems: {e}")
        return []

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
    """Generate German to English vocabulary problems"""
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
    
    # Fallback to predefined vocabulary problems
    grade2_vocabulary = [
        {"german": "Hund", "english": "dog", "wrong": ["cat", "bird", "fish"]},
        {"german": "Katze", "english": "cat", "wrong": ["dog", "mouse", "bird"]},
        {"german": "Auto", "english": "car", "wrong": ["bus", "train", "bike"]},
        {"german": "Haus", "english": "house", "wrong": ["tree", "car", "book"]},
        {"german": "Baum", "english": "tree", "wrong": ["flower", "grass", "house"]},
        {"german": "Wasser", "english": "water", "wrong": ["milk", "juice", "tea"]},
        {"german": "Brot", "english": "bread", "wrong": ["cake", "apple", "cheese"]},
        {"german": "Apfel", "english": "apple", "wrong": ["banana", "orange", "grape"]},
        {"german": "Schule", "english": "school", "wrong": ["home", "park", "shop"]},
        {"german": "Buch", "english": "book", "wrong": ["pen", "paper", "table"]},
        {"german": "rot", "english": "red", "wrong": ["blue", "green", "yellow"]},
        {"german": "blau", "english": "blue", "wrong": ["red", "green", "black"]},
        {"german": "groß", "english": "big", "wrong": ["small", "long", "fast"]},
        {"german": "klein", "english": "small", "wrong": ["big", "tall", "wide"]},
        {"german": "gut", "english": "good", "wrong": ["bad", "fast", "slow"]},
        {"german": "Ball", "english": "ball", "wrong": ["toy", "game", "stick"]},
        {"german": "Mama", "english": "mom", "wrong": ["dad", "sister", "brother"]},
        {"german": "Papa", "english": "dad", "wrong": ["mom", "uncle", "grandpa"]},
        {"german": "Kind", "english": "child", "wrong": ["adult", "baby", "parent"]},
        {"german": "Freund", "english": "friend", "wrong": ["enemy", "teacher", "doctor"]},
        {"german": "Sonne", "english": "sun", "wrong": ["moon", "star", "cloud"]},
        {"german": "Mond", "english": "moon", "wrong": ["sun", "star", "planet"]},
        {"german": "Blume", "english": "flower", "wrong": ["tree", "grass", "leaf"]},
        {"german": "Vogel", "english": "bird", "wrong": ["fish", "cat", "dog"]},
        {"german": "Fisch", "english": "fish", "wrong": ["bird", "cat", "mouse"]},
        {"german": "Maus", "english": "mouse", "wrong": ["cat", "dog", "bird"]},
        {"german": "Tür", "english": "door", "wrong": ["window", "wall", "roof"]},
        {"german": "Fenster", "english": "window", "wrong": ["door", "wall", "floor"]},
        {"german": "Tisch", "english": "table", "wrong": ["chair", "bed", "sofa"]},
        {"german": "Stuhl", "english": "chair", "wrong": ["table", "bed", "lamp"]},
        {"german": "warm", "english": "warm", "wrong": ["cold", "hot", "cool"]},
        {"german": "kalt", "english": "cold", "wrong": ["warm", "hot", "cool"]},
        {"german": "schnell", "english": "fast", "wrong": ["slow", "big", "small"]},
        {"german": "langsam", "english": "slow", "wrong": ["fast", "quick", "rapid"]},
        {"german": "neu", "english": "new", "wrong": ["old", "used", "broken"]},
        {"german": "alt", "english": "old", "wrong": ["new", "young", "fresh"]},
        {"german": "glücklich", "english": "happy", "wrong": ["sad", "angry", "tired"]},
        {"german": "traurig", "english": "sad", "wrong": ["happy", "glad", "joyful"]},
        {"german": "Milch", "english": "milk", "wrong": ["water", "juice", "tea"]},
        {"german": "Käse", "english": "cheese", "wrong": ["bread", "butter", "meat"]},
        {"german": "Ei", "english": "egg", "wrong": ["chicken", "milk", "bread"]},
        {"german": "Fleisch", "english": "meat", "wrong": ["bread", "fruit", "vegetable"]},
        {"german": "Gemüse", "english": "vegetable", "wrong": ["fruit", "meat", "bread"]},
        {"german": "Obst", "english": "fruit", "wrong": ["vegetable", "meat", "bread"]},
        {"german": "Banane", "english": "banana", "wrong": ["apple", "orange", "grape"]},
        {"german": "Orange", "english": "orange", "wrong": ["apple", "banana", "lemon"]},
        {"german": "Zitrone", "english": "lemon", "wrong": ["orange", "apple", "lime"]},
        {"german": "Traube", "english": "grape", "wrong": ["berry", "cherry", "plum"]},
        {"german": "Kirsche", "english": "cherry", "wrong": ["grape", "berry", "plum"]},
        {"german": "Erdbeere", "english": "strawberry", "wrong": ["cherry", "grape", "berry"]},
        {"german": "Familie", "english": "family", "wrong": ["friends", "people", "group"]},
        {"german": "Bruder", "english": "brother", "wrong": ["sister", "cousin", "friend"]},
        {"german": "Schwester", "english": "sister", "wrong": ["brother", "cousin", "friend"]},
        {"german": "Oma", "english": "grandma", "wrong": ["mom", "aunt", "sister"]},
        {"german": "Opa", "english": "grandpa", "wrong": ["dad", "uncle", "brother"]},
        {"german": "Tante", "english": "aunt", "wrong": ["mom", "sister", "cousin"]},
        {"german": "Onkel", "english": "uncle", "wrong": ["dad", "brother", "cousin"]},
        {"german": "Baby", "english": "baby", "wrong": ["child", "adult", "teenager"]},
        {"german": "Junge", "english": "boy", "wrong": ["girl", "man", "child"]},
        {"german": "Mädchen", "english": "girl", "wrong": ["boy", "woman", "child"]},
        {"german": "Mann", "english": "man", "wrong": ["woman", "boy", "person"]},
        {"german": "Frau", "english": "woman", "wrong": ["man", "girl", "person"]},
        {"german": "Tier", "english": "animal", "wrong": ["plant", "person", "thing"]},
        {"german": "Pferd", "english": "horse", "wrong": ["cow", "pig", "sheep"]},
        {"german": "Kuh", "english": "cow", "wrong": ["horse", "pig", "goat"]},
        {"german": "Schwein", "english": "pig", "wrong": ["cow", "horse", "sheep"]},
        {"german": "Schaf", "english": "sheep", "wrong": ["goat", "cow", "pig"]},
        {"german": "Ziege", "english": "goat", "wrong": ["sheep", "cow", "horse"]},
        {"german": "Hase", "english": "rabbit", "wrong": ["mouse", "cat", "hamster"]},
        {"german": "Hamster", "english": "hamster", "wrong": ["mouse", "rabbit", "rat"]},
        {"german": "spielen", "english": "to play", "wrong": ["to work", "to sleep", "to eat"]},
        {"german": "laufen", "english": "to run", "wrong": ["to walk", "to jump", "to sit"]},
        {"german": "gehen", "english": "to go", "wrong": ["to come", "to stay", "to stop"]},
        {"german": "kommen", "english": "to come", "wrong": ["to go", "to leave", "to stay"]},
        {"german": "essen", "english": "to eat", "wrong": ["to drink", "to sleep", "to play"]},
        {"german": "trinken", "english": "to drink", "wrong": ["to eat", "to sleep", "to walk"]},
        {"german": "schlafen", "english": "to sleep", "wrong": ["to wake", "to eat", "to play"]},
        {"german": "sehen", "english": "to see", "wrong": ["to hear", "to feel", "to smell"]},
        {"german": "hören", "english": "to hear", "wrong": ["to see", "to feel", "to taste"]},
        {"german": "sprechen", "english": "to speak", "wrong": ["to listen", "to write", "to read"]},
        {"german": "lesen", "english": "to read", "wrong": ["to write", "to speak", "to listen"]},
        {"german": "schreiben", "english": "to write", "wrong": ["to read", "to draw", "to paint"]},
        {"german": "malen", "english": "to paint", "wrong": ["to draw", "to write", "to color"]},
        {"german": "singen", "english": "to sing", "wrong": ["to dance", "to play", "to listen"]},
        {"german": "tanzen", "english": "to dance", "wrong": ["to sing", "to jump", "to run"]},
        {"german": "springen", "english": "to jump", "wrong": ["to run", "to walk", "to dance"]},
        {"german": "schwimmen", "english": "to swim", "wrong": ["to run", "to fly", "to walk"]},
        {"german": "fliegen", "english": "to fly", "wrong": ["to swim", "to run", "to jump"]},
        {"german": "fahren", "english": "to drive", "wrong": ["to walk", "to fly", "to swim"]},
        {"german": "arbeiten", "english": "to work", "wrong": ["to play", "to rest", "to sleep"]},
        {"german": "lernen", "english": "to learn", "wrong": ["to teach", "to forget", "to play"]},
        {"german": "lehren", "english": "to teach", "wrong": ["to learn", "to study", "to play"]},
        {"german": "helfen", "english": "to help", "wrong": ["to hurt", "to ignore", "to leave"]},
        {"german": "kaufen", "english": "to buy", "wrong": ["to sell", "to give", "to take"]},
        {"german": "verkaufen", "english": "to sell", "wrong": ["to buy", "to give", "to keep"]},
        {"german": "geben", "english": "to give", "wrong": ["to take", "to keep", "to sell"]},
        {"german": "nehmen", "english": "to take", "wrong": ["to give", "to leave", "to put"]},
        {"german": "haben", "english": "to have", "wrong": ["to be", "to get", "to lose"]},
        {"german": "sein", "english": "to be", "wrong": ["to have", "to do", "to go"]},
        {"german": "werden", "english": "to become", "wrong": ["to be", "to have", "to stay"]},
        {"german": "machen", "english": "to make", "wrong": ["to break", "to fix", "to buy"]},
        {"german": "tun", "english": "to do", "wrong": ["to make", "to be", "to have"]},
        {"german": "können", "english": "can", "wrong": ["must", "should", "will"]},
        {"german": "müssen", "english": "must", "wrong": ["can", "may", "should"]},
        {"german": "wollen", "english": "want", "wrong": ["need", "must", "can"]},
        {"german": "mögen", "english": "like", "wrong": ["hate", "love", "need"]},
        {"german": "lieben", "english": "love", "wrong": ["like", "hate", "need"]},
        {"german": "hassen", "english": "hate", "wrong": ["love", "like", "enjoy"]},
        {"german": "brauchen", "english": "need", "wrong": ["want", "have", "get"]},
        {"german": "bekommen", "english": "get", "wrong": ["give", "take", "have"]},
        {"german": "verlieren", "english": "lose", "wrong": ["find", "win", "get"]},
        {"german": "finden", "english": "find", "wrong": ["lose", "search", "look"]},
        {"german": "suchen", "english": "search", "wrong": ["find", "lose", "get"]},
        {"german": "warten", "english": "wait", "wrong": ["go", "run", "leave"]},
        {"german": "bleiben", "english": "stay", "wrong": ["go", "leave", "come"]},
        {"german": "verlassen", "english": "leave", "wrong": ["stay", "come", "arrive"]},
        {"german": "ankommen", "english": "arrive", "wrong": ["leave", "go", "stay"]},
        {"german": "beginnen", "english": "begin", "wrong": ["end", "stop", "finish"]},
        {"german": "aufhören", "english": "stop", "wrong": ["start", "begin", "continue"]},
        {"german": "weitermachen", "english": "continue", "wrong": ["stop", "end", "pause"]},
        {"german": "Nummer", "english": "number", "wrong": ["letter", "word", "name"]},
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
    
    grade3_vocabulary = [
        {"german": "Wissenschaft", "english": "science", "wrong": ["art", "history", "music"]},
        {"german": "Experiment", "english": "experiment", "wrong": ["test", "game", "lesson"]},
        {"german": "Forschung", "english": "research", "wrong": ["study", "homework", "project"]},
        {"german": "Entdeckung", "english": "discovery", "wrong": ["invention", "creation", "finding"]},
        {"german": "Erfindung", "english": "invention", "wrong": ["discovery", "creation", "idea"]},
        {"german": "Technologie", "english": "technology", "wrong": ["science", "computer", "machine"]},
        {"german": "Computer", "english": "computer", "wrong": ["television", "radio", "phone"]},
        {"german": "Internet", "english": "internet", "wrong": ["computer", "website", "email"]},
        {"german": "Programm", "english": "program", "wrong": ["computer", "software", "game"]},
        {"german": "Software", "english": "software", "wrong": ["hardware", "computer", "program"]},
        {"german": "Roboter", "english": "robot", "wrong": ["machine", "computer", "android"]},
        {"german": "Maschine", "english": "machine", "wrong": ["robot", "tool", "device"]},
        {"german": "Werkzeug", "english": "tool", "wrong": ["machine", "instrument", "device"]},
        {"german": "Instrument", "english": "instrument", "wrong": ["tool", "device", "machine"]},
        {"german": "Gerät", "english": "device", "wrong": ["machine", "tool", "gadget"]},
        {"german": "Energie", "english": "energy", "wrong": ["power", "electricity", "fuel"]},
        {"german": "Elektrizität", "english": "electricity", "wrong": ["energy", "power", "battery"]},
        {"german": "Batterie", "english": "battery", "wrong": ["electricity", "power", "energy"]},
        {"german": "Motor", "english": "engine", "wrong": ["machine", "motor", "device"]},
        {"german": "Fahrzeug", "english": "vehicle", "wrong": ["car", "transport", "machine"]},
        # ... continue with more grade 3 vocabulary
    ]
    
    vocabulary_list = grade2_vocabulary if grade == 2 else grade3_vocabulary
    
    # Shuffle and select random subset to ensure variety
    import random
    shuffled_vocab = random.sample(vocabulary_list, min(count * 3, len(vocabulary_list)))
    
    for i in range(min(count, len(shuffled_vocab))):
        vocab = shuffled_vocab[i]
        options = [vocab["english"]] + vocab["wrong"]
        random.shuffle(options)
        
        problem = EnglishProblem(
            question=f"Was bedeutet '{vocab['german']}' auf Englisch?",
            question_type="vocabulary_de_en",
            options=options,
            correct_answer=vocab["english"],
            problem_data={"german_word": vocab["german"]}
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
    """Generate simple sentence translation problems"""
    problems = []
    
    # Try AI generation first
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            ai_problems = await generate_ai_simple_sentence_problems(count, grade, settings)
            if ai_problems:
                return ai_problems
    except Exception as e:
        logging.error(f"AI simple sentence generation failed: {e}")
    
    # Fallback to predefined simple sentences
    grade2_sentences = [
        {"german": "Ich bin ein Kind.", "english": "I am a child.", "wrong": ["I have a child.", "I see a child.", "I like children."]},
        {"german": "Das Auto ist rot.", "english": "The car is red.", "wrong": ["The car is blue.", "The car is big.", "The car is new."]},
        {"german": "Ich habe einen Hund.", "english": "I have a dog.", "wrong": ["I see a dog.", "I am a dog.", "I like dogs."]},
        {"german": "Die Katze schläft.", "english": "The cat sleeps.", "wrong": ["The cat eats.", "The cat runs.", "The cat plays."]},
        {"german": "Wir gehen zur Schule.", "english": "We go to school.", "wrong": ["We are at school.", "We like school.", "We have school."]},
        {"german": "Mama kocht Essen.", "english": "Mom cooks food.", "wrong": ["Mom eats food.", "Mom buys food.", "Mom likes food."]},
        {"german": "Papa arbeitet viel.", "english": "Dad works a lot.", "wrong": ["Dad sleeps a lot.", "Dad plays a lot.", "Dad eats a lot."]},
        {"german": "Das Haus ist groß.", "english": "The house is big.", "wrong": ["The house is small.", "The house is new.", "The house is old."]},
        {"german": "Ich mag Äpfel.", "english": "I like apples.", "wrong": ["I eat apples.", "I have apples.", "I see apples."]},
        {"german": "Der Ball ist rund.", "english": "The ball is round.", "wrong": ["The ball is big.", "The ball is red.", "The ball is new."]},
        {"german": "Wir spielen im Park.", "english": "We play in the park.", "wrong": ["We walk in the park.", "We sit in the park.", "We run in the park."]},
        {"german": "Die Sonne scheint.", "english": "The sun shines.", "wrong": ["The sun sleeps.", "The sun runs.", "The sun eats."]},
        {"german": "Ich trinke Wasser.", "english": "I drink water.", "wrong": ["I see water.", "I have water.", "I like water."]},
        {"german": "Das Buch ist interessant.", "english": "The book is interesting.", "wrong": ["The book is big.", "The book is new.", "The book is red."]},
        {"german": "Mein Freund ist nett.", "english": "My friend is nice.", "wrong": ["My friend is big.", "My friend is new.", "My friend is old."]},
        {"german": "Die Blume duftet.", "english": "The flower smells good.", "wrong": ["The flower looks good.", "The flower is good.", "The flower feels good."]},
        {"german": "Ich lese gerne.", "english": "I like to read.", "wrong": ["I have to read.", "I can read.", "I will read."]},
        {"german": "Der Vogel singt.", "english": "The bird sings.", "wrong": ["The bird flies.", "The bird eats.", "The bird sleeps."]},
        {"german": "Es regnet heute.", "english": "It rains today.", "wrong": ["It snows today.", "It's sunny today.", "It's windy today."]},
        {"german": "Ich bin müde.", "english": "I am tired.", "wrong": ["I am happy.", "I am sad.", "I am hungry."]},
        {"german": "Das Wetter ist schön.", "english": "The weather is nice.", "wrong": ["The weather is bad.", "The weather is cold.", "The weather is hot."]},
        {"german": "Wir haben Hunger.", "english": "We are hungry.", "wrong": ["We are thirsty.", "We are tired.", "We are happy."]},
        {"german": "Die Kinder lachen.", "english": "The children laugh.", "wrong": ["The children cry.", "The children sleep.", "The children run."]},
        {"german": "Ich helfe Mama.", "english": "I help Mom.", "wrong": ["I see Mom.", "I call Mom.", "I love Mom."]},
        {"german": "Der Fisch schwimmt.", "english": "The fish swims.", "wrong": ["The fish flies.", "The fish runs.", "The fish jumps."]},
        {"german": "Wir lernen Deutsch.", "english": "We learn German.", "wrong": ["We speak German.", "We read German.", "We write German."]},
        {"german": "Das Baby weint.", "english": "The baby cries.", "wrong": ["The baby laughs.", "The baby sleeps.", "The baby eats."]},
        {"german": "Ich wasche meine Hände.", "english": "I wash my hands.", "wrong": ["I see my hands.", "I have my hands.", "I use my hands."]},
        {"german": "Die Uhr tickt.", "english": "The clock ticks.", "wrong": ["The clock rings.", "The clock shows.", "The clock runs."]},
        {"german": "Wir kaufen Brot.", "english": "We buy bread.", "wrong": ["We eat bread.", "We make bread.", "We see bread."]},
        {"german": "Ich höre Musik.", "english": "I listen to music.", "wrong": ["I make music.", "I see music.", "I have music."]},
        {"german": "Der Hund läuft.", "english": "The dog runs.", "wrong": ["The dog sleeps.", "The dog eats.", "The dog barks."]},
        {"german": "Wir malen Bilder.", "english": "We paint pictures.", "wrong": ["We see pictures.", "We have pictures.", "We like pictures."]},
        {"german": "Das Eis ist kalt.", "english": "The ice cream is cold.", "wrong": ["The ice cream is hot.", "The ice cream is sweet.", "The ice cream is big."]},
        {"german": "Ich putze Zähne.", "english": "I brush teeth.", "wrong": ["I see teeth.", "I have teeth.", "I count teeth."]},
        {"german": "Die Tür ist offen.", "english": "The door is open.", "wrong": ["The door is closed.", "The door is big.", "The door is new."]},
        {"german": "Wir singen Lieder.", "english": "We sing songs.", "wrong": ["We hear songs.", "We write songs.", "We like songs."]},
        {"german": "Ich ziehe mich an.", "english": "I get dressed.", "wrong": ["I go to bed.", "I wake up.", "I take a shower."]},
        {"german": "Der Baum ist hoch.", "english": "The tree is tall.", "wrong": ["The tree is short.", "The tree is wide.", "The tree is old."]},
        {"german": "Wir essen Gemüse.", "english": "We eat vegetables.", "wrong": ["We grow vegetables.", "We buy vegetables.", "We like vegetables."]},
        {"german": "Ich spiele Ball.", "english": "I play ball.", "wrong": ["I throw ball.", "I catch ball.", "I see ball."]},
        {"german": "Die Milch ist weiß.", "english": "The milk is white.", "wrong": ["The milk is cold.", "The milk is fresh.", "The milk is good."]},
        {"german": "Wir gehen schlafen.", "english": "We go to sleep.", "wrong": ["We go home.", "We go outside.", "We go shopping."]},
        {"german": "Ich kämme mein Haar.", "english": "I comb my hair.", "wrong": ["I wash my hair.", "I cut my hair.", "I see my hair."]},
        {"german": "Das Fenster ist groß.", "english": "The window is big.", "wrong": ["The window is small.", "The window is clean.", "The window is open."]},
        {"german": "Wir fahren Bus.", "english": "We take the bus.", "wrong": ["We see the bus.", "We wait for the bus.", "We like the bus."]},
        {"german": "Ich füttre die Katze.", "english": "I feed the cat.", "wrong": ["I pet the cat.", "I see the cat.", "I call the cat."]},
        {"german": "Der Käse schmeckt gut.", "english": "The cheese tastes good.", "wrong": ["The cheese looks good.", "The cheese smells good.", "The cheese is good."]},
        {"german": "Wir besuchen Oma.", "english": "We visit Grandma.", "wrong": ["We call Grandma.", "We see Grandma.", "We help Grandma."]},
        {"german": "Ich räume auf.", "english": "I clean up.", "wrong": ["I wake up.", "I get up.", "I give up."]}
    ]
    
    grade3_sentences = [
        {"german": "Ich interessiere mich für Wissenschaft.", "english": "I am interested in science.", "wrong": ["I study science.", "I like science.", "I need science."]},
        {"german": "Der Computer funktioniert nicht.", "english": "The computer doesn't work.", "wrong": ["The computer is broken.", "The computer is old.", "The computer is slow."]},
        {"german": "Wir experimentieren im Labor.", "english": "We experiment in the laboratory.", "wrong": ["We work in the laboratory.", "We study in the laboratory.", "We learn in the laboratory."]},
        {"german": "Die Technologie entwickelt sich schnell.", "english": "Technology develops quickly.", "wrong": ["Technology works quickly.", "Technology changes quickly.", "Technology grows quickly."]},
        {"german": "Ich programmiere einen Roboter.", "english": "I program a robot.", "wrong": ["I build a robot.", "I repair a robot.", "I control a robot."]},
        {"german": "Das Internet verbindet Menschen.", "english": "The internet connects people.", "wrong": ["The internet helps people.", "The internet teaches people.", "The internet shows people."]},
        {"german": "Wir erforschen die Natur.", "english": "We explore nature.", "wrong": ["We protect nature.", "We study nature.", "We love nature."]},
        {"german": "Die Erfindung verändert das Leben.", "english": "The invention changes life.", "wrong": ["The invention improves life.", "The invention helps life.", "The invention makes life."]},
        {"german": "Ich analysiere die Daten.", "english": "I analyze the data.", "wrong": ["I collect the data.", "I save the data.", "I use the data."]},
        {"german": "Der Wissenschaftler macht Entdeckungen.", "english": "The scientist makes discoveries.", "wrong": ["The scientist finds discoveries.", "The scientist has discoveries.", "The scientist shows discoveries."]},
        {"german": "Wir benutzen moderne Geräte.", "english": "We use modern devices.", "wrong": ["We buy modern devices.", "We repair modern devices.", "We need modern devices."]},
        {"german": "Die Maschine arbeitet automatisch.", "english": "The machine works automatically.", "wrong": ["The machine runs automatically.", "The machine starts automatically.", "The machine stops automatically."]},
        {"german": "Ich löse komplizierte Probleme.", "english": "I solve complicated problems.", "wrong": ["I find complicated problems.", "I have complicated problems.", "I see complicated problems."]},
        {"german": "Das System ist sehr effizient.", "english": "The system is very efficient.", "wrong": ["The system is very fast.", "The system is very good.", "The system is very new."]},
        {"german": "Wir entwickeln neue Software.", "english": "We develop new software.", "wrong": ["We use new software.", "We buy new software.", "We test new software."]},
        {"german": "Die Energie kommt von der Sonne.", "english": "The energy comes from the sun.", "wrong": ["The energy needs the sun.", "The energy uses the sun.", "The energy makes the sun."]},
        {"german": "Ich konstruiere eine Brücke.", "english": "I construct a bridge.", "wrong": ["I design a bridge.", "I build a bridge.", "I plan a bridge."]},
        {"german": "Der Motor verbraucht wenig Benzin.", "english": "The engine uses little gasoline.", "wrong": ["The engine needs little gasoline.", "The engine has little gasoline.", "The engine makes little gasoline."]},
        {"german": "Wir kommunizieren über das Internet.", "english": "We communicate via the internet.", "wrong": ["We work via the internet.", "We learn via the internet.", "We play via the internet."]},
        {"german": "Die Batterie speichert Elektrizität.", "english": "The battery stores electricity.", "wrong": ["The battery makes electricity.", "The battery uses electricity.", "The battery needs electricity."]},
        {"german": "Ich repariere defekte Geräte.", "english": "I repair broken devices.", "wrong": ["I find broken devices.", "I buy broken devices.", "I throw broken devices."]},
        {"german": "Das Mikroskop vergrößert kleine Objekte.", "english": "The microscope magnifies small objects.", "wrong": ["The microscope finds small objects.", "The microscope makes small objects.", "The microscope shows small objects."]},
        {"german": "Wir dokumentieren unsere Experimente.", "english": "We document our experiments.", "wrong": ["We plan our experiments.", "We finish our experiments.", "We start our experiments."]},
        {"german": "Die Forschung bringt neue Erkenntnisse.", "english": "Research brings new insights.", "wrong": ["Research finds new insights.", "Research makes new insights.", "Research needs new insights."]},
        {"german": "Ich installiere ein neues Programm.", "english": "I install a new program.", "wrong": ["I buy a new program.", "I use a new program.", "I test a new program."]},
        {"german": "Der Satellit umkreist die Erde.", "english": "The satellite orbits the Earth.", "wrong": ["The satellite flies around the Earth.", "The satellite watches the Earth.", "The satellite protects the Earth."]},
        {"german": "Wir messen die Temperatur.", "english": "We measure the temperature.", "wrong": ["We check the temperature.", "We change the temperature.", "We control the temperature."]},
        {"german": "Die Innovation revolutioniert die Industrie.", "english": "The innovation revolutionizes the industry.", "wrong": ["The innovation helps the industry.", "The innovation changes the industry.", "The innovation improves the industry."]},
        {"german": "Ich kalibriere das Instrument.", "english": "I calibrate the instrument.", "wrong": ["I use the instrument.", "I repair the instrument.", "I test the instrument."]},
        {"german": "Das Labor ist steril und sauber.", "english": "The laboratory is sterile and clean.", "wrong": ["The laboratory is big and clean.", "The laboratory is new and clean.", "The laboratory is modern and clean."]}
    ]
    
    sentences = grade2_sentences if grade == 2 else grade3_sentences
    
    # Shuffle and select random subset to ensure variety
    import random
    shuffled_sentences = random.sample(sentences, min(count * 3, len(sentences)))
    
    for i in range(min(count, len(shuffled_sentences))):
        sentence = shuffled_sentences[i]
        options = [sentence["english"]] + sentence["wrong"]
        random.shuffle(options)
        
        problem = EnglishProblem(
            question=f"Wie übersetzt man diesen Satz ins Englische?\n\n'{sentence['german']}'",
            question_type="simple_sentences",
            options=options,
            correct_answer=sentence["english"],
            problem_data={"german_sentence": sentence["german"]}
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
    """Generate German to English vocabulary problems using AI"""
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    system_message = f"""Du bist ein Englisch-Lehrer für deutsche Kinder. Erstelle genau {count} Deutsch-zu-Englisch Vokabel-Aufgaben für Klasse {grade}.

AUFGABENFORMAT:
- Deutsche Wörter ins Englische übersetzen
- Multiple Choice mit einer richtigen und 2-3 falschen englischen Antworten
- Altersgerechte, einfache Vokabeln für Klasse {grade}
- Fokus auf Grundwortschatz: Tiere, Familie, Farben, Zahlen, Alltag

Gib NUR ein JSON-Array zurück:
[{{"question": "Was bedeutet 'Hund' auf Englisch?", "options": ["dog", "cat", "bird"], "correct_answer": "dog"}}]"""

    try:
        chat = LlmChat(
            api_key=openai_key,
            session_id=f"english-vocab-de-en-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Generiere {count} Deutsch-zu-Englisch Vokabel-Aufgaben für Klasse {grade}")
        response = await chat.send_message(user_message)
        
        problems_data = json.loads(response.strip())
        problems = []
        
        for problem_data in problems_data[:count]:
            problem = EnglishProblem(
                question=problem_data["question"],
                question_type="vocabulary_de_en",
                options=problem_data["options"],
                correct_answer=problem_data["correct_answer"]
            )
            problems.append(problem)
        
        return problems
        
    except Exception as e:
        logging.error(f"Error generating AI DE->EN vocabulary problems: {e}")
        return []

async def generate_ai_vocabulary_en_de_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate English to German vocabulary problems using AI"""
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    system_message = f"""Du bist ein Englisch-Lehrer für deutsche Kinder. Erstelle genau {count} Englisch-zu-Deutsch Vokabel-Aufgaben für Klasse {grade}.

AUFGABENFORMAT:
- Englische Wörter ins Deutsche übersetzen
- Multiple Choice mit einer richtigen und 2-3 falschen deutschen Antworten
- Altersgerechte, einfache Vokabeln für Klasse {grade}
- Fokus auf Grundwortschatz: Tiere, Familie, Farben, Zahlen, Alltag

Gib NUR ein JSON-Array zurück:
[{{"question": "Was bedeutet 'dog' auf Deutsch?", "options": ["Hund", "Katze", "Vogel"], "correct_answer": "Hund"}}]"""

    try:
        chat = LlmChat(
            api_key=openai_key,
            session_id=f"english-vocab-en-de-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Generiere {count} Englisch-zu-Deutsch Vokabel-Aufgaben für Klasse {grade}")
        response = await chat.send_message(user_message)
        
        problems_data = json.loads(response.strip())
        problems = []
        
        for problem_data in problems_data[:count]:
            problem = EnglishProblem(
                question=problem_data["question"],
                question_type="vocabulary_en_de",
                options=problem_data["options"],
                correct_answer=problem_data["correct_answer"]
            )
            problems.append(problem)
        
        return problems
        
    except Exception as e:
        logging.error(f"Error generating AI EN->DE vocabulary problems: {e}")
        return []

async def generate_ai_simple_sentence_problems(count: int, grade: int, settings: EnglishSettings) -> List[EnglishProblem]:
    """Generate simple sentence translation problems using AI"""
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    system_message = f"""Du bist ein Englisch-Lehrer für deutsche Kinder. Erstelle genau {count} einfache Satz-Übersetzungsaufgaben für Klasse {grade}.

AUFGABENFORMAT:
- Deutsche Sätze ins Englische übersetzen
- Multiple Choice mit einer richtigen und 2-3 falschen englischen Übersetzungen
- Sehr einfache, kurze Sätze für Klasse {grade}
- Grundlegende Satzstrukturen mit bekanntem Vokabular

Gib NUR ein JSON-Array zurück:
[{{"question": "Wie übersetzt man 'Ich bin ein Kind.' ins Englische?", "options": ["I am a child.", "I have a child.", "I see a child."], "correct_answer": "I am a child."}}]"""

    try:
        chat = LlmChat(
            api_key=openai_key,
            session_id=f"english-sentences-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Generiere {count} einfache Satz-Übersetzungsaufgaben für Klasse {grade}")
        response = await chat.send_message(user_message)
        
        problems_data = json.loads(response.strip())
        problems = []
        
        for problem_data in problems_data[:count]:
            problem = EnglishProblem(
                question=problem_data["question"],
                question_type="simple_sentences",
                options=problem_data["options"],
                correct_answer=problem_data["correct_answer"]
            )
            problems.append(problem)
        
        return problems
        
    except Exception as e:
        logging.error(f"Error generating AI simple sentence problems: {e}")
        return []

# Helper functions
def get_current_week_start():
    today = datetime.now()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

async def generate_math_problems(grade: int, count: int = None) -> List[MathProblem]:
    """Generate AI-powered math problems using OpenAI with extended problem types"""
    
    # Get math settings
    settings_doc = await db.math_settings.find_one()
    if not settings_doc:
        settings = MathSettings()
        await db.math_settings.insert_one(settings.dict())
    else:
        settings = MathSettings(**settings_doc)
    
    # Use configured problem count if not specified
    if count is None:
        count = settings.problem_count
    
    # Generate mix of problems based on enabled types
    problems = []
    enabled_types = [k for k, v in settings.problem_types.items() if v]
    
    if not enabled_types:
        enabled_types = ["addition", "subtraction", "multiplication"]  # fallback
    
    problems_per_type = count // len(enabled_types)
    remaining = count % len(enabled_types)
    
    for problem_type in enabled_types:
        type_count = problems_per_type + (1 if remaining > 0 else 0)
        remaining -= 1
        
        if problem_type == "clock_reading":
            problems.extend(generate_clock_problems(type_count, settings))
        elif problem_type == "currency_math":
            problems.extend(generate_currency_problems(type_count, settings))
        elif problem_type == "word_problems":
            problems.extend(generate_german_word_problems(type_count, grade, settings))
        else:
            # Generate traditional math problems via AI (with fallback)
            try:
                openai_key = os.environ.get('OPENAI_API_KEY')
                if openai_key:
                    ai_problems = await generate_ai_math_problems(problem_type, grade, type_count, settings)
                    problems.extend(ai_problems)
                else:
                    problems.extend(await generate_simple_math_problems(grade, type_count, settings))
            except Exception as e:
                logging.error(f"AI generation failed for {problem_type}: {e}")
                problems.extend(await generate_simple_math_problems(grade, type_count, settings))
    
    # Shuffle the problems
    random.shuffle(problems)
    return problems[:count]

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
    """Generate traditional math problems using AI"""
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    type_descriptions = {
        "addition": "Addition",
        "subtraction": "Subtraktion", 
        "multiplication": "Multiplikation",
        "word_problems": "Textaufgaben"
    }
    
    type_desc = type_descriptions.get(problem_type, "Mathematik")
    
    # Create appropriate system message based on problem type
    if problem_type == "word_problems":
        system_message = f"""Du bist ein Mathe-Aufgaben-Generator für Kinder. Erstelle genau {count} {type_desc} für Klasse {grade}.

WICHTIGE BESCHRÄNKUNGEN:
- ALLE Antworten müssen zwischen 1 und 100 liegen (niemals über 100)
- Für Klasse {grade}: Textaufgaben mit Zahlen bis {settings.max_number}
- Erstelle realistische Alltagssituationen für Kinder
- Verwende nur deutsche Sprache
- Die Geschichten sollen einfach und verständlich sein

Gib NUR ein JSON-Array von Objekten zurück in genau diesem Format:
[{{"question": "Anna hat 12 Äpfel. Sie gibt 5 Äpfel an ihre Freundin. Wie viele Äpfel hat Anna noch?", "answer": "7"}}, {{"question": "Tom sammelt 8 Sticker am Montag und 6 Sticker am Dienstag. Wie viele Sticker hat er insgesamt?", "answer": "14"}}]

Erstelle abwechslungsreiche Textaufgaben mit verschiedenen Alltagssituationen. Überprüfe doppelt, dass ALLE Antworten 100 oder weniger sind."""
    else:
        system_message = f"""Du bist ein Mathe-Aufgaben-Generator für Kinder. Erstelle genau {count} {type_desc}-Aufgaben für Klasse {grade}.

WICHTIGE BESCHRÄNKUNGEN:
- ALLE Antworten müssen zwischen 1 und 100 liegen (niemals über 100)
- Für Klasse {grade}: {type_desc} mit Zahlen bis {settings.max_number}
- Bei Multiplikation: maximal bis x{settings.max_multiplication}
- Stelle sicher, dass keine Antwort 100 überschreitet
- Verwende nur deutsche Sprache

Gib NUR ein JSON-Array von Objekten zurück in genau diesem Format:
[{{"question": "Was ist 5 + 3?", "answer": "8"}}, {{"question": "Was ist 3 + 5?", "answer": "8"}}]

Erstelle abwechslungsreiche aber altersgerechte Aufgaben. Fokus auf Zahlen, keine komplexen Textaufgaben. Überprüfe doppelt, dass ALLE Antworten 100 oder weniger sind."""

    try:
        chat = LlmChat(
            api_key=openai_key,
            session_id=f"math-gen-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Generiere {count} {type_desc}-Aufgaben für Klasse {grade}")
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        problems_data = json.loads(response.strip())
        
        problems = []
        for i, problem_data in enumerate(problems_data[:count]):
            answer_str = str(problem_data["answer"])
            
            # Ensure numeric answers don't exceed 100
            try:
                if answer_str.replace(".", "").replace(",", "").isdigit():
                    numeric_val = float(answer_str.replace(",", "."))
                    if numeric_val > 100:
                        continue  # Skip problems with answers > 100
            except:
                pass  # Non-numeric answers are ok
            
            problem = MathProblem(
                question=problem_data["question"],
                question_type="text",
                correct_answer=answer_str
            )
            problems.append(problem)
        
        return problems
        
    except Exception as e:
        logging.error(f"Error generating AI math problems: {e}")
        # Fallback to simple generated problems
        return await generate_simple_math_problems(grade, count, settings)

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