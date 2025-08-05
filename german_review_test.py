#!/usr/bin/env python3
"""
Focused German Review Request Tests for Weekly Star Tracker
Tests specifically requested features: German word problems and configurable problem count
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://08ea8e81-0160-4f81-bdfa-a3009c5ac4a3.preview.emergentagent.com/api"
TIMEOUT = 30

class GermanReviewTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
    
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
        print()
    
    def test_1_deutsche_textaufgaben(self):
        """Test 1: Deutsche Textaufgaben Test"""
        print("🇩🇪 TEST 1: DEUTSCHE TEXTAUFGABEN TEST")
        print("=" * 50)
        
        success_count = 0
        
        # Update Math Settings: Set only "word_problems": true (all others false)
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
                }
            }
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=word_problems_settings)
            if response.status_code == 200:
                settings = response.json()
                if settings["problem_types"]["word_problems"] == True:
                    self.log_test("1.1 Configure Word Problems Only", True, "✅ Math settings updated: only word_problems=true")
                    success_count += 1
                else:
                    self.log_test("1.1 Configure Word Problems Only", False, "❌ Settings not properly configured")
            else:
                self.log_test("1.1 Configure Word Problems Only", False, f"❌ Status code: {response.status_code}")
        except Exception as e:
            self.log_test("1.1 Configure Word Problems Only", False, f"❌ Exception: {str(e)}")
        
        # Test Grade 2 German word problems
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/2")
            if response.status_code == 200:
                challenge = response.json()
                problems = challenge.get("problems", [])
                
                if len(problems) > 0:
                    # Check for German word problem templates
                    grade2_keywords = ["Anna", "Äpfel", "Tom", "Sticker", "Lisa", "Bonbons", "Max", "Spielzeugautos", "Blumen"]
                    german_problems = []
                    english_problems = []
                    
                    for i, problem in enumerate(problems):
                        question = problem.get("question", "")
                        if any(keyword in question for keyword in grade2_keywords):
                            german_problems.append(f"Problem {i+1}: {question}")
                        if "What is" in question:
                            english_problems.append(f"Problem {i+1}: {question}")
                    
                    if len(german_problems) > 0 and len(english_problems) == 0:
                        self.log_test("1.2 Grade 2 German Templates", True, f"✅ Found {len(german_problems)} German word problems with proper templates")
                        success_count += 1
                        
                        # Show examples
                        print("   📝 German Word Problem Examples:")
                        for example in german_problems[:3]:
                            print(f"      {example}")
                        
                    elif len(english_problems) > 0:
                        self.log_test("1.2 Grade 2 German Templates", False, f"❌ Found {len(english_problems)} English fallback problems instead of German")
                        print("   📝 English Fallback Examples:")
                        for example in english_problems[:3]:
                            print(f"      {example}")
                    else:
                        self.log_test("1.2 Grade 2 German Templates", False, "❌ No recognizable German word problem templates found")
                        
                    # Verify all answers ≤ 100
                    invalid_answers = []
                    for i, problem in enumerate(problems):
                        try:
                            answer = int(problem.get("correct_answer", "0"))
                            if answer > 100:
                                invalid_answers.append(f"Problem {i+1}: answer={answer}")
                        except:
                            pass  # Non-numeric answers are ok
                    
                    if len(invalid_answers) == 0:
                        self.log_test("1.3 Grade 2 Answer Range ≤100", True, "✅ All answers ≤ 100")
                        success_count += 1
                    else:
                        self.log_test("1.3 Grade 2 Answer Range ≤100", False, f"❌ {len(invalid_answers)} answers > 100: {invalid_answers}")
                        
                else:
                    self.log_test("1.2 Grade 2 German Templates", False, "❌ No problems generated")
            else:
                self.log_test("1.2 Grade 2 German Templates", False, f"❌ Status code: {response.status_code}")
        except Exception as e:
            self.log_test("1.2 Grade 2 German Templates", False, f"❌ Exception: {str(e)}")
        
        # Test Grade 3 German word problems
        try:
            response = self.session.post(f"{BASE_URL}/math/challenge/3")
            if response.status_code == 200:
                challenge = response.json()
                problems = challenge.get("problems", [])
                
                if len(problems) > 0:
                    # Check for Grade 3 German word problem templates
                    grade3_keywords = ["Sarah", "Euro", "Taschengeld", "Paket", "Keksen", "Packung", "Stifte", "Tim", "Minuten", "Klasse", "Schüler"]
                    german_problems = []
                    english_problems = []
                    
                    for i, problem in enumerate(problems):
                        question = problem.get("question", "")
                        if any(keyword in question for keyword in grade3_keywords):
                            german_problems.append(f"Problem {i+1}: {question}")
                        if "What is" in question:
                            english_problems.append(f"Problem {i+1}: {question}")
                    
                    if len(german_problems) > 0 and len(english_problems) == 0:
                        self.log_test("1.4 Grade 3 German Templates", True, f"✅ Found {len(german_problems)} Grade 3 German word problems")
                        success_count += 1
                        
                        # Show examples
                        print("   📝 Grade 3 German Word Problem Examples:")
                        for example in german_problems[:3]:
                            print(f"      {example}")
                        
                    elif len(english_problems) > 0:
                        self.log_test("1.4 Grade 3 German Templates", False, f"❌ Found {len(english_problems)} English fallback problems instead of German")
                    else:
                        self.log_test("1.4 Grade 3 German Templates", False, "❌ No recognizable Grade 3 German word problem templates found")
                        
                else:
                    self.log_test("1.4 Grade 3 German Templates", False, "❌ No problems generated")
            else:
                self.log_test("1.4 Grade 3 German Templates", False, f"❌ Status code: {response.status_code}")
        except Exception as e:
            self.log_test("1.4 Grade 3 German Templates", False, f"❌ Exception: {str(e)}")
        
        print(f"\n📊 TEST 1 RESULT: {success_count}/4 tests passed")
        return success_count >= 3
    
    def test_2_konfigurierbare_aufgaben_anzahl(self):
        """Test 2: Konfigurierbare Aufgaben-Anzahl Test"""
        print("\n🔢 TEST 2: KONFIGURIERBARE AUFGABEN-ANZAHL TEST")
        print("=" * 50)
        
        success_count = 0
        
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
                            self.log_test(f"2.{test_counts.index(count)+1} Problem Count {count}", True, f"✅ Generated exactly {actual_count} problems")
                            success_count += 1
                        else:
                            self.log_test(f"2.{test_counts.index(count)+1} Problem Count {count}", False, f"❌ Expected {count} problems, got {actual_count}")
                    else:
                        self.log_test(f"2.{test_counts.index(count)+1} Problem Count {count}", False, f"❌ Challenge creation failed: {response.status_code}")
                else:
                    self.log_test(f"2.{test_counts.index(count)+1} Problem Count {count}", False, f"❌ Settings update failed: {response.status_code}")
            except Exception as e:
                self.log_test(f"2.{test_counts.index(count)+1} Problem Count {count}", False, f"❌ Exception: {str(e)}")
        
        print(f"\n📊 TEST 2 RESULT: {success_count}/4 tests passed")
        return success_count >= 3
    
    def test_3_mixed_problem_types(self):
        """Test 3: Mixed Problem Types Test"""
        print("\n🎯 TEST 3: MIXED PROBLEM TYPES TEST")
        print("=" * 50)
        
        success_count = 0
        
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
                }
            }
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=mixed_settings)
            if response.status_code == 200:
                self.log_test("3.1 Configure Mixed Types", True, "✅ Settings: word_problems=true, addition=true, clock_reading=true")
                success_count += 1
                
                # Create challenge and analyze problem type distribution
                response = self.session.post(f"{BASE_URL}/math/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    if len(problems) == 12:
                        self.log_test("3.2 Problem Count 12", True, f"✅ Generated exactly 12 problems as configured")
                        success_count += 1
                        
                        # Count problem types
                        type_counts = {"addition": 0, "clock": 0, "word_problem": 0}
                        
                        for problem in problems:
                            question = problem.get("question", "")
                            question_type = problem.get("question_type", "text")
                            
                            if question_type == "clock":
                                type_counts["clock"] += 1
                            elif any(keyword in question for keyword in ["Anna", "Tom", "Lisa", "Max", "Sarah"]):
                                type_counts["word_problem"] += 1
                            else:
                                type_counts["addition"] += 1
                        
                        # Check if distribution is reasonable (each type should have 2-6 problems out of 12)
                        distribution_ok = all(2 <= count <= 6 for count in type_counts.values())
                        
                        if distribution_ok:
                            self.log_test("3.3 Problem Distribution", True, f"✅ Good distribution: {type_counts}")
                            success_count += 1
                        else:
                            self.log_test("3.3 Problem Distribution", False, f"❌ Uneven distribution: {type_counts}")
                            
                    else:
                        self.log_test("3.2 Problem Count 12", False, f"❌ Expected 12 problems, got {len(problems)}")
                else:
                    self.log_test("3.2 Mixed Challenge Creation", False, f"❌ Challenge creation failed: {response.status_code}")
            else:
                self.log_test("3.1 Configure Mixed Types", False, f"❌ Settings update failed: {response.status_code}")
        except Exception as e:
            self.log_test("3.1 Mixed Problem Types", False, f"❌ Exception: {str(e)}")
        
        print(f"\n📊 TEST 3 RESULT: {success_count}/3 tests passed")
        return success_count >= 2
    
    def test_4_grade_specific_validation(self):
        """Test 4: Grade-specific Textaufgaben Test"""
        print("\n📚 TEST 4: GRADE-SPECIFIC TEXTAUFGABEN TEST")
        print("=" * 50)
        
        success_count = 0
        
        # Configure for word problems only
        try:
            word_settings = {
                "max_number": 100,
                "max_multiplication": 10,
                "problem_count": 10,
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
            
            response = self.session.put(f"{BASE_URL}/math/settings", json=word_settings)
            if response.status_code == 200:
                # Test Grade 2: Simple problems (Äpfel, Sticker, Bonbons)
                response = self.session.post(f"{BASE_URL}/math/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    grade2_simple_keywords = ["Äpfel", "Sticker", "Bonbons", "Spielzeugautos", "Blumen"]
                    simple_problems = []
                    
                    for problem in problems:
                        question = problem.get("question", "")
                        if any(keyword in question for keyword in grade2_simple_keywords):
                            simple_problems.append(question)
                    
                    if len(simple_problems) > 0:
                        self.log_test("4.1 Grade 2 Simple Problems", True, f"✅ Found {len(simple_problems)} simple Grade 2 problems")
                        success_count += 1
                        print("   📝 Grade 2 Examples:")
                        for example in simple_problems[:2]:
                            print(f"      {example}")
                    else:
                        self.log_test("4.1 Grade 2 Simple Problems", False, "❌ No Grade 2 simple problems found")
                
                # Test Grade 3: Complex problems (Euro, Division, Multiplication)
                response = self.session.post(f"{BASE_URL}/math/challenge/3")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    grade3_complex_keywords = ["Euro", "Paket", "Packung", "Minuten", "Klasse", "Schüler"]
                    complex_problems = []
                    
                    for problem in problems:
                        question = problem.get("question", "")
                        if any(keyword in question for keyword in grade3_complex_keywords):
                            complex_problems.append(question)
                    
                    if len(complex_problems) > 0:
                        self.log_test("4.2 Grade 3 Complex Problems", True, f"✅ Found {len(complex_problems)} complex Grade 3 problems")
                        success_count += 1
                        print("   📝 Grade 3 Examples:")
                        for example in complex_problems[:2]:
                            print(f"      {example}")
                    else:
                        self.log_test("4.2 Grade 3 Complex Problems", False, "❌ No Grade 3 complex problems found")
                    
                    # Verify all answers ≤ 100 for both grades
                    all_valid = True
                    invalid_count = 0
                    
                    for problem in problems:
                        try:
                            answer = int(problem.get("correct_answer", "0"))
                            if answer > 100:
                                all_valid = False
                                invalid_count += 1
                        except:
                            pass
                    
                    if all_valid:
                        self.log_test("4.3 All Answers ≤100", True, "✅ All Grade 3 answers ≤ 100")
                        success_count += 1
                    else:
                        self.log_test("4.3 All Answers ≤100", False, f"❌ {invalid_count} answers > 100")
                        
        except Exception as e:
            self.log_test("4.1 Grade-specific Test", False, f"❌ Exception: {str(e)}")
        
        print(f"\n📊 TEST 4 RESULT: {success_count}/3 tests passed")
        return success_count >= 2
    
    def test_5_error_handling(self):
        """Test 5: Error Handling Test"""
        print("\n🛡️ TEST 5: ERROR HANDLING TEST")
        print("=" * 50)
        
        success_count = 0
        
        # Test with extreme settings
        try:
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
                response = self.session.post(f"{BASE_URL}/math/challenge/2")
                if response.status_code == 200:
                    challenge = response.json()
                    problems = challenge.get("problems", [])
                    
                    if len(problems) > 0:
                        self.log_test("5.1 Extreme Settings Fallback", True, f"✅ Generated {len(problems)} problems with extreme settings")
                        success_count += 1
                    else:
                        self.log_test("5.1 Extreme Settings Fallback", False, "❌ No problems generated with extreme settings")
                else:
                    self.log_test("5.1 Extreme Settings Fallback", False, f"❌ Challenge creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("5.1 Extreme Settings", False, f"❌ Exception: {str(e)}")
        
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
                        self.log_test("5.2 No Types Fallback", True, f"✅ Generated {len(problems)} fallback problems")
                        success_count += 1
                    else:
                        self.log_test("5.2 No Types Fallback", False, "❌ No fallback problems generated")
                else:
                    self.log_test("5.2 No Types Fallback", False, f"❌ Challenge creation failed: {response.status_code}")
        except Exception as e:
            self.log_test("5.2 No Types Fallback", False, f"❌ Exception: {str(e)}")
        
        print(f"\n📊 TEST 5 RESULT: {success_count}/2 tests passed")
        return success_count >= 1
    
    def run_german_review_tests(self):
        """Run all German review tests"""
        print("🇩🇪 GERMAN REVIEW REQUEST - COMPREHENSIVE TESTING")
        print("=" * 60)
        print("Testing: Deutsche Textaufgaben-Fixes und konfigurierbare Anzahl von Aufgaben")
        print("=" * 60)
        
        test_functions = [
            ("Deutsche Textaufgaben Test", self.test_1_deutsche_textaufgaben),
            ("Konfigurierbare Aufgaben-Anzahl Test", self.test_2_konfigurierbare_aufgaben_anzahl),
            ("Mixed Problem Types Test", self.test_3_mixed_problem_types),
            ("Grade-spezifische Textaufgaben Test", self.test_4_grade_specific_validation),
            ("Error Handling Test", self.test_5_error_handling),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"💥 {test_name} - EXCEPTION: {str(e)}")
        
        # Final Summary
        print("\n" + "=" * 60)
        print("🎯 GERMAN REVIEW REQUEST - FINAL RESULTS")
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
        else:
            print(f"\n🎉 ALL INDIVIDUAL TESTS PASSED!")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = GermanReviewTester()
    success = tester.run_german_review_tests()
    exit(0 if success else 1)