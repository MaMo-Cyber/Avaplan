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
    """Generate German spelling problems using AI with fallback templates"""
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
    
    # Fallback to predefined spelling problems
    grade2_words = [
        {"correct": "Hund", "wrong": ["Hunt", "Hundt", "Huhnd"]},
        {"correct": "Haus", "wrong": ["Hauss", "Heus", "Hous"]},
        {"correct": "Ball", "wrong": ["Bal", "Bahl", "Balle"]},
        {"correct": "Auto", "wrong": ["Autto", "Outo", "Autho"]},
        {"correct": "Baum", "wrong": ["Boum", "Bauhm", "Baumb"]},
        {"correct": "Buch", "wrong": ["Buuch", "Buhch", "Booch"]},
        {"correct": "Tisch", "wrong": ["Tish", "Tishch", "Tiisch"]},
        {"correct": "Stuhl", "wrong": ["Stul", "Sthuhl", "Stuuhl"]},
        {"correct": "Kind", "wrong": ["Kint", "Kindt", "Kihnd"]},
        {"correct": "Mama", "wrong": ["Mamma", "Mahma", "Mema"]}
    ]
    
    grade3_words = [
        {"correct": "Freundin", "wrong": ["Freundhin", "Freundihn", "Freindin"]},
        {"correct": "Schule", "wrong": ["Schuhle", "Schuele", "Schuhle"]},
        {"correct": "Lehrer", "wrong": ["Lerer", "Lehhrer", "Lehrrer"]},
        {"correct": "Aufgabe", "wrong": ["Aufgaabe", "Aufkabe", "Aufgahbe"]},
        {"correct": "Geschichte", "wrong": ["Geschicte", "Geschischte", "Geschiechte"]},
        {"correct": "Mathematik", "wrong": ["Mathmatik", "Matematik", "Mahtematik"]},
        {"correct": "Spielplatz", "wrong": ["Spilplatz", "Spielplaz", "Spieplatz"]},
        {"correct": "Geburtstag", "wrong": ["Geburtztag", "Geburstag", "Geburtstaag"]},
        {"correct": "Wochenende", "wrong": ["Wochenehende", "Wochenente", "Wohchenende"]},
        {"correct": "Nachmittag", "wrong": ["Nachhmittag", "Nachmitag", "Nachmittagg"]}
    ]
    
    word_list = grade2_words if grade == 2 else grade3_words
    
    for i in range(min(count, len(word_list))):
        word_data = random.choice(word_list)
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
    
    # Fallback templates
    grade2_examples = [
        {"sentence": "Der Hund bellt laut.", "word": "Hund", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Auto fährt schnell.", "word": "fährt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Blume ist schön.", "word": "schön", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Mama kocht Suppe.", "word": "kocht", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der Ball ist rund.", "word": "Ball", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Papa liest ein Buch.", "word": "liest", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Haus ist groß.", "word": "groß", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Katze schläft.", "word": "Katze", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]}
    ]
    
    grade3_examples = [
        {"sentence": "Die Lehrerin erklärt die Aufgabe sehr deutlich.", "word": "erklärt", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das neue Fahrrad steht im Garten.", "word": "neue", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Mein Bruder spielt gerne Fußball.", "word": "Bruder", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die Kinder laufen schnell zum Spielplatz.", "word": "laufen", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Der schwierige Test ist endlich vorbei.", "word": "schwierige", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Unsere Nachbarin hat einen kleinen Hund.", "word": "Nachbarin", "type": "Nomen", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Das Wetter wird morgen hoffentlich besser.", "word": "wird", "type": "Verb", "options": ["Nomen", "Verb", "Adjektiv"]},
        {"sentence": "Die alte Kirche steht mitten im Dorf.", "word": "alte", "type": "Adjektiv", "options": ["Nomen", "Verb", "Adjektiv"]}
    ]
    
    examples = grade2_examples if grade == 2 else grade3_examples
    
    for i in range(min(count, len(examples))):
        example = random.choice(examples)
        
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
    """Generate fill-in-the-blank problems"""
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
    
    # Fallback templates
    grade2_blanks = [
        {"text": "Der ___ bellt laut.", "answer": "Hund", "options": ["Hund", "Katze", "Vogel"]},
        {"text": "Mama ___ in der Küche.", "answer": "kocht", "options": ["kocht", "singt", "tanzt"]},
        {"text": "Das Auto ist ___.", "answer": "rot", "options": ["rot", "groß", "neu"]},
        {"text": "Wir gehen in die ___.", "answer": "Schule", "options": ["Schule", "Kirche", "Bank"]},
        {"text": "Der Ball ist ___.", "answer": "rund", "options": ["rund", "eckig", "spitz"]},
        {"text": "Papa ___ die Zeitung.", "answer": "liest", "options": ["liest", "kauft", "wirft"]},
        {"text": "Die Sonne ___ hell.", "answer": "scheint", "options": ["scheint", "regnet", "schneit"]},
        {"text": "Im Garten wachsen ___.", "answer": "Blumen", "options": ["Blumen", "Steine", "Autos"]}
    ]
    
    grade3_blanks = [
        {"text": "Die Schüler ___ ihre Hausaufgaben sehr sorgfältig.", "answer": "machen", "options": ["machen", "vergessen", "kaufen"]},
        {"text": "Nach dem Regen bildete sich ein ___ am Himmel.", "answer": "Regenbogen", "options": ["Regenbogen", "Flugzeug", "Stern"]},
        {"text": "Der ___ Lehrer erklärt die Aufgabe noch einmal.", "answer": "geduldige", "options": ["geduldige", "müde", "schnelle"]},
        {"text": "Meine Schwester ___ jeden Tag Klavier.", "answer": "übt", "options": ["übt", "verkauft", "repariert"]},
        {"text": "Im Winter ___ es oft und die Straßen werden glatt.", "answer": "schneit", "options": ["schneit", "blüht", "schwimmt"]},
        {"text": "Die ___ Geschichte hat mir sehr gut gefallen.", "answer": "spannende", "options": ["spannende", "langweilige", "kurze"]},
        {"text": "Opa ___ uns oft von früher.", "answer": "erzählt", "options": ["erzählt", "fragt", "vergisst"]},
        {"text": "Das ___ Buch liegt auf dem Tisch.", "answer": "dicke", "options": ["dicke", "kleine", "alte"]}
    ]
    
    blanks = grade2_blanks if grade == 2 else grade3_blanks
    
    for i in range(min(count, len(blanks))):
        blank = random.choice(blanks)
        
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