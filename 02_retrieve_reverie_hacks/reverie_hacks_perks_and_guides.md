# Reverie Hacks 2026 — Sponsor Resources & API Setup Guide

This document compiles the complete information, redemption codes, and setup instructions from the **Wolfram Research** and **Featherless.ai** sponsor packets for **Reverie Hacks 2026**.

---

## 1. Wolfram|One & Wolfram API

### 🎁 Sponsor Perk
- **Offer**: 1 Month Complimentary Full Access to Wolfram|One & Wolfram API.
- **Redemption Link**: [https://account.wolfram.com/redeem/REVHACKS26](https://account.wolfram.com/redeem/REVHACKS26)
- **Promo / Claim Code**: `REVHACKS26`

### 🚀 Getting Started
1. Visit [https://account.wolfram.com/redeem/REVHACKS26](https://account.wolfram.com/redeem/REVHACKS26).
2. Log in with your Wolfram ID or create an account with an active email address.
3. In the **Downloads** section, access software binaries and copy your activation key.
4. Download the desktop version and enter the activation key when prompted.
5. In the cloud interface, you can load the **"Things to Try"** live notebook to explore computation workflows.

### 🌐 Instant APIs & Deployment
- Deploy instant web apps and APIs directly from your notebook.
- Access documentation under **Cloud and Deployment > Instant APIs**.
- View account credits and cloud storage at: [https://account.wolfram.com/products](https://account.wolfram.com/products).
- Wolfram Language is also supported on Raspberry Pi and Arduino integrations.

### 📚 Additional Opportunities
- **Wolfram Summer Programs**: [http://education.wolfram.com/summer/](http://education.wolfram.com/summer/)
- **Mentorships & Careers**: [https://www.wolfram.com/company/careers](https://www.wolfram.com/company/careers)
- **Contact**: Cyrus Taylor, Wolfram Research, Inc. ([wolfram.com](https://www.wolfram.com))

---

## 2. Featherless.ai Serverless AI Platform

### 🎁 Sponsor Perk
- **Offer**: 1 Month Free **Feather Premium** ($25/mo tier, 100% off).
- **Promo Code**: `REVERIE26`
- **Features Included**:
  - Unlimited serverless inference across 10,000+ open-source AI models.
  - Access to flagship models: DeepSeek-V3.2, MiniMax-M2.5, Kimi-K2.5, GLM-5, Mistral-Nemo-Instruct, Qwen 2.5 / Qwen 3, Llama 3.3.
  - Up to **4 concurrent connections** and up to **32k context window**.
  - Capacity reservation model (no per-token metering surprise bills).

### 🚀 Setup in 3 Steps
1. **Sign Up**:
   - Go to [Featherless.ai](https://featherless.ai) and apply promo code **`REVERIE26`** at checkout for 100% discount.
2. **Generate API Key**:
   - Click your profile on the top right > **API Keys** > **New API Key**.
3. **Select Model & Connect**:
   - Explore models in the [Model Catalog](https://featherless.ai/models).
   - Base URL: `https://api.featherless.ai/v1`

---

## 3. Featherless API Quickstart Code

### Python (OpenAI SDK Compatible)
```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.environ.get("FEATHERLESS_API_KEY", "YOUR_API_KEY")
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[
        {"role": "system", "content": "You are a helpful hackathon assistant."},
        {"role": "user", "content": "Hello! Explain our hackathon architecture in 2 sentences."}
    ]
)

print(response.choices[0].message.content)
```

### Python (Requests)
```python
import requests

url = "https://api.featherless.ai/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "model": "deepseek-ai/DeepSeek-V3-0324",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

---

## 4. Concurrency & Rate Limits

| Model Size Tier | Concurrency Cost (Slots) | Example Models |
|---|:---:|---|
| **7B to 15B** | 1 | Qwen 2.5 7B, Llama 2 13B |
| **24B to 34B** | 2 | Qwen 32B Coder, Mistral 3 24B |
| **70B to 72B** | 4 | Llama 3.3 70B, Qwen 2.5 72B |
| **DeepSeek V3.2 / R1 / Kimi-K2.5** | 4 | Feather Premium Tier Only |

---

## 5. Troubleshooting Common Error Codes

| Status Code | Meaning | Resolution |
|:---:|---|---|
| **401** | `Unauthenticated` | API key not recognized. Verify token string or generate a new key. |
| **403** | `Unauthorized` | Model is gated. Visit the model page on Featherless, click **"Unlock Model"**, and accept license terms. |
| **500** | `Internal Server Error` | Unsupported request payload/parameters. Check API documentation. |
| **503** | `Service Unavailable` | Insufficient capacity / cold start model. Retry 3 times or check Featherless Discord. |

---

## 6. Developer Tool Integrations
Featherless can be plugged into your favorite IDE and agent workflows:
- **Coding Agents**: Cursor, Cline, Roo Code, Aider
- **Workflow Automation**: n8n, Dify
- **Documentation**: [https://featherless.ai/docs/application-guides](https://featherless.ai/docs/application-guides)
