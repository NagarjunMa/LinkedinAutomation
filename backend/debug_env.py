#!/usr/bin/env python3
"""
Debug script to check environment variables in Railway
Add this temporarily to your backend to debug Railway env vars
"""
import os
import sys

print("🔍 Railway Environment Debug")
print("=" * 50)

# Check critical environment variables
critical_vars = [
    'SQLALCHEMY_DATABASE_URI',
    'SUPABASE_URL',
    'SUPABASE_ANON_KEY',
    'SUPABASE_JWT_SECRET',
    'SECRET_KEY',
    'OPENAI_API_KEY'
]

print("Critical Environment Variables:")
for var in critical_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if 'SECRET' in var or 'KEY' in var or 'URI' in var:
            masked = value[:8] + '...' + value[-8:] if len(value) > 16 else '***'
            print(f"✅ {var}: {masked}")
        else:
            print(f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: NOT SET")

print("\n" + "=" * 50)
print("All Environment Variables:")
for key, value in sorted(os.environ.items()):
    if any(sensitive in key.upper() for sensitive in ['SECRET', 'KEY', 'PASSWORD', 'TOKEN']):
        masked = value[:4] + '***' + value[-4:] if len(value) > 8 else '***'
        print(f"{key}: {masked}")
    else:
        print(f"{key}: {value}")

print("\n" + "=" * 50)
print("Python Path and Working Directory:")
print(f"Python executable: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

if __name__ == "__main__":
    print("\n🚀 Running environment check...")