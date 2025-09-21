#!/usr/bin/env python3
"""
Test runner script for E2E API tests.
Provides convenient ways to run different test suites.
"""
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run E2E API tests for Eibox")
    parser.add_argument(
        "--suite", 
        choices=["all", "auth", "oauth", "websocket", "utility", "integration"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true", 
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection based on suite
    test_files = {
        "all": "tests/",
        "auth": "tests/test_auth_endpoints.py",
        "oauth": "tests/test_oauth_endpoints.py", 
        "websocket": "tests/test_websocket_endpoints.py",
        "utility": "tests/test_utility_endpoints.py",
        "integration": "tests/test_integration_workflows.py"
    }
    
    cmd.append(test_files[args.suite])
    
    # Add options based on arguments
    if args.verbose:
        cmd.extend(["-v", "-s"])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    if args.html_report:
        cmd.extend(["--html=reports/test_report.html", "--self-contained-html"])
    
    # Add common options
    cmd.extend([
        "--tb=short",
        "--timeout=60",
        "-ra"  # Show summary of all test results
    ])
    
    print("🚀 Starting E2E API Tests for Eibox")
    print(f"Test Suite: {args.suite}")
    print(f"Options: verbose={args.verbose}, parallel={args.parallel}, coverage={args.coverage}")
    
    # Run the tests
    success = run_command(cmd, f"Running {args.suite} tests")
    
    if success:
        print("\n🎉 All tests passed!")
        if args.html_report:
            print("📊 HTML report generated: reports/test_report.html")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()