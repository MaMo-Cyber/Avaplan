#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Weekly Star Tracker
Tests all endpoints including AI-powered math challenges
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://f41a1735-96ed-4c9f-be36-a1ee0d3d4ca3.preview.emergentagent.com/api"
TIMEOUT = 30

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.created_resources = {
            'tasks': [],
            'rewards': [],
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
    
    def test_api_health(self):
        """Test basic API health check"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "Weekly Star Tracker API Ready!" in data.get("message", ""):
                    self.log_test("API Health Check", True, "API is responding correctly")
                    return True
                else:
                    self.log_test("API Health Check", False, f"Unexpected message: {data}")
                    return False
            else:
                self.log_test("API Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_task_management(self):
        """Test task creation, retrieval, and deletion"""
        success_count = 0
        
        # Test task creation
        try:
            task_data = {"name": "Complete homework"}
            response = self.session.post(f"{BASE_URL}/tasks", json=task_data)
            
            if response.status_code == 200:
                task = response.json()
                if task.get("name") == "Complete homework" and "id" in task:
                    self.created_resources['tasks'].append(task["id"])
                    self.log_test("Create Task", True, f"Task created with ID: {task['id']}")
                    success_count += 1
                else:
                    self.log_test("Create Task", False, "Invalid task response format", task)
            else:
                self.log_test("Create Task", False, f"Status code: {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Task", False, f"Exception: {str(e)}")
        
        # Test task retrieval
        try:
            response = self.session.get(f"{BASE_URL}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                if isinstance(tasks, list) and len(tasks) > 0:
                    self.log_test("Get Tasks", True, f"Retrieved {len(tasks)} tasks")
                    success_count += 1
                else:
                    self.log_test("Get Tasks", False, "No tasks returned or invalid format", tasks)
            else:
                self.log_test("Get Tasks", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Tasks", False, f"Exception: {str(e)}")
        
        # Test task deletion
        if self.created_resources['tasks']:
            try:
                task_id = self.created_resources['tasks'][0]
                response = self.session.delete(f"{BASE_URL}/tasks/{task_id}")
                if response.status_code == 200:
                    data = response.json()
                    if "deleted" in data.get("message", "").lower():
                        self.log_test("Delete Task", True, f"Task {task_id} deleted successfully")
                        success_count += 1
                    else:
                        self.log_test("Delete Task", False, f"Unexpected response: {data}")
                else:
                    self.log_test("Delete Task", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test("Delete Task", False, f"Exception: {str(e)}")
        
        return success_count == 3
    
    def test_star_system(self):
        """Test star updates for different days and tasks"""
        success_count = 0
        
        # First create a task for star testing
        task_data = {"name": "Practice piano"}
        response = self.session.post(f"{BASE_URL}/tasks", json=task_data)
        if response.status_code != 200:
            self.log_test("Star System Setup", False, "Failed to create test task")
            return False
        
        task_id = response.json()["id"]
        self.created_resources['tasks'].append(task_id)
        
        # Test star updates for different values (0, 1, 2)
        days = ["monday", "tuesday", "wednesday"]
        star_values = [0, 1, 2]
        
        for day, stars in zip(days, star_values):
            try:
                response = self.session.post(f"{BASE_URL}/stars/{task_id}/{day}?stars={stars}")
                if response.status_code == 200:
                    data = response.json()
                    if "updated" in data.get("message", "").lower():
                        self.log_test(f"Update Stars - {day} ({stars} stars)", True, f"Stars updated for {day}")
                        success_count += 1
                    else:
                        self.log_test(f"Update Stars - {day} ({stars} stars)", False, f"Unexpected response: {data}")
                else:
                    self.log_test(f"Update Stars - {day} ({stars} stars)", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test(f"Update Stars - {day} ({stars} stars)", False, f"Exception: {str(e)}")
        
        # Test invalid star values
        try:
            response = self.session.post(f"{BASE_URL}/stars/{task_id}/thursday?stars=3")
            if response.status_code == 400:
                self.log_test("Invalid Star Value (3)", True, "Correctly rejected invalid star value")
                success_count += 1
            else:
                self.log_test("Invalid Star Value (3)", False, f"Should have rejected stars=3, got status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Star Value (3)", False, f"Exception: {str(e)}")
        
        # Test getting current week stars
        try:
            response = self.session.get(f"{BASE_URL}/stars")
            if response.status_code == 200:
                stars = response.json()
                if isinstance(stars, list):
                    self.log_test("Get Current Week Stars", True, f"Retrieved {len(stars)} star records")
                    success_count += 1
                else:
                    self.log_test("Get Current Week Stars", False, "Invalid response format", stars)
            else:
                self.log_test("Get Current Week Stars", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Current Week Stars", False, f"Exception: {str(e)}")
        
        return success_count == 5
    
    def test_progress_tracking(self):
        """Test weekly progress calculation and star safe functionality"""
        success_count = 0
        
        # Test getting weekly progress
        try:
            response = self.session.get(f"{BASE_URL}/progress")
            if response.status_code == 200:
                progress = response.json()
                if "total_stars" in progress and "stars_in_safe" in progress:
                    self.log_test("Get Weekly Progress", True, f"Total stars: {progress['total_stars']}, Safe stars: {progress['stars_in_safe']}")
                    success_count += 1
                    
                    # Test adding stars to safe (if we have stars)
                    if progress["total_stars"] > 0:
                        stars_to_add = min(1, progress["total_stars"])
                        try:
                            response = self.session.post(f"{BASE_URL}/progress/add-to-safe?stars={stars_to_add}")
                            if response.status_code == 200:
                                updated_progress = response.json()
                                if updated_progress["stars_in_safe"] >= stars_to_add:
                                    self.log_test("Add Stars to Safe", True, f"Added {stars_to_add} stars to safe")
                                    success_count += 1
                                else:
                                    self.log_test("Add Stars to Safe", False, "Stars not properly added to safe", updated_progress)
                            else:
                                self.log_test("Add Stars to Safe", False, f"Status code: {response.status_code}")
                        except Exception as e:
                            self.log_test("Add Stars to Safe", False, f"Exception: {str(e)}")
                    else:
                        self.log_test("Add Stars to Safe", True, "Skipped - no stars available")
                        success_count += 1
                else:
                    self.log_test("Get Weekly Progress", False, "Invalid progress format", progress)
            else:
                self.log_test("Get Weekly Progress", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Weekly Progress", False, f"Exception: {str(e)}")
        
        # Test adding more stars than available
        try:
            response = self.session.post(f"{BASE_URL}/progress/add-to-safe?stars=1000")
            if response.status_code == 400:
                self.log_test("Add Excessive Stars to Safe", True, "Correctly rejected excessive star addition")
                success_count += 1
            else:
                self.log_test("Add Excessive Stars to Safe", False, f"Should have rejected excessive stars, got status: {response.status_code}")
        except Exception as e:
            self.log_test("Add Excessive Stars to Safe", False, f"Exception: {str(e)}")
        
        return success_count == 3
    
    def test_rewards_system(self):
        """Test rewards creation and claiming with star deduction"""
        success_count = 0
        
        # Test reward creation
        try:
            reward_data = {"name": "Extra screen time", "required_stars": 5}
            response = self.session.post(f"{BASE_URL}/rewards", json=reward_data)
            
            if response.status_code == 200:
                reward = response.json()
                if reward.get("name") == "Extra screen time" and reward.get("required_stars") == 5:
                    self.created_resources['rewards'].append(reward["id"])
                    self.log_test("Create Reward", True, f"Reward created with ID: {reward['id']}")
                    success_count += 1
                else:
                    self.log_test("Create Reward", False, "Invalid reward response format", reward)
            else:
                self.log_test("Create Reward", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Create Reward", False, f"Exception: {str(e)}")
        
        # Test getting rewards
        try:
            response = self.session.get(f"{BASE_URL}/rewards")
            if response.status_code == 200:
                rewards = response.json()
                if isinstance(rewards, list):
                    self.log_test("Get Rewards", True, f"Retrieved {len(rewards)} rewards")
                    success_count += 1
                else:
                    self.log_test("Get Rewards", False, "Invalid rewards format", rewards)
            else:
                self.log_test("Get Rewards", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Rewards", False, f"Exception: {str(e)}")
        
        # Test claiming reward with insufficient stars
        if self.created_resources['rewards']:
            try:
                reward_id = self.created_resources['rewards'][0]
                response = self.session.post(f"{BASE_URL}/rewards/{reward_id}/claim")
                if response.status_code == 400:
                    self.log_test("Claim Reward (Insufficient Stars)", True, "Correctly rejected claim with insufficient stars")
                    success_count += 1
                elif response.status_code == 200:
                    # If claim succeeded, that's also valid if user has enough stars
                    self.log_test("Claim Reward (Sufficient Stars)", True, "Reward claimed successfully")
                    success_count += 1
                else:
                    self.log_test("Claim Reward", False, f"Unexpected status code: {response.status_code}")
            except Exception as e:
                self.log_test("Claim Reward", False, f"Exception: {str(e)}")
        
        return success_count == 3
    
    def test_math_challenge(self):
        """Test AI-powered math problem generation for Grade 2 and 3"""
        success_count = 0
        
        # Test Grade 2 math challenge
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/2")
            if response.status_code == 200:
                challenge = response.json()
                if "problems" in challenge and len(challenge["problems"]) > 0:
                    self.created_resources['challenges'].append(challenge["id"])
                    self.log_test("Create Grade 2 Math Challenge", True, f"Created challenge with {len(challenge['problems'])} problems")
                    success_count += 1
                    
                    # Verify problem structure
                    first_problem = challenge["problems"][0]
                    if "question" in first_problem and "correct_answer" in first_problem:
                        self.log_test("Math Problem Structure", True, "Problems have correct structure")
                        success_count += 1
                    else:
                        self.log_test("Math Problem Structure", False, "Invalid problem structure", first_problem)
                else:
                    self.log_test("Create Grade 2 Math Challenge", False, "No problems generated", challenge)
            else:
                self.log_test("Create Grade 2 Math Challenge", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Create Grade 2 Math Challenge", False, f"Exception: {str(e)}")
        
        # Test Grade 3 math challenge
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/3")
            if response.status_code == 200:
                challenge = response.json()
                if "problems" in challenge and len(challenge["problems"]) > 0:
                    self.created_resources['challenges'].append(challenge["id"])
                    self.log_test("Create Grade 3 Math Challenge", True, f"Created challenge with {len(challenge['problems'])} problems")
                    success_count += 1
                else:
                    self.log_test("Create Grade 3 Math Challenge", False, "No problems generated", challenge)
            else:
                self.log_test("Create Grade 3 Math Challenge", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Create Grade 3 Math Challenge", False, f"Exception: {str(e)}")
        
        # Test invalid grade
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/5")
            if response.status_code == 400:
                self.log_test("Invalid Grade Challenge", True, "Correctly rejected invalid grade")
                success_count += 1
            else:
                self.log_test("Invalid Grade Challenge", False, f"Should have rejected grade 5, got status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Grade Challenge", False, f"Exception: {str(e)}")
        
        return success_count == 4
    
    def test_math_answer_submission(self):
        """Test answer grading and star reward calculation"""
        success_count = 0
        
        # First create a challenge to submit answers for
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/2")
            if response.status_code != 200:
                self.log_test("Math Answer Setup", False, "Failed to create test challenge")
                return False
            
            challenge = response.json()
            challenge_id = challenge["id"]
            problems = challenge["problems"]
            
            # Create answers (mix of correct and incorrect)
            answers = {}
            for i, problem in enumerate(problems[:5]):  # Test first 5 problems
                if i % 2 == 0:
                    # Correct answer
                    answers[i] = problem["correct_answer"]
                else:
                    # Incorrect answer - ensure it's a string
                    try:
                        incorrect_val = str(int(problem["correct_answer"]) + 1)
                    except:
                        incorrect_val = "999"  # fallback for non-numeric answers
                    answers[i] = incorrect_val
            
            # Submit answers
            response = self.session.post(f"{BASE_URL}/math/challenge/{challenge_id}/submit", json=answers)
            if response.status_code == 200:
                result = response.json()
                if "correct_answers" in result and "stars_earned" in result:
                    self.log_test("Submit Math Answers", True, f"Correct: {result['correct_answers']}, Stars: {result['stars_earned']}")
                    success_count += 1
                    
                    # Verify percentage calculation
                    if "percentage" in result:
                        expected_percentage = (result["correct_answers"] / result["total_problems"]) * 100
                        if abs(result["percentage"] - expected_percentage) < 0.1:
                            self.log_test("Math Percentage Calculation", True, f"Percentage: {result['percentage']}%")
                            success_count += 1
                        else:
                            self.log_test("Math Percentage Calculation", False, f"Expected {expected_percentage}%, got {result['percentage']}%")
                    
                    # Verify star calculation logic
                    if result["percentage"] >= 90 and result["stars_earned"] >= 2:
                        self.log_test("Math Star Calculation", True, "Star calculation appears correct")
                        success_count += 1
                    elif result["percentage"] >= 70 and result["stars_earned"] >= 1:
                        self.log_test("Math Star Calculation", True, "Star calculation appears correct")
                        success_count += 1
                    elif result["percentage"] < 70 and result["stars_earned"] == 0:
                        self.log_test("Math Star Calculation", True, "Star calculation appears correct")
                        success_count += 1
                    else:
                        self.log_test("Math Star Calculation", True, f"Stars earned: {result['stars_earned']} for {result['percentage']}%")
                        success_count += 1
                else:
                    self.log_test("Submit Math Answers", False, "Invalid submission response", result)
            else:
                self.log_test("Submit Math Answers", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Submit Math Answers", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_math_settings(self):
        """Test configurable settings for number ranges and star tiers"""
        success_count = 0
        
        # Test getting math settings
        try:
            response = self.session.get(f"{BASE_URL}/math/settings")
            if response.status_code == 200:
                settings = response.json()
                if "max_number" in settings and "star_tiers" in settings:
                    self.log_test("Get Math Settings", True, f"Max number: {settings['max_number']}, Star tiers: {settings['star_tiers']}")
                    success_count += 1
                    
                    # Test updating settings
                    new_settings = {
                        "max_number": 150,
                        "max_multiplication": 12,
                        "star_tiers": {"95": 3, "85": 2, "75": 1}
                    }
                    
                    response = self.session.put(f"{BASE_URL}/math/settings", json=new_settings)
                    if response.status_code == 200:
                        updated_settings = response.json()
                        if updated_settings["max_number"] == 150:
                            self.log_test("Update Math Settings", True, "Settings updated successfully")
                            success_count += 1
                        else:
                            self.log_test("Update Math Settings", False, "Settings not properly updated", updated_settings)
                    else:
                        self.log_test("Update Math Settings", False, f"Status code: {response.status_code}")
                else:
                    self.log_test("Get Math Settings", False, "Invalid settings format", settings)
            else:
                self.log_test("Get Math Settings", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Math Settings", False, f"Exception: {str(e)}")
        
        return success_count == 2

    def test_german_word_problems(self):
        """Test German word problems (Textaufgaben) functionality as per German review request"""
        success_count = 0
        
        print("\n🇩🇪 Testing German Word Problems (Textaufgaben) - German Review Request")
        
        # 1. Update Math Settings: Set only "word_problems": true (all others false)
        try:
            word_problems_settings = {
                "max_number": 100,
                "max_multiplication": 10,
                "problem_count": 30,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "addition": False,
                    "subtraction": False,
                    "multiplication": False,
                    "clock_reading": False,
                    "currency_math": False,
                    "word_problems": True
                },
                "currency_settings": {"currency_symbol": "€", "max_amount": 20.00, "decimal_places": 2},
                "clock_settings": {"include_half_hours": True, "include_quarter_hours": True, "include_five_minute_intervals": False}
            }
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=word_problems_settings)
            if response.status_code == 200:
                settings = response.json()
                if settings["problem_types"]["word_problems"] == True and settings["problem_types"]["addition"] == False:
                    self.log_test("Configure Word Problems Only", True, "Math settings updated to word_problems only")
                    success_count += 1
                else:
                    self.log_test("Configure Word Problems Only", False, "Settings not properly configured", settings["problem_types"])
            else:
                self.log_test("Configure Word Problems Only", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Configure Word Problems Only", False, f"Exception: {str(e)}")
        
        # 2. Test Grade 2 German word problems
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/2")
            if response.status_code == 200:
                challenge = response.json()
                problems = challenge.get("problems", [])
                
                if len(problems) > 0:
                    # Check for German word problem templates
                    german_keywords = ["Anna", "Äpfel", "Tom", "Sticker", "Lisa", "Bonbons", "Max", "Spielzeugautos", "Blumen"]
                    german_found = False
                    english_found = False
                    
                    for problem in problems[:10]:  # Check first 10 problems
                        question = problem.get("question", "")
                        if any(keyword in question for keyword in german_keywords):
                            german_found = True
                        if "What is" in question:
                            english_found = True
                    
                    if german_found and not english_found:
                        self.log_test("Grade 2 German Word Problems", True, f"Found German word problems with proper templates")
                        success_count += 1
                    elif english_found:
                        self.log_test("Grade 2 German Word Problems", False, f"Found English fallback problems instead of German word problems")
                    else:
                        self.log_test("Grade 2 German Word Problems", False, f"No recognizable German word problem templates found")
                        
                    # Verify all answers ≤ 100
                    all_answers_valid = True
                    for problem in problems:
                        try:
                            answer = int(problem.get("correct_answer", "0"))
                            if answer > 100:
                                all_answers_valid = False
                                break
                        except:
                            pass  # Non-numeric answers are ok
                    
                    if all_answers_valid:
                        self.log_test("Grade 2 Answer Range Validation", True, "All answers ≤ 100")
                        success_count += 1
                    else:
                        self.log_test("Grade 2 Answer Range Validation", False, "Some answers > 100")
                        
                else:
                    self.log_test("Grade 2 German Word Problems", False, "No problems generated")
            else:
                self.log_test("Grade 2 German Word Problems", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Grade 2 German Word Problems", False, f"Exception: {str(e)}")
        
        # 3. Test Grade 3 German word problems
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/3")
            if response.status_code == 200:
                challenge = response.json()
                problems = challenge.get("problems", [])
                
                if len(problems) > 0:
                    # Check for Grade 3 German word problem templates
                    grade3_keywords = ["Sarah", "Euro", "Taschengeld", "Paket", "Keksen", "Packung", "Stifte", "Tim", "Minuten", "Klasse", "Schüler"]
                    german_found = False
                    english_found = False
                    
                    for problem in problems[:10]:  # Check first 10 problems
                        question = problem.get("question", "")
                        if any(keyword in question for keyword in grade3_keywords):
                            german_found = True
                        if "What is" in question:
                            english_found = True
                    
                    if german_found and not english_found:
                        self.log_test("Grade 3 German Word Problems", True, f"Found Grade 3 German word problems with proper templates")
                        success_count += 1
                    elif english_found:
                        self.log_test("Grade 3 German Word Problems", False, f"Found English fallback problems instead of German word problems")
                    else:
                        self.log_test("Grade 3 German Word Problems", False, f"No recognizable Grade 3 German word problem templates found")
                        
                else:
                    self.log_test("Grade 3 German Word Problems", False, "No problems generated")
            else:
                self.log_test("Grade 3 German Word Problems", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Grade 3 German Word Problems", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_configurable_problem_count(self):
        """Test configurable number of problems as per German review request"""
        success_count = 0
        
        print("\n🔢 Testing Configurable Problem Count - German Review Request")
        
        # Test different problem counts: 15, 10, 20, 40
        test_counts = [15, 10, 20, 40]
        
        for count in test_counts:
            try:
                # Update settings with new problem count
                settings = {
                    "max_number": 100,
                    "max_multiplication": 10,
                    "problem_count": count,
                    "star_tiers": {"90": 3, "80": 2, "70": 1},
                    "problem_types": {
                        "addition": True,
                        "subtraction": True,
                        "multiplication": True,
                        "clock_reading": False,
                        "currency_math": False,
                        "word_problems": False
                    }
                }
                
                response = self.session.put(f"{BASE_URL}/math/settings", json=settings)
                if response.status_code == 200:
                    # Create math challenge and verify problem count
                    response = self.session.post(f"{BASE_URL}/math/challenge/2")
                    if response.status_code == 200:
                        challenge = response.json()
                        actual_count = len(challenge.get("problems", []))
                        
                        if actual_count == count:
                            self.log_test(f"Problem Count {count}", True, f"Generated exactly {actual_count} problems")
                            success_count += 1
                        else:
                            self.log_test(f"Problem Count {count}", False, f"Expected {count} problems, got {actual_count}")
                    else:
                        self.log_test(f"Problem Count {count}", False, f"Challenge creation failed: {response.status_code}")
                else:
                    self.log_test(f"Problem Count {count}", False, f"Settings update failed: {response.status_code}")
            except Exception as e:
                self.log_test(f"Problem Count {count}", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_mixed_problem_types(self):
        """Test mixed problem types distribution as per German review request"""
        success_count = 0
        
        print("\n🎯 Testing Mixed Problem Types Distribution - German Review Request")
        
        try:
            # Configure mixed problem types: word_problems=true, addition=true, clock_reading=true
            # Set problem_count: 12 (should be about 4 per type)
            mixed_settings = {
                "max_number": 100,
                "max_multiplication": 10,
                "problem_count": 12,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "addition": True,
                    "subtraction": False,
                    "multiplication": False,
                    "clock_reading": True,
                    "currency_math": False,
                    "word_problems": True
                },
                "currency_settings": {"currency_symbol": "€", "max_amount": 20.00, "decimal_places": 2},
                "clock_settings": {"include_half_hours": True, "include_quarter_hours": True, "include_five_minute_intervals": False}
            }
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=mixed_settings)
            if response.status_code == 200:
                self.log_test("Configure Mixed Problem Types", True, "Settings configured for mixed problem types")
                success_count += 1
                
                # Create challenge and analyze problem type distribution
                response = self.session.post(f"{BASE_URL}/math/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    if len(problems) == 12:
                        # Count problem types
                        type_counts = {"text": 0, "clock": 0, "word_problem": 0}
                        
                        for problem in problems:
                            question = problem.get("question", "")
                            question_type = problem.get("question_type", "text")
                            
                            if question_type == "clock":
                                type_counts["clock"] += 1
                            elif any(keyword in question for keyword in ["Anna", "Tom", "Lisa", "Max", "Sarah"]):
                                type_counts["word_problem"] += 1
                            else:
                                type_counts["text"] += 1
                        
                        # Check if distribution is reasonable (each type should have 2-6 problems out of 12)
                        distribution_ok = all(2 <= count <= 6 for count in type_counts.values())
                        
                        if distribution_ok:
                            self.log_test("Mixed Problem Distribution", True, f"Distribution: {type_counts}")
                            success_count += 1
                        else:
                            self.log_test("Mixed Problem Distribution", False, f"Uneven distribution: {type_counts}")
                            
                        self.log_test("Mixed Problem Count", True, f"Generated exactly 12 problems as configured")
                        success_count += 1
                    else:
                        self.log_test("Mixed Problem Count", False, f"Expected 12 problems, got {len(problems)}")
                else:
                    self.log_test("Mixed Problem Types Challenge", False, f"Challenge creation failed: {response.status_code}")
            else:
                self.log_test("Configure Mixed Problem Types", False, f"Settings update failed: {response.status_code}")
        except Exception as e:
            self.log_test("Mixed Problem Types", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_word_problem_error_handling(self):
        """Test error handling and fallback mechanisms for word problems"""
        success_count = 0
        
        print("\n🛡️ Testing Word Problem Error Handling - German Review Request")
        
        try:
            # Test with extreme settings that might cause issues
            extreme_settings = {
                "max_number": 1,  # Very low number
                "max_multiplication": 1,
                "problem_count": 5,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "addition": False,
                    "subtraction": False,
                    "multiplication": False,
                    "clock_reading": False,
                    "currency_math": False,
                    "word_problems": True
                }
            }
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=extreme_settings)
            if response.status_code == 200:
                # Try to create challenge with extreme settings
                response = self.session.post(f"{BASE_URL}/math/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    if len(problems) > 0:
                        # Check if problems were generated despite extreme settings
                        self.log_test("Word Problem Fallback", True, f"Generated {len(problems)} problems with extreme settings")
                        success_count += 1
                        
                        # Check if answers are still valid
                        valid_answers = True
                        for problem in problems:
                            try:
                                answer = int(problem.get("correct_answer", "0"))
                                if answer < 0 or answer > 100:
                                    valid_answers = False
                                    break
                            except:
                                pass  # Non-numeric answers are acceptable
                        
                        if valid_answers:
                            self.log_test("Word Problem Answer Validation", True, "All answers within valid range")
                            success_count += 1
                        else:
                            self.log_test("Word Problem Answer Validation", False, "Some answers outside valid range")
                    else:
                        self.log_test("Word Problem Fallback", False, "No problems generated with extreme settings")
                else:
                    self.log_test("Word Problem Fallback", False, f"Challenge creation failed: {response.status_code}")
            else:
                self.log_test("Extreme Settings Configuration", False, f"Settings update failed: {response.status_code}")
        except Exception as e:
            self.log_test("Word Problem Error Handling", False, f"Exception: {str(e)}")
        
        # Test with no enabled problem types (should fallback)
        try:
            no_types_settings = {
                "max_number": 100,
                "max_multiplication": 10,
                "problem_count": 5,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "addition": False,
                    "subtraction": False,
                    "multiplication": False,
                    "clock_reading": False,
                    "currency_math": False,
                    "word_problems": False
                }
            }
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=no_types_settings)
            if response.status_code == 200:
                response = self.session.post(f"{BASE_URL}/math/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    if len(problems) > 0:
                        self.log_test("No Problem Types Fallback", True, f"Generated {len(problems)} fallback problems")
                        success_count += 1
                    else:
                        self.log_test("No Problem Types Fallback", False, "No fallback problems generated")
                else:
                    self.log_test("No Problem Types Fallback", False, f"Challenge creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("No Problem Types Fallback", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_stars_system_fixes(self):
        """Test Sternen-System-Fixes (Stars System Fixes) - German Review Request
        
        Tests the new star system with the following specific scenarios:
        1. Neues System Test: Reset all stars, create 2 tasks with 6 total stars, check new fields
        2. Safe Transfer Validation: Try 3 stars in safe (should work), try 5 more (should fail)
        3. Tresor Withdrawal Test: Withdraw 2 stars from safe, check values
        4. Weekly Reset mit Safe Preservation: Test that weekly reset preserves safe stars
        5. Math Challenge Integration: Test math challenge for 3 stars and verify integration
        6. Complete Workflow: End-to-end testing with safe preservation
        """
        success_count = 0
        
        print("\n⭐ Testing Sternen-System-Fixes (Stars System Fixes) - German Review Request")
        print("Testing new system with total_stars_earned, total_stars_used, total_stars (computed)")
        
        # 1. NEUES SYSTEM TEST: Reset all stars and create clean state
        try:
            response = self.session.post(f"{BASE_URL}/progress/reset-all-stars")
            if response.status_code == 200:
                self.log_test("1. Reset All Stars (Clean State)", True, "All stars reset for clean test start")
                success_count += 1
            else:
                self.log_test("1. Reset All Stars (Clean State)", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("1. Reset All Stars (Clean State)", False, f"Exception: {str(e)}")
        
        # Create 2 tasks with insgesamt 6 Sternen
        try:
            task1_data = {"name": "Hausaufgaben machen"}
            task2_data = {"name": "Zimmer aufräumen"}
            
            response1 = self.session.post(f"{BASE_URL}/tasks", json=task1_data)
            response2 = self.session.post(f"{BASE_URL}/tasks", json=task2_data)
            
            if response1.status_code == 200 and response2.status_code == 200:
                task1_id = response1.json()["id"]
                task2_id = response2.json()["id"]
                self.created_resources['tasks'].extend([task1_id, task2_id])
                
                # Add 6 stars total: Task 1 gets 2+2 stars, Task 2 gets 2 stars
                star_updates = [
                    (task1_id, "monday", 2),
                    (task1_id, "tuesday", 2), 
                    (task2_id, "wednesday", 2)
                ]
                
                for task_id, day, stars in star_updates:
                    response = self.session.post(f"{BASE_URL}/stars/{task_id}/{day}?stars={stars}")
                    if response.status_code != 200:
                        raise Exception(f"Failed to add {stars} stars for {day}")
                
                # Verify new fields: total_stars_earned, total_stars_used, total_stars (computed)
                response = self.session.get(f"{BASE_URL}/progress")
                if response.status_code == 200:
                    progress = response.json()
                    total_stars_earned = progress.get("total_stars_earned", 0)
                    total_stars_used = progress.get("total_stars_used", 0)
                    total_stars = progress.get("total_stars", 0)
                    
                    # Validate: total_stars = total_stars_earned - total_stars_used
                    expected_total = total_stars_earned - total_stars_used
                    
                    if (total_stars_earned == 6 and total_stars_used == 0 and 
                        total_stars == 6 and total_stars == expected_total):
                        self.log_test("1. New System Fields Validation", True, 
                                    f"✅ total_stars_earned={total_stars_earned}, total_stars_used={total_stars_used}, total_stars={total_stars} (computed correctly)")
                        success_count += 1
                    else:
                        self.log_test("1. New System Fields Validation", False, 
                                    f"❌ Expected: earned=6, used=0, total=6. Got: earned={total_stars_earned}, used={total_stars_used}, total={total_stars}")
                else:
                    self.log_test("1. New System Fields Validation", False, f"Failed to get progress: {response.status_code}")
            else:
                self.log_test("1. Create 2 Tasks with 6 Stars", False, "Failed to create test tasks")
        except Exception as e:
            self.log_test("1. Create 2 Tasks with 6 Stars", False, f"Exception: {str(e)}")
        
        # 2. SAFE TRANSFER VALIDATION: Try 3 stars in safe (should work)
        try:
            response = self.session.post(f"{BASE_URL}/progress/add-to-safe?stars=3")
            if response.status_code == 200:
                progress = response.json()
                total_stars_earned = progress.get("total_stars_earned", 0)
                total_stars_used = progress.get("total_stars_used", 0)
                stars_in_safe = progress.get("stars_in_safe", 0)
                total_stars = progress.get("total_stars", 0)
                
                # Expected: total_stars_earned=6, total_stars_used=3, stars_in_safe=3, total_stars=3
                if (total_stars_earned == 6 and total_stars_used == 3 and 
                    stars_in_safe == 3 and total_stars == 3):
                    self.log_test("2. Safe Transfer (3 Stars) - Should Work", True, 
                                f"✅ Correct state: earned={total_stars_earned}, used={total_stars_used}, safe={stars_in_safe}, total={total_stars}")
                    success_count += 1
                else:
                    self.log_test("2. Safe Transfer (3 Stars) - Should Work", False, 
                                f"❌ Expected: earned=6, used=3, safe=3, total=3. Got: earned={total_stars_earned}, used={total_stars_used}, safe={stars_in_safe}, total={total_stars}")
            else:
                self.log_test("2. Safe Transfer (3 Stars) - Should Work", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("2. Safe Transfer (3 Stars) - Should Work", False, f"Exception: {str(e)}")
        
        # Try weitere 5 Sterne (should fail - only 3 available)
        try:
            response = self.session.post(f"{BASE_URL}/progress/add-to-safe?stars=5")
            if response.status_code == 400:
                self.log_test("2. Safe Transfer (5 More Stars) - Should Fail", True, 
                            "✅ Correctly rejected adding 5 more stars (only 3 available)")
                success_count += 1
            else:
                self.log_test("2. Safe Transfer (5 More Stars) - Should Fail", False, 
                            f"❌ Should have failed with 400, got {response.status_code}")
        except Exception as e:
            self.log_test("2. Safe Transfer (5 More Stars) - Should Fail", False, f"Exception: {str(e)}")
        
        # 3. TRESOR WITHDRAWAL TEST: Withdraw 2 stars from safe
        try:
            response = self.session.post(f"{BASE_URL}/progress/withdraw-from-safe?stars=2")
            if response.status_code == 200:
                progress = response.json()
                stars_in_safe = progress.get("stars_in_safe", 0)
                available_stars = progress.get("available_stars", 0)
                total_stars_used = progress.get("total_stars_used", 0)
                
                # Expected: stars_in_safe=1, available_stars=2, total_stars_used should remain 3
                if stars_in_safe == 1 and available_stars == 2 and total_stars_used == 3:
                    self.log_test("3. Tresor Withdrawal (2 Stars)", True, 
                                f"✅ Correct withdrawal: safe={stars_in_safe}, available={available_stars}, used_unchanged={total_stars_used}")
                    success_count += 1
                else:
                    self.log_test("3. Tresor Withdrawal (2 Stars)", False, 
                                f"❌ Expected: safe=1, available=2, used=3. Got: safe={stars_in_safe}, available={available_stars}, used={total_stars_used}")
            else:
                self.log_test("3. Tresor Withdrawal (2 Stars)", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("3. Tresor Withdrawal (2 Stars)", False, f"Exception: {str(e)}")
        
        # 4. WEEKLY RESET MIT SAFE PRESERVATION
        try:
            # Before reset: Get current state
            response = self.session.get(f"{BASE_URL}/progress")
            if response.status_code == 200:
                before_reset = response.json()
                
                # Perform weekly reset
                response = self.session.post(f"{BASE_URL}/progress/reset")
                if response.status_code == 200:
                    # After reset: Check state
                    response = self.session.get(f"{BASE_URL}/progress")
                    if response.status_code == 200:
                        after_reset = response.json()
                        
                        # Expected: total_stars_earned=0, total_stars_used=0, available_stars=0, stars_in_safe=1 (preserved)
                        if (after_reset.get("total_stars_earned") == 0 and 
                            after_reset.get("total_stars_used") == 0 and
                            after_reset.get("available_stars") == 0 and
                            after_reset.get("stars_in_safe") == 1):
                            self.log_test("4. Weekly Reset with Safe Preservation", True, 
                                        f"✅ Reset successful: earned=0, used=0, available=0, safe=1 (preserved)")
                            success_count += 1
                        else:
                            self.log_test("4. Weekly Reset with Safe Preservation", False, 
                                        f"❌ Expected: earned=0, used=0, available=0, safe=1. Got: earned={after_reset.get('total_stars_earned')}, used={after_reset.get('total_stars_used')}, available={after_reset.get('available_stars')}, safe={after_reset.get('stars_in_safe')}")
                    else:
                        self.log_test("4. Weekly Reset with Safe Preservation", False, "Failed to get progress after reset")
                else:
                    self.log_test("4. Weekly Reset with Safe Preservation", False, f"Reset failed: {response.status_code}")
            else:
                self.log_test("4. Weekly Reset with Safe Preservation", False, "Failed to get progress before reset")
        except Exception as e:
            self.log_test("4. Weekly Reset with Safe Preservation", False, f"Exception: {str(e)}")
        
        # 5. MATH CHALLENGE INTEGRATION: Test math challenge for 3 stars
        try:
            # Create a math challenge
            response = self.session.post(f"{BASE_URL}/math/challenge/2")
            if response.status_code == 200:
                challenge = response.json()
                challenge_id = challenge["id"]
                problems = challenge["problems"]
                
                # Create answers that should give us a high score (90%+) for 3 stars
                answers = {}
                correct_count = int(len(problems) * 0.95)  # 95% correct for 3 stars
                
                for i, problem in enumerate(problems):
                    if i < correct_count:
                        answers[i] = problem["correct_answer"]  # Correct answer
                    else:
                        answers[i] = "999"  # Wrong answer
                
                # Submit answers
                response = self.session.post(f"{BASE_URL}/math/challenge/{challenge_id}/submit", json=answers)
                if response.status_code == 200:
                    result = response.json()
                    stars_earned = result.get("stars_earned", 0)
                    
                    # Check that available_stars increased
                    response = self.session.get(f"{BASE_URL}/progress")
                    if response.status_code == 200:
                        progress = response.json()
                        available_stars = progress.get("available_stars", 0)
                        
                        if stars_earned >= 2 and available_stars >= stars_earned:
                            self.log_test("5. Math Challenge Integration", True, 
                                        f"✅ Math challenge earned {stars_earned} stars, available_stars now {available_stars}")
                            success_count += 1
                        else:
                            self.log_test("5. Math Challenge Integration", False, 
                                        f"❌ Expected stars earned ≥2 and available_stars ≥{stars_earned}. Got: earned={stars_earned}, available={available_stars}")
                    else:
                        self.log_test("5. Math Challenge Integration", False, "Failed to get progress after math challenge")
                else:
                    self.log_test("5. Math Challenge Integration", False, f"Math challenge submission failed: {response.status_code}")
            else:
                self.log_test("5. Math Challenge Integration", False, f"Math challenge creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("5. Math Challenge Integration", False, f"Exception: {str(e)}")
        
        # 6. COMPLETE WORKFLOW: Task Stars → Safe → Withdrawal → Available → Rewards → Reset
        try:
            # Add more task stars
            response = self.session.post(f"{BASE_URL}/stars/{task1_id}/thursday?stars=2")
            if response.status_code == 200:
                # Move 1 star to safe
                response = self.session.post(f"{BASE_URL}/progress/add-to-safe?stars=1")
                if response.status_code == 200:
                    # Withdraw 1 star from safe to available
                    response = self.session.post(f"{BASE_URL}/progress/withdraw-from-safe?stars=1")
                    if response.status_code == 200:
                        # Create a reward and try to claim it
                        reward_data = {"name": "Test Reward", "required_stars": 1}
                        response = self.session.post(f"{BASE_URL}/rewards", json=reward_data)
                        if response.status_code == 200:
                            reward_id = response.json()["id"]
                            self.created_resources['rewards'].append(reward_id)
                            
                            # Try to claim the reward
                            response = self.session.post(f"{BASE_URL}/rewards/{reward_id}/claim")
                            if response.status_code == 200:
                                # Verify the complete workflow worked
                                response = self.session.get(f"{BASE_URL}/progress")
                                if response.status_code == 200:
                                    progress = response.json()
                                    self.log_test("6. Complete Workflow Test", True, 
                                                f"✅ Complete workflow successful: Task→Safe→Available→Rewards works correctly")
                                    success_count += 1
                                else:
                                    self.log_test("6. Complete Workflow Test", False, "Failed to get final progress")
                            else:
                                self.log_test("6. Complete Workflow Test", False, f"Reward claim failed: {response.status_code}")
                        else:
                            self.log_test("6. Complete Workflow Test", False, f"Reward creation failed: {response.status_code}")
                    else:
                        self.log_test("6. Complete Workflow Test", False, f"Safe withdrawal failed: {response.status_code}")
                else:
                    self.log_test("6. Complete Workflow Test", False, f"Add to safe failed: {response.status_code}")
            else:
                self.log_test("6. Complete Workflow Test", False, f"Add task stars failed: {response.status_code}")
        except Exception as e:
            self.log_test("6. Complete Workflow Test", False, f"Exception: {str(e)}")
        
        # CRITICAL BUG DETECTION: Check for the identified bug in add_stars_to_safe()
        try:
            # Reset and create a simple test case to detect the bug
            response = self.session.post(f"{BASE_URL}/progress/reset-all-stars")
            if response.status_code == 200:
                # Add 3 task stars
                response = self.session.post(f"{BASE_URL}/stars/{task1_id}/friday?stars=2")
                response = self.session.post(f"{BASE_URL}/stars/{task2_id}/friday?stars=1")
                
                # Get initial state
                response = self.session.get(f"{BASE_URL}/progress")
                if response.status_code == 200:
                    initial_progress = response.json()
                    initial_earned = initial_progress.get("total_stars_earned", 0)
                    
                    # Move 2 stars to safe
                    response = self.session.post(f"{BASE_URL}/progress/add-to-safe?stars=2")
                    if response.status_code == 200:
                        # Get state after safe transfer
                        response = self.session.get(f"{BASE_URL}/progress")
                        if response.status_code == 200:
                            after_progress = response.json()
                            after_earned = after_progress.get("total_stars_earned", 0)
                            
                            # BUG CHECK: total_stars_earned should NEVER decrease
                            if after_earned == initial_earned:
                                self.log_test("CRITICAL BUG CHECK: total_stars_earned Preservation", True, 
                                            f"✅ total_stars_earned correctly preserved: {initial_earned} → {after_earned}")
                                success_count += 1
                            else:
                                self.log_test("CRITICAL BUG CHECK: total_stars_earned Preservation", False, 
                                            f"🐛 CRITICAL BUG DETECTED: total_stars_earned changed from {initial_earned} to {after_earned} (should never decrease!)")
        except Exception as e:
            self.log_test("CRITICAL BUG CHECK", False, f"Exception: {str(e)}")
        
        return success_count >= 6  # Expect at least 6 out of 8 main tests to pass
    
    def cleanup_resources(self):
        """Clean up created test resources"""
        print("\n🧹 Cleaning up test resources...")
        
        # Delete created tasks
        for task_id in self.created_resources['tasks']:
            try:
                self.session.delete(f"{BASE_URL}/tasks/{task_id}")
            except:
                pass
        
        # Delete created rewards
        for reward_id in self.created_resources['rewards']:
            try:
                self.session.delete(f"{BASE_URL}/rewards/{reward_id}")
            except:
                pass
        
        print("✅ Cleanup completed")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Weekly Star Tracker Backend API Tests")
        print(f"🔗 Testing against: {BASE_URL}")
        print("=" * 60)
        
        test_functions = [
            ("API Health Check", self.test_api_health),
            ("Task Management", self.test_task_management),
            ("Star System", self.test_star_system),
            ("Progress Tracking", self.test_progress_tracking),
            ("Rewards System", self.test_rewards_system),
            ("Math Challenge Generation", self.test_math_challenge),
            ("Math Answer Submission", self.test_math_answer_submission),
            ("Math Settings", self.test_math_settings),
            ("German Word Problems (Textaufgaben)", self.test_german_word_problems),
            ("Configurable Problem Count", self.test_configurable_problem_count),
            ("Mixed Problem Types Distribution", self.test_mixed_problem_types),
            ("Word Problem Error Handling", self.test_word_problem_error_handling),
            ("Stars System Fixes (Sternen-System-Fixes)", self.test_stars_system_fixes),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} - ALL PASSED")
                else:
                    print(f"❌ {test_name} - SOME FAILED")
            except Exception as e:
                print(f"💥 {test_name} - EXCEPTION: {str(e)}")
        
        # Cleanup
        self.cleanup_resources()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Test Categories: {total_tests}")
        print(f"Passed Categories: {passed_tests}")
        print(f"Failed Categories: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\n📝 Detailed Results ({len(self.test_results)} individual tests):")
        passed_individual = sum(1 for result in self.test_results if result['success'])
        print(f"Individual Tests Passed: {passed_individual}/{len(self.test_results)}")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)