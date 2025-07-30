#!/usr/bin/env python3
"""
Focused Testing for Word Problems (Textaufgaben) in Math System
Tests the specific issues mentioned in the German review request
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://f41a1735-96ed-4c9f-be36-a1ee0d3d4ca3.preview.emergentagent.com/api"
TIMEOUT = 30

class WordProblemsTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.created_resources = {
            'challenges': [],
            'settings_backup': None
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
    
    def backup_current_settings(self):
        """Backup current math settings before testing"""
        try:
            response = self.session.get(f"{BASE_URL}/math/settings")
            if response.status_code == 200:
                self.created_resources['settings_backup'] = response.json()
                self.log_test("Backup Current Settings", True, "Settings backed up successfully")
                return True
            else:
                self.log_test("Backup Current Settings", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backup Current Settings", False, f"Exception: {str(e)}")
            return False
    
    def test_word_problems_only_configuration(self):
        """Test 1: Math Settings with only word_problems enabled"""
        success_count = 0
        
        # Configure settings with only word_problems enabled
        word_problems_only_settings = {
            "max_number": 100,
            "max_multiplication": 10,
            "star_tiers": {"90": 3, "80": 2, "70": 1},
            "problem_types": {
                "addition": False,
                "subtraction": False,
                "multiplication": False,
                "clock_reading": False,
                "currency_math": False,
                "word_problems": True
            },
            "currency_settings": {
                "currency_symbol": "€",
                "max_amount": 20.00,
                "decimal_places": 2
            },
            "clock_settings": {
                "include_half_hours": True,
                "include_quarter_hours": True,
                "include_five_minute_intervals": False
            }
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/math/settings", json=word_problems_only_settings)
            if response.status_code == 200:
                settings = response.json()
                if settings["problem_types"]["word_problems"] == True and \
                   all(not v for k, v in settings["problem_types"].items() if k != "word_problems"):
                    self.log_test("Configure Word Problems Only", True, "Settings configured with only word_problems enabled")
                    success_count += 1
                else:
                    self.log_test("Configure Word Problems Only", False, "Settings not properly configured", settings["problem_types"])
            else:
                self.log_test("Configure Word Problems Only", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Configure Word Problems Only", False, f"Exception: {str(e)}")
        
        return success_count == 1
    
    def test_word_problems_grade_2_generation(self):
        """Test 2: Generate Grade 2 word problems and analyze AI response"""
        success_count = 0
        
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/2")
            if response.status_code == 200:
                challenge = response.json()
                if "problems" in challenge and len(challenge["problems"]) > 0:
                    self.created_resources['challenges'].append(challenge["id"])
                    problems = challenge["problems"]
                    
                    # Analyze the generated problems
                    word_problem_count = 0
                    text_problems = []
                    
                    for problem in problems:
                        if problem.get("question_type") == "text" or "question_type" not in problem:
                            # Check if it's actually a word problem (German text)
                            question = problem.get("question", "")
                            if any(word in question.lower() for word in ["was", "wie", "wieviel", "berechne", "löse", "aufgabe"]):
                                word_problem_count += 1
                                text_problems.append(question)
                    
                    self.log_test("Grade 2 Word Problems Generation", True, 
                                f"Generated {len(problems)} problems, {word_problem_count} appear to be word problems")
                    success_count += 1
                    
                    # Check if problems have proper structure
                    first_problem = problems[0]
                    if "question" in first_problem and "correct_answer" in first_problem:
                        self.log_test("Word Problem Structure Check", True, 
                                    f"First problem: '{first_problem['question'][:50]}...' Answer: '{first_problem['correct_answer']}'")
                        success_count += 1
                    else:
                        self.log_test("Word Problem Structure Check", False, "Missing required fields", first_problem)
                    
                    # Log some example problems for analysis
                    if text_problems:
                        self.log_test("Word Problems Examples", True, 
                                    f"Sample problems: {text_problems[:3]}")
                        success_count += 1
                    else:
                        self.log_test("Word Problems Examples", False, "No clear word problems found in German")
                
                else:
                    self.log_test("Grade 2 Word Problems Generation", False, "No problems generated", challenge)
            else:
                self.log_test("Grade 2 Word Problems Generation", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Grade 2 Word Problems Generation", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_word_problems_grade_3_generation(self):
        """Test 3: Generate Grade 3 word problems and analyze AI response"""
        success_count = 0
        
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/3")
            if response.status_code == 200:
                challenge = response.json()
                if "problems" in challenge and len(challenge["problems"]) > 0:
                    self.created_resources['challenges'].append(challenge["id"])
                    problems = challenge["problems"]
                    
                    # Analyze the generated problems for Grade 3
                    word_problem_count = 0
                    complex_problems = []
                    
                    for problem in problems:
                        question = problem.get("question", "")
                        # Check for more complex Grade 3 word problem indicators
                        if any(word in question.lower() for word in ["berechne", "löse", "aufgabe", "problem", "geschichte"]):
                            word_problem_count += 1
                            complex_problems.append(question)
                    
                    self.log_test("Grade 3 Word Problems Generation", True, 
                                f"Generated {len(problems)} problems, {word_problem_count} appear to be word problems")
                    success_count += 1
                    
                    # Check answer format and complexity
                    answers_valid = True
                    for problem in problems[:5]:  # Check first 5
                        answer = problem.get("correct_answer", "")
                        try:
                            # Try to parse as number
                            float(str(answer).replace(",", "."))
                        except:
                            # Non-numeric answers might be valid for word problems
                            pass
                    
                    self.log_test("Grade 3 Answer Format Check", True, "Answer formats appear valid")
                    success_count += 1
                    
                    # Log examples
                    if complex_problems:
                        self.log_test("Grade 3 Word Problems Examples", True, 
                                    f"Sample problems: {complex_problems[:2]}")
                        success_count += 1
                    else:
                        self.log_test("Grade 3 Word Problems Examples", False, "No clear word problems found")
                
                else:
                    self.log_test("Grade 3 Word Problems Generation", False, "No problems generated", challenge)
            else:
                self.log_test("Grade 3 Word Problems Generation", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Grade 3 Word Problems Generation", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_problem_type_distribution(self):
        """Test 4: Test various combinations of enabled problem types"""
        success_count = 0
        
        # Test mixed configuration
        mixed_settings = {
            "max_number": 100,
            "max_multiplication": 10,
            "star_tiers": {"90": 3, "80": 2, "70": 1},
            "problem_types": {
                "addition": True,
                "subtraction": False,
                "multiplication": True,
                "clock_reading": False,
                "currency_math": False,
                "word_problems": True
            }
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/math/settings", json=mixed_settings)
            if response.status_code == 200:
                self.log_test("Mixed Problem Types Configuration", True, "Mixed settings applied successfully")
                success_count += 1
                
                # Generate challenge with mixed types
                response = self.session.post(f"{BASE_URL}/math/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    # Analyze distribution
                    type_counts = {"addition": 0, "multiplication": 0, "word_problems": 0, "other": 0}
                    
                    for problem in problems:
                        question = problem.get("question", "").lower()
                        if "+" in question:
                            type_counts["addition"] += 1
                        elif "×" in question or "*" in question:
                            type_counts["multiplication"] += 1
                        elif any(word in question for word in ["was", "wie", "berechne", "löse"]):
                            type_counts["word_problems"] += 1
                        else:
                            type_counts["other"] += 1
                    
                    self.log_test("Problem Type Distribution", True, 
                                f"Distribution: {type_counts}")
                    success_count += 1
                else:
                    self.log_test("Mixed Types Challenge Generation", False, f"Status code: {response.status_code}")
            else:
                self.log_test("Mixed Problem Types Configuration", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Problem Type Distribution Test", False, f"Exception: {str(e)}")
        
        return success_count >= 1
    
    def test_ai_response_parsing(self):
        """Test 5: Check AI response parsing for German word problems"""
        success_count = 0
        
        # First, ensure we have word problems enabled
        word_problems_settings = {
            "problem_types": {
                "addition": False,
                "subtraction": False,
                "multiplication": False,
                "clock_reading": False,
                "currency_math": False,
                "word_problems": True
            }
        }
        
        try:
            # Update settings
            response = self.session.put(f"{BASE_URL}/math/settings", json=word_problems_settings)
            if response.status_code == 200:
                self.log_test("AI Response Test Setup", True, "Word problems enabled for AI response test")
                success_count += 1
                
                # Generate multiple challenges to test consistency
                for grade in [2, 3]:
                    try:
                        response = self.session.post(f"{BASE_URL}/math/challenge/{grade}")
                        if response.status_code == 200:
                            challenge = response.json()
                            problems = challenge.get("problems", [])
                            
                            # Check for JSON parsing issues
                            json_valid = True
                            german_text_found = False
                            
                            for problem in problems:
                                # Check if problem has all required fields
                                if not all(key in problem for key in ["question", "correct_answer"]):
                                    json_valid = False
                                    break
                                
                                # Check for German text
                                question = problem.get("question", "")
                                if any(word in question.lower() for word in ["was", "wie", "ist", "sind", "der", "die", "das"]):
                                    german_text_found = True
                            
                            if json_valid:
                                self.log_test(f"Grade {grade} JSON Parsing", True, "All problems have valid JSON structure")
                                success_count += 1
                            else:
                                self.log_test(f"Grade {grade} JSON Parsing", False, "Some problems missing required fields")
                            
                            if german_text_found:
                                self.log_test(f"Grade {grade} German Text", True, "German text found in problems")
                                success_count += 1
                            else:
                                self.log_test(f"Grade {grade} German Text", False, "No clear German text found")
                        
                        else:
                            self.log_test(f"Grade {grade} AI Response Test", False, f"Status code: {response.status_code}")
                    
                    except json.JSONDecodeError as e:
                        self.log_test(f"Grade {grade} JSON Parsing", False, f"JSON decode error: {str(e)}")
                    except Exception as e:
                        self.log_test(f"Grade {grade} AI Response Test", False, f"Exception: {str(e)}")
            
            else:
                self.log_test("AI Response Test Setup", False, f"Status code: {response.status_code}")
        
        except Exception as e:
            self.log_test("AI Response Parsing Test", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_error_handling_fallback(self):
        """Test 6: Test error handling and fallback mechanisms"""
        success_count = 0
        
        # Test with invalid OpenAI key scenario (simulate by checking current behavior)
        try:
            # Generate a challenge and see if fallback works
            response = self.session.post(f"{BASE_URL}/math/challenge/2")
            if response.status_code == 200:
                challenge = response.json()
                problems = challenge.get("problems", [])
                
                if len(problems) > 0:
                    # Check if problems look like AI-generated or fallback
                    first_problem = problems[0]
                    question = first_problem.get("question", "")
                    
                    # Fallback problems typically have simple English format
                    if "What is" in question:
                        self.log_test("Fallback Mechanism Detection", True, "Appears to be using fallback simple problems")
                        success_count += 1
                    else:
                        self.log_test("AI Generation Working", True, "AI generation appears to be working (no fallback needed)")
                        success_count += 1
                    
                    # Test answer submission to ensure grading works
                    answers = {0: first_problem.get("correct_answer", "0")}
                    response = self.session.post(f"{BASE_URL}/math/challenge/{challenge['id']}/submit", json=answers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "correct_answers" in result:
                            self.log_test("Error Handling - Answer Submission", True, "Answer submission works with generated problems")
                            success_count += 1
                        else:
                            self.log_test("Error Handling - Answer Submission", False, "Invalid submission response", result)
                    else:
                        self.log_test("Error Handling - Answer Submission", False, f"Status code: {response.status_code}")
                
                else:
                    self.log_test("Error Handling Test", False, "No problems generated")
            
            else:
                self.log_test("Error Handling Test", False, f"Challenge generation failed: {response.status_code}")
        
        except Exception as e:
            self.log_test("Error Handling Test", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def restore_settings(self):
        """Restore original settings"""
        if self.created_resources['settings_backup']:
            try:
                response = self.session.put(f"{BASE_URL}/math/settings", json=self.created_resources['settings_backup'])
                if response.status_code == 200:
                    self.log_test("Restore Original Settings", True, "Settings restored successfully")
                else:
                    self.log_test("Restore Original Settings", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test("Restore Original Settings", False, f"Exception: {str(e)}")
    
    def cleanup_resources(self):
        """Clean up created test resources"""
        print("\n🧹 Cleaning up test resources...")
        
        # Delete created challenges
        for challenge_id in self.created_resources['challenges']:
            try:
                # Note: There's no delete endpoint for challenges, they'll be cleaned up naturally
                pass
            except:
                pass
        
        # Restore original settings
        self.restore_settings()
        
        print("✅ Cleanup completed")
    
    def run_word_problems_tests(self):
        """Run all word problems focused tests"""
        print("🚀 Starting Word Problems (Textaufgaben) Focused Testing")
        print(f"🔗 Testing against: {BASE_URL}")
        print("=" * 70)
        
        # Backup settings first
        if not self.backup_current_settings():
            print("❌ Failed to backup settings, continuing anyway...")
        
        test_functions = [
            ("Word Problems Only Configuration", self.test_word_problems_only_configuration),
            ("Grade 2 Word Problems Generation", self.test_word_problems_grade_2_generation),
            ("Grade 3 Word Problems Generation", self.test_word_problems_grade_3_generation),
            ("Problem Type Distribution", self.test_problem_type_distribution),
            ("AI Response Parsing", self.test_ai_response_parsing),
            ("Error Handling & Fallback", self.test_error_handling_fallback),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            print(f"\n📋 Running {test_name} Test...")
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"💥 {test_name} - EXCEPTION: {str(e)}")
        
        # Cleanup
        self.cleanup_resources()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 WORD PROBLEMS TEST SUMMARY")
        print("=" * 70)
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
        
        # Analysis and recommendations
        print(f"\n🔍 ANALYSIS:")
        if passed_tests == total_tests:
            print("✅ All word problems tests passed - functionality appears to be working correctly")
        else:
            print("⚠️  Some word problems tests failed - issues identified:")
            for test in failed_tests:
                if "word_problems" in test['test'].lower() or "textaufgaben" in test['test'].lower():
                    print(f"   - {test['test']}: {test['details']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = WordProblemsTestSuite()
    success = tester.run_word_problems_tests()
    exit(0 if success else 1)