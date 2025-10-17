#!/usr/bin/env python3
"""
Script to run tests for the ANB Rising Stars Showcase API
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests with pytest"""
    print("🧪 Running ANB Rising Stars API Tests...")
    
    # Change to API directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_specific_test(test_file):
    """Run a specific test file"""
    print(f"🧪 Running specific test: {test_file}")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        f"tests/{test_file}", 
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running test {test_file}: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        exit_code = run_specific_test(test_file)
    else:
        # Run all tests
        exit_code = run_tests()
    
    sys.exit(exit_code)
