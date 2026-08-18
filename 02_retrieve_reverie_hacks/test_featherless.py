"""
Featherless.ai Test Script
Test your API connection to Featherless.ai models with OpenAI SDK or Requests.

Setup:
    pip install openai requests
    set FEATHERLESS_API_KEY=your_key_here
    python test_featherless.py
"""

import os
import requests
from openai import OpenAI

API_KEY = os.getenv("FEATHERLESS_API_KEY", "YOUR_API_KEY")
BASE_URL = "https://api.featherless.ai/v1"
MODEL_ID = "deepseek-ai/DeepSeek-V3-0324"  # Or "Qwen/Qwen2.5-7B-Instruct", "mistralai/Mistral-Nemo-Instruct-2407"

def test_via_openai_sdk():
    print("Testing via OpenAI SDK...")
    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": "You are an AI assistant for Reverie Hacks 2026."},
            {"role": "user", "content": "Say hello to the hackathon participants!"}
        ]
    )
    print("Response:\n", response.choices[0].message.content)

def test_via_requests():
    print("Testing via Python requests...")
    response = requests.post(
        url=f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": "Say hello to the hackathon participants!"}]
        }
    )
    print("Status:", response.status_code)
    print("Response:", response.json())

if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY":
        print("Please set your FEATHERLESS_API_KEY before running:")
        print("   set FEATHERLESS_API_KEY=<your_api_token>")
    else:
        test_via_openai_sdk()
