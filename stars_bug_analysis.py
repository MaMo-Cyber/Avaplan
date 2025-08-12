#!/usr/bin/env python3
"""
Stars System Critical Bug Analysis - German Review Request
Documents the critical bug in the stars system logic
"""

import requests
import json

BASE_URL = "https://star-quest-app.preview.emergentagent.com/api"

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
    print("🐛 CRITICAL BUG ANALYSIS: Stars System Logic Issue")
    print("=" * 80)
    
    # Reset all stars
    response = requests.post(f"{BASE_URL}/progress/reset-all-stars")
    print("🔄 Reset all stars for clean test")
    
    # Create test task
    task_data = {"name": "Bug Test Task"}
    response = requests.post(f"{BASE_URL}/tasks", json=task_data)
    task_id = response.json()["id"]
    print(f"📝 Created test task: {task_id[:8]}...")
    
    # Add 5 stars total
    star_updates = [
        ("monday", 2),
        ("tuesday", 1), 
        ("wednesday", 2)
    ]
    
    print("\n🌟 Adding 5 stars from tasks:")
    for day, stars in star_updates:
        response = requests.post(f"{BASE_URL}/stars/{task_id}/{day}?stars={stars}")
        progress = get_progress()
        print(f"   After {day} +{stars}: total_stars={progress.get('total_stars')}")
    
    print(f"\n✅ Expected: total_stars=5 (2+1+2)")
    progress = get_progress()
    print(f"✅ Actual: total_stars={progress.get('total_stars')}")
    
    # Now move 3 stars to safe - THIS IS WHERE THE BUG OCCURS
    print(f"\n🔒 Moving 3 stars to safe...")
    print(f"   Before: total_stars={progress.get('total_stars')}, stars_in_safe={progress.get('stars_in_safe')}")
    
    response = requests.post(f"{BASE_URL}/progress/add-to-safe?stars=3")
    if response.status_code == 200:
        progress_after_safe = response.json()
        print(f"   Immediately after add-to-safe API: total_stars={progress_after_safe.get('total_stars')}, stars_in_safe={progress_after_safe.get('stars_in_safe')}")
        
        # Now call get_progress() which recalculates total_stars
        progress_after_get = get_progress()
        print(f"   After get_progress() recalculation: total_stars={progress_after_get.get('total_stars')}, stars_in_safe={progress_after_get.get('stars_in_safe')}")
        
        print(f"\n🐛 BUG IDENTIFIED:")
        print(f"   - add_to_safe reduces total_stars: {progress.get('total_stars')} → {progress_after_safe.get('total_stars')}")
        print(f"   - get_progress recalculates from daily records: {progress_after_safe.get('total_stars')} → {progress_after_get.get('total_stars')}")
        print(f"   - This creates inconsistent behavior!")
        
        print(f"\n💡 EXPECTED BEHAVIOR:")
        print(f"   - total_stars should ALWAYS be sum of daily star records (5)")
        print(f"   - stars_in_safe should track stars moved to safe (3)")
        print(f"   - total_stars should NOT be reduced when moving to safe")
        
        if progress_after_safe.get('total_stars') != progress_after_get.get('total_stars'):
            log_test("CRITICAL BUG: Inconsistent total_stars calculation", False, 
                    f"add_to_safe returns {progress_after_safe.get('total_stars')}, get_progress returns {progress_after_get.get('total_stars')}")
        else:
            log_test("Stars calculation consistency", True, "total_stars consistent between API calls")
    
    # Test the weekly reset behavior
    print(f"\n🔄 Testing weekly reset with current buggy behavior...")
    progress_before_reset = get_progress()
    print(f"   Before reset: total_stars={progress_before_reset.get('total_stars')}, stars_in_safe={progress_before_reset.get('stars_in_safe')}")
    
    response = requests.post(f"{BASE_URL}/progress/reset")
    if response.status_code == 200:
        progress_after_reset = get_progress()
        print(f"   After reset: total_stars={progress_after_reset.get('total_stars')}, stars_in_safe={progress_after_reset.get('stars_in_safe')}")
        
        if (progress_after_reset.get('total_stars') == 0 and 
            progress_after_reset.get('stars_in_safe') == progress_before_reset.get('stars_in_safe')):
            log_test("Weekly Reset (Safe Preservation)", True, "Safe stars preserved, task stars reset")
        else:
            log_test("Weekly Reset (Safe Preservation)", False, "Reset behavior incorrect")
    
    # Test withdrawal
    print(f"\n💰 Testing safe withdrawal...")
    response = requests.post(f"{BASE_URL}/progress/withdraw-from-safe?stars=2")
    if response.status_code == 200:
        progress = response.json()
        print(f"   After withdrawing 2: stars_in_safe={progress.get('stars_in_safe')}, available_stars={progress.get('available_stars')}")
        
        if progress.get('available_stars') == 2:
            log_test("Safe Withdrawal", True, "Withdrawal adds to available_stars correctly")
        else:
            log_test("Safe Withdrawal", False, f"Expected 2 available_stars, got {progress.get('available_stars')}")
    
    # Cleanup
    requests.delete(f"{BASE_URL}/tasks/{task_id}")
    
    print(f"\n" + "=" * 80)
    print(f"🚨 CRITICAL ISSUE SUMMARY:")
    print(f"The stars system has a fundamental logic bug in add_stars_to_safe():")
    print(f"1. It incorrectly reduces total_stars when moving stars to safe")
    print(f"2. get_progress() recalculates total_stars from daily records")
    print(f"3. This creates inconsistent state and violates the model definition")
    print(f"4. total_stars should represent 'Stars earned from tasks this week' (never reduced)")
    print(f"")
    print(f"🔧 RECOMMENDED FIX:")
    print(f"Remove line 559 in add_stars_to_safe(): progress['total_stars'] -= stars")
    print(f"total_stars should always equal sum of daily star records")
    print(f"=" * 80)

if __name__ == "__main__":
    main()