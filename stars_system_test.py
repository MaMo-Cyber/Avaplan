#!/usr/bin/env python3
"""
Focused Stars System Fixes Test - German Review Request
Tests the specific scenarios requested for Sternen-System-Fixes validation
"""

import requests
import json

BASE_URL = "https://7bcca722-bd3a-4927-8afe-4fd31ad54c91.preview.emergentagent.com/api"

def log_test(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   Details: {details}")
    print()

def get_progress():
    """Get current progress state"""
    response = requests.get(f"{BASE_URL}/progress")
    if response.status_code == 200:
        return response.json()
    return None

def main():
    print("⭐ Testing Sternen-System-Fixes (Stars System Fixes) - German Review Request")
    print("=" * 80)
    
    # Reset all stars to start clean (including safe)
    print("🔄 Resetting all stars for clean test start...")
    response = requests.post(f"{BASE_URL}/progress/reset-all-stars")
    if response.status_code == 200:
        # Verify clean state
        progress = get_progress()
        if progress and progress.get("total_stars") == 0 and progress.get("stars_in_safe") == 0 and progress.get("available_stars") == 0:
            log_test("Reset All Stars (Setup)", True, "All stars reset for clean test start")
        else:
            log_test("Reset All Stars (Setup)", False, f"Not completely clean: {progress}")
            return
    else:
        log_test("Reset All Stars (Setup)", False, f"Status code: {response.status_code}")
        return
    
    # Create test tasks
    print("📝 Creating test tasks...")
    task1_data = {"name": "Hausaufgaben machen"}
    task2_data = {"name": "Zimmer aufräumen"}
    
    response1 = requests.post(f"{BASE_URL}/tasks", json=task1_data)
    response2 = requests.post(f"{BASE_URL}/tasks", json=task2_data)
    
    if response1.status_code != 200 or response2.status_code != 200:
        log_test("Create Test Tasks", False, "Failed to create test tasks")
        return
    
    task1_id = response1.json()["id"]
    task2_id = response2.json()["id"]
    log_test("Create Test Tasks", True, f"Created tasks: {task1_id[:8]}..., {task2_id[:8]}...")
    
    # **1. Stars Validation Test: Create 5 stars through tasks**
    print("🌟 Test 1: Stars Validation Test - Creating 5 stars through tasks")
    
    # Task 1: 2 stars on Monday, 1 star on Tuesday = 3 stars
    # Task 2: 2 stars on Wednesday = 2 stars
    # Total = 5 stars
    star_updates = [
        (task1_id, "monday", 2),
        (task1_id, "tuesday", 1), 
        (task2_id, "wednesday", 2)
    ]
    
    for task_id, day, stars in star_updates:
        response = requests.post(f"{BASE_URL}/stars/{task_id}/{day}?stars={stars}")
        if response.status_code != 200:
            log_test(f"Add {stars} stars on {day}", False, f"Status code: {response.status_code}")
            return
    
    progress = get_progress()
    if progress and progress.get("total_stars") == 5:
        log_test("Create 5 Task Stars", True, f"Successfully created 5 task stars")
    else:
        log_test("Create 5 Task Stars", False, f"Expected 5 stars, got {progress.get('total_stars') if progress else 'None'}")
        return
    
    # Try to move 10 stars to safe (should fail)
    print("❌ Test 2: Try to move 10 stars to safe (should fail)")
    response = requests.post(f"{BASE_URL}/progress/add-to-safe?stars=10")
    if response.status_code == 400:
        log_test("Move 10 Stars Validation (Should Fail)", True, "Correctly rejected moving 10 stars (only 5 available)")
    else:
        log_test("Move 10 Stars Validation (Should Fail)", False, f"Should have failed with 400, got {response.status_code}")
    
    # Try to move 3 stars to safe (should work)
    print("✅ Test 3: Try to move 3 stars to safe (should work)")
    response = requests.post(f"{BASE_URL}/progress/add-to-safe?stars=3")
    if response.status_code == 200:
        progress = response.json()
        if progress.get("stars_in_safe") == 3 and progress.get("total_stars") == 2:
            log_test("Move 3 Stars to Safe (Should Work)", True, f"Successfully moved 3 stars to safe, 2 remaining in total_stars")
        else:
            log_test("Move 3 Stars to Safe (Should Work)", False, f"Incorrect star distribution: safe={progress.get('stars_in_safe')}, total={progress.get('total_stars')}")
    else:
        log_test("Move 3 Stars to Safe (Should Work)", False, f"Status code: {response.status_code}")
    
    # **2. Safe Transfer Validation Test: Add more stars to get 8 total**
    print("🔒 Test 4: Safe Transfer Validation Test - Adding more stars to get 8 total")
    
    # We currently have 2 task stars remaining after moving 3 to safe
    # Add 6 more stars to reach 8 total task stars
    additional_stars = [
        (task1_id, "thursday", 2),
        (task1_id, "friday", 2),
        (task2_id, "saturday", 2)
    ]
    
    for task_id, day, stars in additional_stars:
        response = requests.post(f"{BASE_URL}/stars/{task_id}/{day}?stars={stars}")
        if response.status_code != 200:
            log_test(f"Add {stars} stars on {day}", False, f"Status code: {response.status_code}")
            return
    
    progress = get_progress()
    expected_total = 2 + 6  # 2 remaining + 6 new = 8 task stars
    if progress and progress.get("total_stars") == expected_total:
        log_test("Create 8 Task Stars Total", True, f"Successfully have {expected_total} task stars")
    else:
        log_test("Create 8 Task Stars Total", False, f"Expected {expected_total} task stars, got {progress.get('total_stars') if progress else 'None'}")
        print(f"   Current state: {progress}")
        # Continue with the test using actual values
        expected_total = progress.get("total_stars") if progress else 0
    
    # Try to put 12 stars in safe (should error 400)
    print("❌ Test 5: Try to put 12 stars in safe (should error 400)")
    response = requests.post(f"{BASE_URL}/progress/add-to-safe?stars=12")
    if response.status_code == 400:
        log_test("Add 12 Stars to Safe (Should Fail)", True, f"Correctly rejected adding 12 stars to safe (only {expected_total} available)")
    else:
        log_test("Add 12 Stars to Safe (Should Fail)", False, f"Should have failed with 400, got {response.status_code}")
    
    # Try to put 5 stars in safe (should work)
    print("✅ Test 6: Try to put 5 stars in safe (should work)")
    response = requests.post(f"{BASE_URL}/progress/add-to-safe?stars=5")
    if response.status_code == 200:
        progress = response.json()
        expected_safe = 3 + 5  # Previous 3 + new 5 = 8
        expected_remaining = expected_total - 5  # Should be 3 remaining
        if progress.get("stars_in_safe") == expected_safe and progress.get("total_stars") == expected_remaining:
            log_test("Add 5 Stars to Safe (Should Work)", True, f"Successfully added 5 more stars to safe (total safe: {expected_safe}, remaining task: {expected_remaining})")
        else:
            log_test("Add 5 Stars to Safe (Should Work)", False, f"Incorrect distribution: safe={progress.get('stars_in_safe')}, total={progress.get('total_stars')}")
            print(f"   Expected: safe={expected_safe}, total={expected_remaining}")
            print(f"   Current state: {progress}")
    else:
        log_test("Add 5 Stars to Safe (Should Work)", False, f"Status code: {response.status_code}")
    
    # **3. Weekly Reset Test: Test that safe stars are preserved**
    print("🔄 Test 7: Weekly Reset Test - Safe stars should be preserved")
    
    # Get state before reset
    progress_before = get_progress()
    print(f"   Before reset: total={progress_before.get('total_stars')}, safe={progress_before.get('stars_in_safe')}, available={progress_before.get('available_stars')}")
    
    response = requests.post(f"{BASE_URL}/progress/reset")
    if response.status_code == 200:
        progress_after = get_progress()
        print(f"   After reset: total={progress_after.get('total_stars')}, safe={progress_after.get('stars_in_safe')}, available={progress_after.get('available_stars')}")
        
        if (progress_after.get("total_stars") == 0 and 
            progress_after.get("available_stars") == 0 and 
            progress_after.get("stars_in_safe") == progress_before.get("stars_in_safe")):
            log_test("Weekly Reset (Safe Stars Preserved)", True, "Safe stars preserved during weekly reset")
        else:
            log_test("Weekly Reset (Safe Stars Preserved)", False, f"Incorrect state after reset: total={progress_after.get('total_stars')}, available={progress_after.get('available_stars')}, safe={progress_after.get('stars_in_safe')}")
            print(f"   Expected safe to remain: {progress_before.get('stars_in_safe')}, got: {progress_after.get('stars_in_safe')}")
    else:
        log_test("Weekly Reset (Safe Stars Preserved)", False, f"Reset failed: {response.status_code}")
    
    # **4. Safe Withdrawal Test: Withdraw 3 stars from safe**
    print("💰 Test 8: Safe Withdrawal Test - Withdraw 3 stars from safe")
    
    response = requests.post(f"{BASE_URL}/progress/withdraw-from-safe?stars=3")
    if response.status_code == 200:
        progress = response.json()
        # Calculate expected values based on current safe amount
        expected_safe = progress_after.get("stars_in_safe") - 3 if progress_after else 0
        expected_available = 3
        if progress.get("stars_in_safe") == expected_safe and progress.get("available_stars") == expected_available:
            log_test("Safe Withdrawal Test", True, f"Successfully withdrew 3 stars from safe (safe: {expected_safe}, available: {expected_available})")
        else:
            log_test("Safe Withdrawal Test", False, f"Incorrect withdrawal result: safe={progress.get('stars_in_safe')}, available={progress.get('available_stars')}")
            print(f"   Expected: safe={expected_safe}, available={expected_available}")
    else:
        log_test("Safe Withdrawal Test", False, f"Status code: {response.status_code}")
    
    # **5. Complete Workflow Test: Task stars → Safe → Available → Rewards → Weekly Reset**
    print("🔄 Test 9: Complete Workflow Test - Full cycle with safe preservation")
    
    # Add 2 more task stars
    response = requests.post(f"{BASE_URL}/stars/{task1_id}/sunday?stars=2")
    if response.status_code == 200:
        progress = get_progress()
        print(f"   After adding 2 task stars: total={progress.get('total_stars')}, safe={progress.get('stars_in_safe')}, available={progress.get('available_stars')}")
        
        # Move 1 star to safe
        response = requests.post(f"{BASE_URL}/progress/add-to-safe?stars=1")
        if response.status_code == 200:
            progress = get_progress()
            print(f"   After moving 1 to safe: total={progress.get('total_stars')}, safe={progress.get('stars_in_safe')}, available={progress.get('available_stars')}")
            
            # Withdraw 2 stars from safe to available
            response = requests.post(f"{BASE_URL}/progress/withdraw-from-safe?stars=2")
            if response.status_code == 200:
                progress_before_reset = get_progress()
                print(f"   After withdrawing 2 from safe: total={progress_before_reset.get('total_stars')}, safe={progress_before_reset.get('stars_in_safe')}, available={progress_before_reset.get('available_stars')}")
                
                # Do weekly reset
                response = requests.post(f"{BASE_URL}/progress/reset")
                if response.status_code == 200:
                    progress_after_reset = get_progress()
                    print(f"   After weekly reset: total={progress_after_reset.get('total_stars')}, safe={progress_after_reset.get('stars_in_safe')}, available={progress_after_reset.get('available_stars')}")
                    
                    # Safe stars should be preserved, others reset
                    if (progress_after_reset.get("total_stars") == 0 and
                        progress_after_reset.get("available_stars") == 0 and
                        progress_after_reset.get("stars_in_safe") == progress_before_reset.get("stars_in_safe")):
                        log_test("Complete Workflow Test", True, "Complete workflow with safe preservation works correctly")
                    else:
                        log_test("Complete Workflow Test", False, f"Workflow failed: safe should be preserved but got different values")
                else:
                    log_test("Complete Workflow Test", False, "Failed to reset in workflow test")
            else:
                log_test("Complete Workflow Test", False, "Failed to withdraw stars in workflow test")
        else:
            log_test("Complete Workflow Test", False, "Failed to add stars to safe in workflow test")
    else:
        log_test("Complete Workflow Test", False, "Failed to add task stars in workflow test")
    
    # Cleanup
    print("🧹 Cleaning up test tasks...")
    requests.delete(f"{BASE_URL}/tasks/{task1_id}")
    requests.delete(f"{BASE_URL}/tasks/{task2_id}")
    
    print("\n" + "=" * 80)
    print("🎯 STERNEN-SYSTEM-FIXES TESTING COMPLETED!")
    print("All critical star system validation scenarios have been tested.")
    print("=" * 80)

if __name__ == "__main__":
    main()