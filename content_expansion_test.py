#!/usr/bin/env python3
"""
Content Expansion Testing for Weekly Star Tracker
Tests the newly expanded German and English content as per review request
"""

import requests
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Set

# Configuration
BASE_URL = "https://08ea8e81-0160-4f81-bdfa-a3009c5ac4a3.preview.emergentagent.com/api"
TIMEOUT = 30

class ContentExpansionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.created_resources = {
            'challenges': []
        }
    
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        if response_data:
            result['response'] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
    
    def test_german_spelling_content_expansion(self):
        """Test German spelling problems with massively expanded content"""
        success_count = 0
        
        print("\n📝 Testing German Spelling Content Expansion")
        print("Expected: 500+ spelling words for Grade 2, 500+ for Grade 3")
        
        # Test Grade 2 spelling variety
        try:
            # Configure settings for spelling only
            settings = {
                "problem_count": 20,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "spelling": True,
                    "word_types": False,
                    "fill_blank": False,
                    "grammar": False,
                    "articles": False,
                    "sentence_order": False
                }
            }
            
            response = self.session.put(f"{BASE_URL}/german/settings", json=settings)
            if response.status_code == 200:
                # Create multiple challenges to test variety
                grade2_words = set()
                challenges_created = 0
                
                for i in range(5):  # Create 5 challenges
                    response = self.session.post(f"{BASE_URL}/german/challenge/2")
                    if response.status_code == 200:
                        challenge = response.json()
                        self.created_resources['challenges'].append(challenge["id"])
                        challenges_created += 1
                        
                        problems = challenge.get("problems", [])
                        for problem in problems:
                            if problem.get("question_type") == "spelling":
                                correct_answer = problem.get("correct_answer", "")
                                if correct_answer:
                                    grade2_words.add(correct_answer)
                
                if challenges_created >= 3:
                    unique_words_count = len(grade2_words)
                    if unique_words_count >= 50:  # Expect at least 50 unique words from 5 challenges
                        self.log_test("Grade 2 Spelling Variety", True, 
                                    f"Found {unique_words_count} unique spelling words across {challenges_created} challenges")
                        success_count += 1
                    else:
                        self.log_test("Grade 2 Spelling Variety", False, 
                                    f"Only found {unique_words_count} unique words (expected ≥50)")
                        
                    # Check for expanded content indicators
                    sample_words = list(grade2_words)[:10]
                    expanded_indicators = ["Apfel", "Banane", "Hund", "Katze", "Spinne", "Ameise", "Wurm"]
                    found_indicators = [word for word in expanded_indicators if word in grade2_words]
                    
                    if len(found_indicators) >= 3:
                        self.log_test("Grade 2 Expanded Content Verification", True, 
                                    f"Found expanded content indicators: {found_indicators}")
                        success_count += 1
                    else:
                        self.log_test("Grade 2 Expanded Content Verification", False, 
                                    f"Limited expanded content found: {found_indicators}")
                else:
                    self.log_test("Grade 2 Spelling Challenges", False, 
                                f"Only created {challenges_created} challenges (expected ≥3)")
            else:
                self.log_test("German Spelling Settings", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Grade 2 Spelling Content Expansion", False, f"Exception: {str(e)}")
        
        # Test Grade 3 spelling variety
        try:
            grade3_words = set()
            challenges_created = 0
            
            for i in range(5):  # Create 5 challenges
                response = self.session.post(f"{BASE_URL}/german/challenge/3")
                if response.status_code == 200:
                    challenge = response.json()
                    self.created_resources['challenges'].append(challenge["id"])
                    challenges_created += 1
                    
                    problems = challenge.get("problems", [])
                    for problem in problems:
                        if problem.get("question_type") == "spelling":
                            correct_answer = problem.get("correct_answer", "")
                            if correct_answer:
                                grade3_words.add(correct_answer)
            
            if challenges_created >= 3:
                unique_words_count = len(grade3_words)
                if unique_words_count >= 40:  # Expect at least 40 unique words from 5 challenges
                    self.log_test("Grade 3 Spelling Variety", True, 
                                f"Found {unique_words_count} unique spelling words across {challenges_created} challenges")
                    success_count += 1
                else:
                    self.log_test("Grade 3 Spelling Variety", False, 
                                f"Only found {unique_words_count} unique words (expected ≥40)")
                    
                # Check for Grade 3 advanced content
                advanced_indicators = ["Wissenschaft", "Experiment", "Technologie", "Computer", "Universität"]
                found_advanced = [word for word in advanced_indicators if word in grade3_words]
                
                if len(found_advanced) >= 2:
                    self.log_test("Grade 3 Advanced Content Verification", True, 
                                f"Found advanced content indicators: {found_advanced}")
                    success_count += 1
                else:
                    self.log_test("Grade 3 Advanced Content Verification", False, 
                                f"Limited advanced content found: {found_advanced}")
            else:
                self.log_test("Grade 3 Spelling Challenges", False, 
                            f"Only created {challenges_created} challenges (expected ≥3)")
        except Exception as e:
            self.log_test("Grade 3 Spelling Content Expansion", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_german_word_types_content_expansion(self):
        """Test German word type problems with expanded content"""
        success_count = 0
        
        print("\n🔤 Testing German Word Types Content Expansion")
        print("Expected: 120+ word type examples per grade")
        
        try:
            # Configure settings for word types only
            settings = {
                "problem_count": 15,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "spelling": False,
                    "word_types": True,
                    "fill_blank": False,
                    "grammar": False,
                    "articles": False,
                    "sentence_order": False
                }
            }
            
            response = self.session.put(f"{BASE_URL}/german/settings", json=settings)
            if response.status_code == 200:
                # Test Grade 2 word types
                grade2_sentences = set()
                grade2_words = set()
                
                for i in range(4):  # Create 4 challenges
                    response = self.session.post(f"{BASE_URL}/german/challenge/2")
                    if response.status_code == 200:
                        challenge = response.json()
                        self.created_resources['challenges'].append(challenge["id"])
                        
                        problems = challenge.get("problems", [])
                        for problem in problems:
                            if problem.get("question_type") == "word_types":
                                problem_data = problem.get("problem_data", {})
                                sentence = problem_data.get("sentence", "")
                                target_word = problem_data.get("target_word", "")
                                
                                if sentence:
                                    grade2_sentences.add(sentence)
                                if target_word:
                                    grade2_words.add(target_word)
                
                unique_sentences = len(grade2_sentences)
                unique_words = len(grade2_words)
                
                if unique_sentences >= 20:  # Expect at least 20 unique sentences
                    self.log_test("Grade 2 Word Types Sentence Variety", True, 
                                f"Found {unique_sentences} unique sentences with {unique_words} target words")
                    success_count += 1
                else:
                    self.log_test("Grade 2 Word Types Sentence Variety", False, 
                                f"Only found {unique_sentences} unique sentences (expected ≥20)")
                
                # Test Grade 3 word types
                grade3_sentences = set()
                grade3_words = set()
                
                for i in range(4):  # Create 4 challenges
                    response = self.session.post(f"{BASE_URL}/german/challenge/3")
                    if response.status_code == 200:
                        challenge = response.json()
                        self.created_resources['challenges'].append(challenge["id"])
                        
                        problems = challenge.get("problems", [])
                        for problem in problems:
                            if problem.get("question_type") == "word_types":
                                problem_data = problem.get("problem_data", {})
                                sentence = problem_data.get("sentence", "")
                                target_word = problem_data.get("target_word", "")
                                
                                if sentence:
                                    grade3_sentences.add(sentence)
                                if target_word:
                                    grade3_words.add(target_word)
                
                unique_sentences_g3 = len(grade3_sentences)
                unique_words_g3 = len(grade3_words)
                
                if unique_sentences_g3 >= 15:  # Expect at least 15 unique sentences for Grade 3
                    self.log_test("Grade 3 Word Types Sentence Variety", True, 
                                f"Found {unique_sentences_g3} unique sentences with {unique_words_g3} target words")
                    success_count += 1
                else:
                    self.log_test("Grade 3 Word Types Sentence Variety", False, 
                                f"Only found {unique_sentences_g3} unique sentences (expected ≥15)")
                
                # Check for proper word type distribution
                word_types_found = set()
                response = self.session.post(f"{BASE_URL}/german/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    for problem in problems:
                        if problem.get("question_type") == "word_types":
                            correct_answer = problem.get("correct_answer", "")
                            if correct_answer:
                                word_types_found.add(correct_answer)
                
                expected_types = {"Nomen", "Verb", "Adjektiv"}
                if word_types_found.intersection(expected_types):
                    self.log_test("Word Types Distribution", True, 
                                f"Found proper word types: {word_types_found}")
                    success_count += 1
                else:
                    self.log_test("Word Types Distribution", False, 
                                f"No proper word types found: {word_types_found}")
            else:
                self.log_test("German Word Types Settings", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("German Word Types Content Expansion", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_german_fill_blank_content_expansion(self):
        """Test German fill-in-the-blank problems with expanded content"""
        success_count = 0
        
        print("\n📋 Testing German Fill-Blank Content Expansion")
        print("Expected: 150+ fill-blank examples per grade")
        
        try:
            # Configure settings for fill-blank only
            settings = {
                "problem_count": 20,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "spelling": False,
                    "word_types": False,
                    "fill_blank": True,
                    "grammar": False,
                    "articles": False,
                    "sentence_order": False
                }
            }
            
            response = self.session.put(f"{BASE_URL}/german/settings", json=settings)
            if response.status_code == 200:
                # Test Grade 2 fill-blank variety
                grade2_texts = set()
                grade2_answers = set()
                
                for i in range(5):  # Create 5 challenges
                    response = self.session.post(f"{BASE_URL}/german/challenge/2")
                    if response.status_code == 200:
                        challenge = response.json()
                        self.created_resources['challenges'].append(challenge["id"])
                        
                        problems = challenge.get("problems", [])
                        for problem in problems:
                            if problem.get("question_type") == "fill_blank":
                                question = problem.get("question", "")
                                correct_answer = problem.get("correct_answer", "")
                                problem_data = problem.get("problem_data", {})
                                original_text = problem_data.get("original_text", "")
                                
                                if original_text:
                                    grade2_texts.add(original_text)
                                if correct_answer:
                                    grade2_answers.add(correct_answer)
                
                unique_texts = len(grade2_texts)
                unique_answers = len(grade2_answers)
                
                if unique_texts >= 30:  # Expect at least 30 unique fill-blank texts
                    self.log_test("Grade 2 Fill-Blank Text Variety", True, 
                                f"Found {unique_texts} unique fill-blank texts with {unique_answers} answers")
                    success_count += 1
                else:
                    self.log_test("Grade 2 Fill-Blank Text Variety", False, 
                                f"Only found {unique_texts} unique texts (expected ≥30)")
                
                # Test Grade 3 fill-blank variety
                grade3_texts = set()
                grade3_answers = set()
                
                for i in range(5):  # Create 5 challenges
                    response = self.session.post(f"{BASE_URL}/german/challenge/3")
                    if response.status_code == 200:
                        challenge = response.json()
                        self.created_resources['challenges'].append(challenge["id"])
                        
                        problems = challenge.get("problems", [])
                        for problem in problems:
                            if problem.get("question_type") == "fill_blank":
                                question = problem.get("question", "")
                                correct_answer = problem.get("correct_answer", "")
                                problem_data = problem.get("problem_data", {})
                                original_text = problem_data.get("original_text", "")
                                
                                if original_text:
                                    grade3_texts.add(original_text)
                                if correct_answer:
                                    grade3_answers.add(correct_answer)
                
                unique_texts_g3 = len(grade3_texts)
                unique_answers_g3 = len(grade3_answers)
                
                if unique_texts_g3 >= 25:  # Expect at least 25 unique fill-blank texts for Grade 3
                    self.log_test("Grade 3 Fill-Blank Text Variety", True, 
                                f"Found {unique_texts_g3} unique fill-blank texts with {unique_answers_g3} answers")
                    success_count += 1
                else:
                    self.log_test("Grade 3 Fill-Blank Text Variety", False, 
                                f"Only found {unique_texts_g3} unique texts (expected ≥25)")
                
                # Check for proper difficulty progression
                sample_g2_texts = list(grade2_texts)[:5]
                sample_g3_texts = list(grade3_texts)[:5]
                
                # Grade 2 should have simpler sentences
                g2_simple = any(len(text.split()) <= 6 for text in sample_g2_texts)
                # Grade 3 should have more complex sentences
                g3_complex = any(len(text.split()) >= 6 for text in sample_g3_texts)
                
                if g2_simple and g3_complex:
                    self.log_test("Fill-Blank Difficulty Progression", True, 
                                "Grade 2 has simpler texts, Grade 3 has more complex texts")
                    success_count += 1
                else:
                    self.log_test("Fill-Blank Difficulty Progression", False, 
                                f"Difficulty progression unclear: G2 simple={g2_simple}, G3 complex={g3_complex}")
            else:
                self.log_test("German Fill-Blank Settings", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("German Fill-Blank Content Expansion", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_english_vocabulary_content_expansion(self):
        """Test English vocabulary problems with expanded content"""
        success_count = 0
        
        print("\n🇬🇧 Testing English Vocabulary Content Expansion")
        print("Expected: 200+ basic words, 200+ intermediate words")
        
        try:
            # Configure settings for vocabulary only
            settings = {
                "problem_count": 15,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "vocabulary_de_en": True,
                    "vocabulary_en_de": True,
                    "simple_sentences": False,
                    "basic_grammar": False,
                    "colors_numbers": False,
                    "animals_objects": False
                },
                "difficulty_settings": {
                    "vocabulary_level": "basic",
                    "include_articles": False,
                    "sentence_complexity": "simple"
                }
            }
            
            response = self.session.put(f"{BASE_URL}/english/settings", json=settings)
            if response.status_code == 200:
                # Test basic vocabulary variety
                english_words = set()
                german_words = set()
                categories = set()
                
                for i in range(6):  # Create 6 challenges
                    response = self.session.post(f"{BASE_URL}/english/challenge/2")
                    if response.status_code == 200:
                        challenge = response.json()
                        self.created_resources['challenges'].append(challenge["id"])
                        
                        problems = challenge.get("problems", [])
                        for problem in problems:
                            question_type = problem.get("question_type", "")
                            if question_type in ["vocabulary_de_en", "vocabulary_en_de"]:
                                question = problem.get("question", "")
                                correct_answer = problem.get("correct_answer", "")
                                problem_data = problem.get("problem_data", {})
                                
                                if question_type == "vocabulary_de_en":
                                    # German to English
                                    german_words.add(question.replace("Was ist ", "").replace(" auf Englisch?", ""))
                                    english_words.add(correct_answer)
                                elif question_type == "vocabulary_en_de":
                                    # English to German
                                    english_words.add(question.replace("Was ist ", "").replace(" auf Deutsch?", ""))
                                    german_words.add(correct_answer)
                                
                                # Extract category if available
                                category = problem_data.get("category", "")
                                if category:
                                    categories.add(category)
                
                unique_english = len(english_words)
                unique_german = len(german_words)
                unique_categories = len(categories)
                
                if unique_english >= 30:  # Expect at least 30 unique English words
                    self.log_test("English Vocabulary Variety", True, 
                                f"Found {unique_english} English words, {unique_german} German words")
                    success_count += 1
                else:
                    self.log_test("English Vocabulary Variety", False, 
                                f"Only found {unique_english} English words (expected ≥30)")
                
                # Check for proper categorization
                expected_categories = {"animals", "food", "colors", "household", "family", "nature"}
                found_categories = categories.intersection(expected_categories)
                
                if len(found_categories) >= 3:
                    self.log_test("English Vocabulary Categorization", True, 
                                f"Found proper categories: {found_categories}")
                    success_count += 1
                else:
                    self.log_test("English Vocabulary Categorization", False, 
                                f"Limited categories found: {found_categories}")
                
                # Test intermediate vocabulary
                settings["difficulty_settings"]["vocabulary_level"] = "intermediate"
                response = self.session.put(f"{BASE_URL}/english/settings", json=settings)
                if response.status_code == 200:
                    intermediate_words = set()
                    
                    for i in range(3):  # Create 3 intermediate challenges
                        response = self.session.post(f"{BASE_URL}/english/challenge/3")
                        if response.status_code == 200:
                            challenge = response.json()
                            self.created_resources['challenges'].append(challenge["id"])
                            
                            problems = challenge.get("problems", [])
                            for problem in problems:
                                question_type = problem.get("question_type", "")
                                if question_type in ["vocabulary_de_en", "vocabulary_en_de"]:
                                    correct_answer = problem.get("correct_answer", "")
                                    if correct_answer:
                                        intermediate_words.add(correct_answer)
                    
                    unique_intermediate = len(intermediate_words)
                    if unique_intermediate >= 15:  # Expect at least 15 intermediate words
                        self.log_test("English Intermediate Vocabulary", True, 
                                    f"Found {unique_intermediate} intermediate vocabulary words")
                        success_count += 1
                    else:
                        self.log_test("English Intermediate Vocabulary", False, 
                                    f"Only found {unique_intermediate} intermediate words (expected ≥15)")
            else:
                self.log_test("English Vocabulary Settings", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("English Vocabulary Content Expansion", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_english_sentence_translation_expansion(self):
        """Test English sentence translation with expanded content"""
        success_count = 0
        
        print("\n💬 Testing English Sentence Translation Expansion")
        print("Expected: 100+ basic sentences, 100+ advanced sentences")
        
        try:
            # Configure settings for sentence translation only
            settings = {
                "problem_count": 10,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "vocabulary_de_en": False,
                    "vocabulary_en_de": False,
                    "simple_sentences": True,
                    "basic_grammar": False,
                    "colors_numbers": False,
                    "animals_objects": False
                },
                "difficulty_settings": {
                    "vocabulary_level": "basic",
                    "include_articles": False,
                    "sentence_complexity": "simple"
                }
            }
            
            response = self.session.put(f"{BASE_URL}/english/settings", json=settings)
            if response.status_code == 200:
                # Test basic sentence variety
                basic_sentences = set()
                
                for i in range(4):  # Create 4 challenges
                    response = self.session.post(f"{BASE_URL}/english/challenge/2")
                    if response.status_code == 200:
                        challenge = response.json()
                        self.created_resources['challenges'].append(challenge["id"])
                        
                        problems = challenge.get("problems", [])
                        for problem in problems:
                            if problem.get("question_type") == "simple_sentences":
                                question = problem.get("question", "")
                                correct_answer = problem.get("correct_answer", "")
                                
                                if question and correct_answer:
                                    basic_sentences.add((question, correct_answer))
                
                unique_basic = len(basic_sentences)
                if unique_basic >= 15:  # Expect at least 15 unique sentence pairs
                    self.log_test("English Basic Sentences Variety", True, 
                                f"Found {unique_basic} unique basic sentence translations")
                    success_count += 1
                else:
                    self.log_test("English Basic Sentences Variety", False, 
                                f"Only found {unique_basic} unique sentences (expected ≥15)")
                
                # Test advanced sentence complexity
                settings["difficulty_settings"]["sentence_complexity"] = "medium"
                response = self.session.put(f"{BASE_URL}/english/settings", json=settings)
                if response.status_code == 200:
                    advanced_sentences = set()
                    
                    for i in range(4):  # Create 4 advanced challenges
                        response = self.session.post(f"{BASE_URL}/english/challenge/3")
                        if response.status_code == 200:
                            challenge = response.json()
                            self.created_resources['challenges'].append(challenge["id"])
                            
                            problems = challenge.get("problems", [])
                            for problem in problems:
                                if problem.get("question_type") == "simple_sentences":
                                    question = problem.get("question", "")
                                    correct_answer = problem.get("correct_answer", "")
                                    
                                    if question and correct_answer:
                                        advanced_sentences.add((question, correct_answer))
                    
                    unique_advanced = len(advanced_sentences)
                    if unique_advanced >= 10:  # Expect at least 10 unique advanced sentences
                        self.log_test("English Advanced Sentences Variety", True, 
                                    f"Found {unique_advanced} unique advanced sentence translations")
                        success_count += 1
                    else:
                        self.log_test("English Advanced Sentences Variety", False, 
                                    f"Only found {unique_advanced} unique sentences (expected ≥10)")
                    
                    # Check complexity difference
                    sample_basic = list(basic_sentences)[:3]
                    sample_advanced = list(advanced_sentences)[:3]
                    
                    basic_avg_length = sum(len(s[0].split()) + len(s[1].split()) for s in sample_basic) / (len(sample_basic) * 2) if sample_basic else 0
                    advanced_avg_length = sum(len(s[0].split()) + len(s[1].split()) for s in sample_advanced) / (len(sample_advanced) * 2) if sample_advanced else 0
                    
                    if advanced_avg_length > basic_avg_length:
                        self.log_test("English Sentence Complexity Progression", True, 
                                    f"Advanced sentences are more complex (avg {advanced_avg_length:.1f} vs {basic_avg_length:.1f} words)")
                        success_count += 1
                    else:
                        self.log_test("English Sentence Complexity Progression", False, 
                                    f"No clear complexity progression: advanced={advanced_avg_length:.1f}, basic={basic_avg_length:.1f}")
            else:
                self.log_test("English Sentence Settings", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("English Sentence Translation Expansion", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_content_import_fallback(self):
        """Test that content imports work correctly with fallback mechanisms"""
        success_count = 0
        
        print("\n🔄 Testing Content Import and Fallback Mechanisms")
        
        # Test German challenge creation (should work with or without imports)
        try:
            response = self.session.post(f"{BASE_URL}/german/challenge/2")
            if response.status_code == 200:
                challenge = response.json()
                problems = challenge.get("problems", [])
                
                if len(problems) > 0:
                    self.log_test("German Content Import/Fallback", True, 
                                f"German challenge created successfully with {len(problems)} problems")
                    success_count += 1
                    
                    # Check if problems have proper structure
                    first_problem = problems[0]
                    required_fields = ["question", "question_type", "correct_answer"]
                    if all(field in first_problem for field in required_fields):
                        self.log_test("German Problem Structure", True, 
                                    "German problems have proper structure")
                        success_count += 1
                    else:
                        self.log_test("German Problem Structure", False, 
                                    f"Missing fields in German problems: {required_fields}")
                else:
                    self.log_test("German Content Import/Fallback", False, 
                                "No problems generated in German challenge")
            else:
                self.log_test("German Content Import/Fallback", False, 
                            f"German challenge creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("German Content Import/Fallback", False, f"Exception: {str(e)}")
        
        # Test English challenge creation (should work with or without imports)
        try:
            response = self.session.post(f"{BASE_URL}/english/challenge/2")
            if response.status_code == 200:
                challenge = response.json()
                problems = challenge.get("problems", [])
                
                if len(problems) > 0:
                    self.log_test("English Content Import/Fallback", True, 
                                f"English challenge created successfully with {len(problems)} problems")
                    success_count += 1
                    
                    # Check if problems have proper structure
                    first_problem = problems[0]
                    required_fields = ["question", "question_type", "correct_answer"]
                    if all(field in first_problem for field in required_fields):
                        self.log_test("English Problem Structure", True, 
                                    "English problems have proper structure")
                        success_count += 1
                    else:
                        self.log_test("English Problem Structure", False, 
                                    f"Missing fields in English problems: {required_fields}")
                else:
                    self.log_test("English Content Import/Fallback", False, 
                                "No problems generated in English challenge")
            else:
                self.log_test("English Content Import/Fallback", False, 
                            f"English challenge creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("English Content Import/Fallback", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_content_quality_and_variety(self):
        """Test overall content quality and variety to prevent repetition"""
        success_count = 0
        
        print("\n🎯 Testing Content Quality and Variety (Anti-Repetition)")
        
        # Test German content variety across multiple challenges
        try:
            all_german_problems = []
            
            for grade in [2, 3]:
                for i in range(3):  # 3 challenges per grade
                    response = self.session.post(f"{BASE_URL}/german/challenge/{grade}")
                    if response.status_code == 200:
                        challenge = response.json()
                        problems = challenge.get("problems", [])
                        all_german_problems.extend(problems)
            
            if len(all_german_problems) >= 60:  # Expect at least 60 problems total
                # Check for variety in questions
                unique_questions = set()
                unique_answers = set()
                problem_types = set()
                
                for problem in all_german_problems:
                    question = problem.get("question", "")
                    answer = problem.get("correct_answer", "")
                    ptype = problem.get("question_type", "")
                    
                    if question:
                        unique_questions.add(question)
                    if answer:
                        unique_answers.add(answer)
                    if ptype:
                        problem_types.add(ptype)
                
                variety_ratio = len(unique_questions) / len(all_german_problems)
                
                if variety_ratio >= 0.7:  # At least 70% unique questions
                    self.log_test("German Content Variety", True, 
                                f"High variety: {len(unique_questions)} unique questions out of {len(all_german_problems)} ({variety_ratio:.1%})")
                    success_count += 1
                else:
                    self.log_test("German Content Variety", False, 
                                f"Low variety: {len(unique_questions)} unique questions out of {len(all_german_problems)} ({variety_ratio:.1%})")
                
                if len(problem_types) >= 2:
                    self.log_test("German Problem Type Diversity", True, 
                                f"Found diverse problem types: {problem_types}")
                    success_count += 1
                else:
                    self.log_test("German Problem Type Diversity", False, 
                                f"Limited problem types: {problem_types}")
            else:
                self.log_test("German Content Volume", False, 
                            f"Insufficient German problems generated: {len(all_german_problems)}")
        except Exception as e:
            self.log_test("German Content Quality", False, f"Exception: {str(e)}")
        
        # Test English content variety across multiple challenges
        try:
            all_english_problems = []
            
            for grade in [2, 3]:
                for i in range(3):  # 3 challenges per grade
                    response = self.session.post(f"{BASE_URL}/english/challenge/{grade}")
                    if response.status_code == 200:
                        challenge = response.json()
                        problems = challenge.get("problems", [])
                        all_english_problems.extend(problems)
            
            if len(all_english_problems) >= 45:  # Expect at least 45 problems total
                # Check for variety in questions
                unique_questions = set()
                unique_answers = set()
                problem_types = set()
                
                for problem in all_english_problems:
                    question = problem.get("question", "")
                    answer = problem.get("correct_answer", "")
                    ptype = problem.get("question_type", "")
                    
                    if question:
                        unique_questions.add(question)
                    if answer:
                        unique_answers.add(answer)
                    if ptype:
                        problem_types.add(ptype)
                
                variety_ratio = len(unique_questions) / len(all_english_problems)
                
                if variety_ratio >= 0.6:  # At least 60% unique questions
                    self.log_test("English Content Variety", True, 
                                f"Good variety: {len(unique_questions)} unique questions out of {len(all_english_problems)} ({variety_ratio:.1%})")
                    success_count += 1
                else:
                    self.log_test("English Content Variety", False, 
                                f"Low variety: {len(unique_questions)} unique questions out of {len(all_english_problems)} ({variety_ratio:.1%})")
                
                if len(problem_types) >= 2:
                    self.log_test("English Problem Type Diversity", True, 
                                f"Found diverse problem types: {problem_types}")
                    success_count += 1
                else:
                    self.log_test("English Problem Type Diversity", False, 
                                f"Limited problem types: {problem_types}")
            else:
                self.log_test("English Content Volume", False, 
                            f"Insufficient English problems generated: {len(all_english_problems)}")
        except Exception as e:
            self.log_test("English Content Quality", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def run_all_tests(self):
        """Run all content expansion tests"""
        print("🚀 Starting Content Expansion Testing for Weekly Star Tracker")
        print("=" * 80)
        
        test_methods = [
            self.test_german_spelling_content_expansion,
            self.test_german_word_types_content_expansion,
            self.test_german_fill_blank_content_expansion,
            self.test_english_vocabulary_content_expansion,
            self.test_english_sentence_translation_expansion,
            self.test_content_import_fallback,
            self.test_content_quality_and_variety
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test method {test_method.__name__} failed with exception: {str(e)}")
        
        print("\n" + "=" * 80)
        print(f"📊 CONTENT EXPANSION TEST SUMMARY")
        print(f"Passed: {passed_tests}/{total_tests} test categories")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        return passed_tests >= (total_tests * 0.7)  # 70% pass rate required

if __name__ == "__main__":
    tester = ContentExpansionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 CONTENT EXPANSION TESTING COMPLETED SUCCESSFULLY!")
        print("The newly expanded German and English content is working correctly.")
    else:
        print("\n⚠️ CONTENT EXPANSION TESTING COMPLETED WITH ISSUES")
        print("Some content expansion features may need attention.")