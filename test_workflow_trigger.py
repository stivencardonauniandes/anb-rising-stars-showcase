#!/usr/bin/env python3
"""
Simple test to trigger workflow execution
This file change should trigger GitHub Actions workflows
"""

print("🧪 Workflow trigger test")
print("This change should execute GitHub Actions workflows on feature/sonar branch")

# Test that imports work correctly
try:
    import sys
    import os
    sys.path.append('api')
    
    from api.models import User, Video, Vote
    from api.services.ranking_service import ranking_service
    from api.services.vote_service import vote_service
    
    print("✅ All imports successful")
    print("✅ Services are available")
    print("✅ Models are properly defined")
    
except Exception as e:
    print(f"❌ Import error: {e}")

if __name__ == "__main__":
    print("🎯 This is a test file to trigger GitHub Actions workflows")
    print("📅 Created to test feature/sonar branch workflow execution")
