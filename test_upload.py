#!/usr/bin/env python3
"""Test script to verify the /transcribe endpoint receives files"""
import requests
import io

# Create a dummy audio file (minimal WebM header)
dummy_audio = b'\x1a\x45\xdf\xa3' + b'\x00' * 100  # Minimal WebM header

files = {
    'file': ('test.webm', io.BytesIO(dummy_audio), 'audio/webm')
}

print("🧪 Testing /transcribe endpoint...")
print(f"📤 Sending {len(dummy_audio)} bytes...")

try:
    response = requests.post('http://localhost:8000/transcribe', files=files)
    print(f"📥 Response status: {response.status_code}")
    print(f"📄 Response: {response.text[:200]}...")
except Exception as e:
    print(f"❌ Error: {e}")

