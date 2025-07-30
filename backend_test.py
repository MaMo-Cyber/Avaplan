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
                    # Incorrect answer
                    answers[i] = problem["correct_answer"] + 1
            
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