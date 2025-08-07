#!/usr/bin/env python3
"""
Focused Star Moving Functionality Test for Weekly Star Tracker
Tests the specific issue user is reporting: "❌ Fehler: [object Object]"
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8001/api"
TIMEOUT = 30

class StarMovingTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.created_resources = {
            'tasks': [],
            'rewards': []
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
    
    def test_star_moving_functionality(self):
        """Test star moving functionality that user is reporting errors with
        
        Focus on:
        1. POST /api/progress/add-to-safe 
        2. POST /api/progress/withdraw-from-safe
        3. API response format validation
        4. Backend connection to https://weekly-star-tracker-backend.onrender.com
        5. Error handling and proper error messages
        """
        success_count = 0
        
        print("\n⭐ Testing Star Moving Functionality - User Error Report")
        print("User reports: '❌ Fehler: [object Object]' when trying to move stars")
        print("Testing API endpoints and response formats...")
        print("=" * 60)
        
        # 1. TEST BACKEND CONNECTION
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "message" in data:
                    self.log_test("1. Backend Connection Test", True, 
                                f"✅ Backend responding correctly: {data.get('message', '')}")
                    success_count += 1
                else:
                    self.log_test("1. Backend Connection Test", False, 
                                f"❌ Invalid response format: {data}")
            else:
                self.log_test("1. Backend Connection Test", False, 
                            f"❌ Status code: {response.status_code}")
        except Exception as e:
            self.log_test("1. Backend Connection Test", False, f"❌ Exception: {str(e)}")
        
        # 2. SETUP TEST DATA - Create tasks and stars for testing
        try:
            # Reset all stars first
            response = self.session.post(f"{BASE_URL}/progress/reset-all-stars")
            
            # Create test tasks
            task_data = {"name": "Test Task for Star Moving"}
            response = self.session.post(f"{BASE_URL}/tasks", json=task_data)
            if response.status_code == 200:
                task_id = response.json()["id"]
                self.created_resources['tasks'].append(task_id)
                
                # Add some stars to work with
                response = self.session.post(f"{BASE_URL}/stars/{task_id}/monday?stars=2")
                response = self.session.post(f"{BASE_URL}/stars/{task_id}/tuesday?stars=2")
                response = self.session.post(f"{BASE_URL}/stars/{task_id}/wednesday?stars=1")
                
                if response.status_code == 200:
                    self.log_test("2. Test Data Setup", True, "✅ Created test task with 5 stars")
                    success_count += 1
                else:
                    self.log_test("2. Test Data Setup", False, f"❌ Failed to add stars: {response.status_code}")
            else:
                self.log_test("2. Test Data Setup", False, f"❌ Failed to create task: {response.status_code}")
        except Exception as e:
            self.log_test("2. Test Data Setup", False, f"❌ Exception: {str(e)}")
        
        # 3. TEST ADD-TO-SAFE API - Valid scenario
        try:
            request_data = {"stars": 3}
            response = self.session.post(f"{BASE_URL}/progress/add-to-safe", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response format - should be proper JSON, not [object Object]
                if isinstance(data, dict):
                    # Check for expected fields
                    expected_fields = ["stars_in_safe", "total_stars", "total_stars_earned", "total_stars_used"]
                    missing_fields = [field for field in expected_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_test("3. Add-to-Safe API (Valid)", True, 
                                    f"✅ Response format correct: {data}")
                        success_count += 1
                    else:
                        self.log_test("3. Add-to-Safe API (Valid)", False, 
                                    f"❌ Missing fields: {missing_fields}. Response: {data}")
                else:
                    self.log_test("3. Add-to-Safe API (Valid)", False, 
                                f"❌ Response not JSON object: {type(data)} - {data}")
            else:
                # Check error response format
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and ("error" in error_data or "message" in error_data or "detail" in error_data):
                        self.log_test("3. Add-to-Safe API (Valid)", False, 
                                    f"❌ API error but proper format: {error_data}")
                    else:
                        self.log_test("3. Add-to-Safe API (Valid)", False, 
                                    f"❌ Invalid error format: {error_data}")
                except:
                    self.log_test("3. Add-to-Safe API (Valid)", False, 
                                f"❌ Non-JSON error response: {response.text}")
        except Exception as e:
            self.log_test("3. Add-to-Safe API (Valid)", False, f"❌ Exception: {str(e)}")
        
        # 4. TEST ADD-TO-SAFE API - Invalid scenario (too many stars)
        try:
            request_data = {"stars": 100}
            response = self.session.post(f"{BASE_URL}/progress/add-to-safe", json=request_data)
            
            if response.status_code == 400:
                # This should fail, but check error message format
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        if "error" in error_data or "message" in error_data or "detail" in error_data:
                            error_msg = error_data.get("error", error_data.get("message", error_data.get("detail", "")))
                            if isinstance(error_msg, str) and len(error_msg) > 0:
                                self.log_test("4. Add-to-Safe API (Invalid) - Error Format", True, 
                                            f"✅ Proper error message: {error_msg}")
                                success_count += 1
                            else:
                                self.log_test("4. Add-to-Safe API (Invalid) - Error Format", False, 
                                            f"❌ Error message not string: {error_msg}")
                        else:
                            self.log_test("4. Add-to-Safe API (Invalid) - Error Format", False, 
                                        f"❌ No error/message/detail field: {error_data}")
                    else:
                        self.log_test("4. Add-to-Safe API (Invalid) - Error Format", False, 
                                    f"❌ Error response not JSON object: {error_data}")
                except:
                    self.log_test("4. Add-to-Safe API (Invalid) - Error Format", False, 
                                f"❌ Non-JSON error response: {response.text}")
            else:
                self.log_test("4. Add-to-Safe API (Invalid) - Error Format", False, 
                            f"❌ Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("4. Add-to-Safe API (Invalid) - Error Format", False, f"❌ Exception: {str(e)}")
        
        # 5. TEST WITHDRAW-FROM-SAFE API - Valid scenario
        try:
            request_data = {"stars": 2}
            response = self.session.post(f"{BASE_URL}/progress/withdraw-from-safe", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response format
                if isinstance(data, dict):
                    expected_fields = ["stars_in_safe", "available_stars"]
                    missing_fields = [field for field in expected_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_test("5. Withdraw-from-Safe API (Valid)", True, 
                                    f"✅ Response format correct: {data}")
                        success_count += 1
                    else:
                        self.log_test("5. Withdraw-from-Safe API (Valid)", False, 
                                    f"❌ Missing fields: {missing_fields}. Response: {data}")
                else:
                    self.log_test("5. Withdraw-from-Safe API (Valid)", False, 
                                f"❌ Response not JSON object: {type(data)} - {data}")
            else:
                # Check error response format
                try:
                    error_data = response.json()
                    self.log_test("5. Withdraw-from-Safe API (Valid)", False, 
                                f"❌ API error: {error_data}")
                except:
                    self.log_test("5. Withdraw-from-Safe API (Valid)", False, 
                                f"❌ Non-JSON error response: {response.text}")
        except Exception as e:
            self.log_test("5. Withdraw-from-Safe API (Valid)", False, f"❌ Exception: {str(e)}")
        
        # 6. TEST WITHDRAW-FROM-SAFE API - Invalid scenario (more than available)
        try:
            request_data = {"stars": 100}
            response = self.session.post(f"{BASE_URL}/progress/withdraw-from-safe", json=request_data)
            
            if response.status_code == 400:
                # Check error message format
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        if "error" in error_data or "message" in error_data or "detail" in error_data:
                            error_msg = error_data.get("error", error_data.get("message", error_data.get("detail", "")))
                            if isinstance(error_msg, str) and len(error_msg) > 0:
                                self.log_test("6. Withdraw-from-Safe API (Invalid) - Error Format", True, 
                                            f"✅ Proper error message: {error_msg}")
                                success_count += 1
                            else:
                                self.log_test("6. Withdraw-from-Safe API (Invalid) - Error Format", False, 
                                            f"❌ Error message not string: {error_msg}")
                        else:
                            self.log_test("6. Withdraw-from-Safe API (Invalid) - Error Format", False, 
                                        f"❌ No error/message/detail field: {error_data}")
                    else:
                        self.log_test("6. Withdraw-from-Safe API (Invalid) - Error Format", False, 
                                    f"❌ Error response not JSON object: {error_data}")
                except:
                    self.log_test("6. Withdraw-from-Safe API (Invalid) - Error Format", False, 
                                f"❌ Non-JSON error response: {response.text}")
            else:
                self.log_test("6. Withdraw-from-Safe API (Invalid) - Error Format", False, 
                            f"❌ Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("6. Withdraw-from-Safe API (Invalid) - Error Format", False, f"❌ Exception: {str(e)}")
        
        # 7. TEST REALISTIC USER SCENARIO - Edge cases
        try:
            # Get current progress
            response = self.session.get(f"{BASE_URL}/progress")
            if response.status_code == 200:
                progress = response.json()
                
                # Test moving exactly the available stars
                available_stars = progress.get("total_stars", 0)
                if available_stars > 0:
                    request_data = {"stars": available_stars}
                    response = self.session.post(f"{BASE_URL}/progress/add-to-safe", json=request_data)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and "stars_in_safe" in data:
                            self.log_test("7. Realistic Scenario - Move All Available", True, 
                                        f"✅ Successfully moved {available_stars} stars to safe")
                            success_count += 1
                        else:
                            self.log_test("7. Realistic Scenario - Move All Available", False, 
                                        f"❌ Invalid response format: {data}")
                    else:
                        try:
                            error_data = response.json()
                            self.log_test("7. Realistic Scenario - Move All Available", False, 
                                        f"❌ Failed to move stars: {error_data}")
                        except:
                            self.log_test("7. Realistic Scenario - Move All Available", False, 
                                        f"❌ Failed with non-JSON response: {response.text}")
                else:
                    self.log_test("7. Realistic Scenario - Move All Available", True, 
                                "✅ No stars available to move (expected)")
                    success_count += 1
            else:
                self.log_test("7. Realistic Scenario - Move All Available", False, 
                            f"❌ Failed to get progress: {response.status_code}")
        except Exception as e:
            self.log_test("7. Realistic Scenario - Move All Available", False, f"❌ Exception: {str(e)}")
        
        # 8. TEST RESPONSE SERIALIZATION - Check for [object Object] issue
        try:
            response = self.session.get(f"{BASE_URL}/progress")
            if response.status_code == 200:
                # Check if response can be properly serialized to JSON string
                data = response.json()
                json_str = json.dumps(data)
                
                # Check for [object Object] patterns
                if "[object Object]" in json_str:
                    self.log_test("8. Response Serialization Check", False, 
                                f"❌ Found [object Object] in response: {json_str}")
                else:
                    # Check if all values are JSON serializable
                    try:
                        json.loads(json_str)  # Try to parse it back
                        self.log_test("8. Response Serialization Check", True, 
                                    "✅ Response properly JSON serializable")
                        success_count += 1
                    except:
                        self.log_test("8. Response Serialization Check", False, 
                                    f"❌ Response not properly serializable: {json_str}")
            else:
                self.log_test("8. Response Serialization Check", False, 
                            f"❌ Failed to get progress: {response.status_code}")
        except Exception as e:
            self.log_test("8. Response Serialization Check", False, f"❌ Exception: {str(e)}")
        
        return success_count >= 6  # Expect at least 6 out of 8 tests to pass
    
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
    
    def run_test(self):
        """Run the star moving functionality test"""
        print("🚀 Starting Star Moving Functionality Test")
        print(f"🔗 Testing against: {BASE_URL}")
        print("=" * 60)
        
        try:
            success = self.test_star_moving_functionality()
            
            # Cleanup
            self.cleanup_resources()
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 TEST SUMMARY")
            print("=" * 60)
            
            if success:
                print("✅ STAR MOVING FUNCTIONALITY TEST - PASSED")
            else:
                print("❌ STAR MOVING FUNCTIONALITY TEST - FAILED")
            
            # Detailed results
            print(f"\n📝 Detailed Results ({len(self.test_results)} individual tests):")
            passed_individual = sum(1 for result in self.test_results if result['success'])
            print(f"Individual Tests Passed: {passed_individual}/{len(self.test_results)}")
            print(f"Success Rate: {(passed_individual/len(self.test_results))*100:.1f}%")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print(f"\n❌ Failed Tests ({len(failed_tests)}):")
                for test in failed_tests:
                    print(f"   • {test['test']}: {test['details']}")
            
            return success
            
        except Exception as e:
            print(f"💥 CRITICAL ERROR: {str(e)}")
            return False

if __name__ == "__main__":
    tester = StarMovingTester()
    success = tester.run_test()
    exit(0 if success else 1)