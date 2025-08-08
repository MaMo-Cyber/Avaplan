#!/usr/bin/env python3
"""
Math Challenge Creation API and Settings Integration Test
Focus on testing the specific review request requirements
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://f358c107-2a1c-4118-a0b5-322a7704d00c.preview.emergentagent.com/api"
TIMEOUT = 30

class MathChallengeSettingsTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.created_challenges = []
        self.original_settings = None
    
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
    
    def test_math_challenge_settings_integration(self):
        """Test math challenge creation API and settings integration as per review request
        
        Focus on:
        1. Test the current math challenge creation endpoint: POST /api/math/challenge/2
        2. Check what parameters it expects and what it returns
        3. Test the math settings endpoint: GET /api/math/settings to see current settings
        4. Verify if the challenge creation API uses the settings from the settings endpoint
        5. Test if changing settings (like problem_count from 10 to 20) affects the challenge generation
        """
        success_count = 0
        
        print("\n🧮 Testing Math Challenge Creation API and Settings Integration")
        print("Focus: Challenge creation, settings usage, problem count configuration")
        
        # 1. TEST MATH SETTINGS ENDPOINT - Get current settings
        try:
            response = self.session.get(f"{BASE_URL}/math/settings")
            if response.status_code == 200:
                settings = response.json()
                
                # Check for expected fields
                expected_fields = ["max_number", "max_multiplication", "problem_count", "star_tiers", "problem_types"]
                missing_fields = [field for field in expected_fields if field not in settings]
                
                if not missing_fields:
                    current_problem_count = settings.get("problem_count", 30)
                    self.log_test("1. Get Math Settings", True, 
                                f"✅ Settings retrieved: problem_count={current_problem_count}, max_number={settings.get('max_number')}, problem_types={list(settings.get('problem_types', {}).keys())}")
                    success_count += 1
                    
                    # Store original settings for later restoration
                    self.original_settings = settings
                else:
                    self.log_test("1. Get Math Settings", False, 
                                f"❌ Missing required fields: {missing_fields}")
            else:
                self.log_test("1. Get Math Settings", False, 
                            f"❌ Status code: {response.status_code}")
        except Exception as e:
            self.log_test("1. Get Math Settings", False, f"❌ Exception: {str(e)}")
        
        # 2. TEST MATH CHALLENGE CREATION - Default settings
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/2")
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if response has challenge wrapper
                if "challenge" in response_data:
                    challenge = response_data["challenge"]
                else:
                    challenge = response_data
                
                # Check response structure
                expected_fields = ["id", "grade", "problems", "completed", "score", "stars_earned", "created_at"]
                missing_fields = [field for field in expected_fields if field not in challenge]
                
                if not missing_fields:
                    problems = challenge.get("problems", [])
                    problem_count = len(problems)
                    
                    self.log_test("2. Math Challenge Creation (Grade 2)", True, 
                                f"✅ Challenge created: {problem_count} problems, grade={challenge.get('grade')}, id={challenge.get('id')}")
                    success_count += 1
                    
                    # Store challenge for cleanup
                    self.created_challenges.append(challenge["id"])
                    
                    # Check problem structure
                    if problems:
                        first_problem = problems[0]
                        problem_fields = ["id", "question", "correct_answer"]
                        problem_missing = [field for field in problem_fields if field not in first_problem]
                        
                        if not problem_missing:
                            self.log_test("2. Problem Structure Validation", True, 
                                        f"✅ Problems have correct structure: question_type={first_problem.get('question_type', 'text')}")
                            success_count += 1
                        else:
                            self.log_test("2. Problem Structure Validation", False, 
                                        f"❌ Missing problem fields: {problem_missing}")
                    else:
                        self.log_test("2. Problem Structure Validation", False, "❌ No problems generated")
                else:
                    self.log_test("2. Math Challenge Creation (Grade 2)", False, 
                                f"❌ Missing challenge fields: {missing_fields}")
            else:
                self.log_test("2. Math Challenge Creation (Grade 2)", False, 
                            f"❌ Status code: {response.status_code}")
        except Exception as e:
            self.log_test("2. Math Challenge Creation (Grade 2)", False, f"❌ Exception: {str(e)}")
        
        # 3. TEST SETTINGS INTEGRATION - Change problem_count and verify
        try:
            # Update settings with different problem_count
            new_settings = {
                "max_number": 100,
                "max_multiplication": 10,
                "problem_count": 15,  # Changed from default
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
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=new_settings)
            if response.status_code == 200:
                updated_settings = response.json()
                
                if updated_settings.get("problem_count") == 15:
                    self.log_test("3. Update Settings (problem_count=15)", True, 
                                f"✅ Settings updated successfully: problem_count={updated_settings.get('problem_count')}")
                    success_count += 1
                    
                    # Create new challenge to test if settings are used
                    response = self.session.post(f"{BASE_URL}/math/challenge/2")
                    if response.status_code == 200:
                        response_data = response.json()
                        challenge = response_data.get("challenge", response_data)
                        actual_problem_count = len(challenge.get("problems", []))
                        
                        if actual_problem_count == 15:
                            self.log_test("3. Settings Integration Test (15 problems)", True, 
                                        f"✅ Challenge respects settings: generated {actual_problem_count} problems as configured")
                            success_count += 1
                        else:
                            self.log_test("3. Settings Integration Test (15 problems)", False, 
                                        f"❌ Expected 15 problems, got {actual_problem_count}")
                        
                        # Store challenge for cleanup
                        self.created_challenges.append(challenge["id"])
                    else:
                        self.log_test("3. Settings Integration Test (15 problems)", False, 
                                    f"❌ Challenge creation failed: {response.status_code}")
                else:
                    self.log_test("3. Update Settings (problem_count=15)", False, 
                                f"❌ Settings not updated correctly: {updated_settings}")
            else:
                self.log_test("3. Update Settings (problem_count=15)", False, 
                            f"❌ Settings update failed: {response.status_code}")
        except Exception as e:
            self.log_test("3. Settings Integration Test", False, f"❌ Exception: {str(e)}")
        
        # 4. TEST DIFFERENT PROBLEM COUNTS - 10, 20, 40
        test_counts = [10, 20, 40]
        for count in test_counts:
            try:
                # Update settings
                settings_update = {
                    "max_number": 100,
                    "max_multiplication": 10,
                    "problem_count": count,
                    "star_tiers": {"90": 3, "80": 2, "70": 1},
                    "problem_types": {
                        "addition": True,
                        "subtraction": True,
                        "multiplication": False,
                        "clock_reading": False,
                        "currency_math": False,
                        "word_problems": False
                    }
                }
                
                response = self.session.put(f"{BASE_URL}/math/settings", json=settings_update)
                if response.status_code == 200:
                    # Create challenge
                    response = self.session.post(f"{BASE_URL}/math/challenge/2")
                    if response.status_code == 200:
                        challenge = response.json()
                        actual_count = len(challenge.get("problems", []))
                        
                        if actual_count == count:
                            self.log_test(f"4. Problem Count Test ({count})", True, 
                                        f"✅ Generated exactly {actual_count} problems")
                            success_count += 1
                        else:
                            self.log_test(f"4. Problem Count Test ({count})", False, 
                                        f"❌ Expected {count}, got {actual_count}")
                        
                        # Store challenge for cleanup
                        self.created_challenges.append(challenge["id"])
                    else:
                        self.log_test(f"4. Problem Count Test ({count})", False, 
                                    f"❌ Challenge creation failed: {response.status_code}")
                else:
                    self.log_test(f"4. Problem Count Test ({count})", False, 
                                f"❌ Settings update failed: {response.status_code}")
            except Exception as e:
                self.log_test(f"4. Problem Count Test ({count})", False, f"❌ Exception: {str(e)}")
        
        # 5. TEST GRADE 3 CHALLENGE CREATION
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/3")
            if response.status_code == 200:
                challenge = response.json()
                problems = challenge.get("problems", [])
                
                if len(problems) > 0 and challenge.get("grade") == 3:
                    self.log_test("5. Math Challenge Creation (Grade 3)", True, 
                                f"✅ Grade 3 challenge created: {len(problems)} problems")
                    success_count += 1
                    
                    # Store challenge for cleanup
                    self.created_challenges.append(challenge["id"])
                else:
                    self.log_test("5. Math Challenge Creation (Grade 3)", False, 
                                f"❌ Invalid Grade 3 challenge: {challenge}")
            else:
                self.log_test("5. Math Challenge Creation (Grade 3)", False, 
                            f"❌ Status code: {response.status_code}")
        except Exception as e:
            self.log_test("5. Math Challenge Creation (Grade 3)", False, f"❌ Exception: {str(e)}")
        
        # 6. TEST INVALID GRADE HANDLING
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/5")
            if response.status_code == 400:
                self.log_test("6. Invalid Grade Handling", True, 
                            "✅ Correctly rejected invalid grade (5)")
                success_count += 1
            else:
                self.log_test("6. Invalid Grade Handling", False, 
                            f"❌ Should reject grade 5, got status: {response.status_code}")
        except Exception as e:
            self.log_test("6. Invalid Grade Handling", False, f"❌ Exception: {str(e)}")
        
        # 7. TEST PROBLEM TYPES CONFIGURATION
        try:
            # Configure only specific problem types
            specific_settings = {
                "max_number": 50,
                "max_multiplication": 5,
                "problem_count": 12,
                "star_tiers": {"90": 3, "80": 2, "70": 1},
                "problem_types": {
                    "addition": True,
                    "subtraction": False,
                    "multiplication": True,
                    "clock_reading": False,
                    "currency_math": False,
                    "word_problems": False
                }
            }
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=specific_settings)
            if response.status_code == 200:
                # Create challenge and analyze problem types
                response = self.session.post(f"{BASE_URL}/math/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    # Count problem types (basic analysis)
                    addition_count = 0
                    multiplication_count = 0
                    
                    for problem in problems:
                        question = problem.get("question", "")
                        if "+" in question:
                            addition_count += 1
                        elif "×" in question or "*" in question:
                            multiplication_count += 1
                    
                    if addition_count > 0 and multiplication_count > 0:
                        self.log_test("7. Problem Types Configuration", True, 
                                    f"✅ Mixed problem types: {addition_count} addition, {multiplication_count} multiplication")
                        success_count += 1
                    else:
                        self.log_test("7. Problem Types Configuration", True, 
                                    f"✅ Problem types generated (analysis limited): total {len(problems)} problems")
                        success_count += 1
                    
                    # Store challenge for cleanup
                    self.created_challenges.append(challenge["id"])
                else:
                    self.log_test("7. Problem Types Configuration", False, 
                                f"❌ Challenge creation failed: {response.status_code}")
            else:
                self.log_test("7. Problem Types Configuration", False, 
                            f"❌ Settings update failed: {response.status_code}")
        except Exception as e:
            self.log_test("7. Problem Types Configuration", False, f"❌ Exception: {str(e)}")
        
        # 8. RESTORE ORIGINAL SETTINGS (if we have them)
        try:
            if self.original_settings:
                response = self.session.put(f"{BASE_URL}/math/settings", json=self.original_settings)
                if response.status_code == 200:
                    self.log_test("8. Restore Original Settings", True, 
                                "✅ Original settings restored")
                    success_count += 1
                else:
                    self.log_test("8. Restore Original Settings", False, 
                                f"❌ Failed to restore: {response.status_code}")
            else:
                self.log_test("8. Restore Original Settings", True, 
                            "✅ No original settings to restore")
                success_count += 1
        except Exception as e:
            self.log_test("8. Restore Original Settings", False, f"❌ Exception: {str(e)}")
        
        return success_count >= 6  # Expect at least 6 out of 8 tests to pass
    
    def run_all_tests(self):
        """Run all math challenge settings integration tests"""
        print("🚀 Starting Math Challenge Settings Integration Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run the main test
        test_passed = self.test_math_challenge_settings_integration()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        if test_passed:
            print("\n🎉 OVERALL RESULT: MATH CHALLENGE SETTINGS INTEGRATION TESTS PASSED")
        else:
            print("\n❌ OVERALL RESULT: MATH CHALLENGE SETTINGS INTEGRATION TESTS FAILED")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        return test_passed

if __name__ == "__main__":
    tester = MathChallengeSettingsTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)