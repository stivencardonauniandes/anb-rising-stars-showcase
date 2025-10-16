#!/usr/bin/env python3
"""
Optimized test runner for all tests at once
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def run_all_tests(parallel=False, coverage=True, verbose=True):
    """
    Run all tests efficiently in a single execution
    
    Args:
        parallel: Enable parallel execution with pytest-xdist
        coverage: Generate coverage reports
        verbose: Verbose output
    """
    print("🚀 ANB Rising Stars - Comprehensive Test Suite")
    print("=" * 50)
    
    # Change to API directory
    api_dir = Path(__file__).parent
    os.chdir(api_dir)
    
    # Base pytest command
    cmd = [sys.executable, "-m"]
    
    if coverage:
        cmd.extend(["coverage", "run", "-m"])
    
    cmd.extend(["pytest", "tests/"])
    
    # Test execution options
    test_options = [
        "-v" if verbose else "-q",
        "--tb=short",
        "--maxfail=0",  # Don't stop on first failure
        "--durations=10",  # Show 10 slowest tests
        "--strict-markers",
        "--strict-config", 
        "--disable-warnings",
        "--junitxml=pytest-report.xml"
    ]
    
    if parallel:
        # Enable parallel execution
        test_options.extend(["-n", "auto"])
        print("⚡ Parallel execution enabled")
    
    cmd.extend(test_options)
    
    # Display configuration
    print(f"📊 Test Configuration:")
    print(f"  • Working directory: {api_dir}")
    print(f"  • Coverage enabled: {coverage}")
    print(f"  • Parallel execution: {parallel}")
    print(f"  • Verbose output: {verbose}")
    print(f"  • Command: {' '.join(cmd)}")
    print()
    
    # Count test files
    test_files = list(Path("tests").glob("test_*.py"))
    print(f"📁 Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  • {test_file}")
    print()
    
    # Execute tests
    start_time = time.time()
    print("🧪 Starting test execution...")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False, text=True)
        execution_time = time.time() - start_time
        
        print("-" * 50)
        print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
        
        if result.returncode == 0:
            print("✅ All tests passed successfully!")
            
            if coverage:
                print("\n📈 Generating coverage reports...")
                
                # Coverage report
                subprocess.run([sys.executable, "-m", "coverage", "report", "--show-missing"], check=False)
                
                # XML report for CI/SonarQube
                subprocess.run([sys.executable, "-m", "coverage", "xml", "-o", "coverage.xml"], check=False)
                
                # HTML report for local viewing
                subprocess.run([sys.executable, "-m", "coverage", "html", "-d", "htmlcov"], check=False)
                
                print("✅ Coverage reports generated:")
                print("  • coverage.xml (for CI)")
                print("  • htmlcov/ (for local viewing)")
            
            print("\n🎉 Test suite execution completed successfully!")
            
        else:
            print("❌ Some tests failed!")
            print(f"Exit code: {result.returncode}")
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

def run_specific_category(category):
    """Run tests for a specific category using markers"""
    print(f"🎯 Running {category} tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        f"-m", category,
        "--maxfail=0",
        "--durations=5"
    ]
    
    try:
        result = subprocess.run(cmd, check=False, text=True)
        if result.returncode == 0:
            print(f"✅ All {category} tests passed!")
        else:
            print(f"❌ Some {category} tests failed!")
        return result.returncode
    except Exception as e:
        print(f"❌ Error running {category} tests: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run ANB Rising Stars test suite")
    parser.add_argument("--parallel", "-p", action="store_true", help="Enable parallel test execution")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--category", "-c", choices=["unit", "integration", "api", "vote", "ranking"], 
                       help="Run tests for specific category")
    
    args = parser.parse_args()
    
    if args.category:
        exit_code = run_specific_category(args.category)
    else:
        exit_code = run_all_tests(
            parallel=args.parallel,
            coverage=not args.no_coverage,
            verbose=not args.quiet
        )
    
    sys.exit(exit_code)
