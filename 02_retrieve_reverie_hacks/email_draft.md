# Email Draft: Reverie Hacks 2026 Sponsor Perks & Setup Guides

---

**Subject:** [Reverie Hacks 2026] Sponsor Access Codes & AI Setup Guides (Wolfram|One & Featherless.ai)

**To:** `[Your Email / Team Members]`

---

### Body:

Hi Team,

Here are the official sponsor access links, redemption codes, and API setup instructions for **Reverie Hacks 2026**:

---

### 1. 🧮 Wolfram|One & Wolfram API (1 Month Free Access)
* **Redemption URL:** https://account.wolfram.com/redeem/REVHACKS26
* **Promo Code:** `REVHACKS26`
* **What's included:** Full desktop & cloud access to Wolfram|One, Wolfram API, instant web app deployment, and cloud credits.
* **How to activate:**
  1. Go to https://account.wolfram.com/redeem/REVHACKS26
  2. Sign in or create a Wolfram ID.
  3. Download the desktop app from the Downloads section and enter your activation key.
  4. Instant APIs guide: Documentation Center > Cloud and Deployment > Instant APIs.
* **Account details / Credits:** https://account.wolfram.com/products

---

### 2. 🪶 Featherless.ai Serverless LLM Platform (1 Month Free Premium - $25 Value)
* **Promo Code:** `REVERIE26`
* **Website:** https://featherless.ai
* **What's included:** Unlimited inference on 10,000+ open-source models (DeepSeek-V3.2, MiniMax-M2.5, Kimi-K2.5, GLM-5, Mistral-Nemo, Qwen 2.5/3, Llama 3.3), up to 4 concurrent connections, and up to 32k context.
* **How to activate:**
  1. Sign up on Featherless.ai and enter promo code `REVERIE26` at checkout.
  2. Generate your API key: Top Right Profile > API Keys > New API Key.
  3. Explore models: https://featherless.ai/models

#### 💻 Quick Python API Call (OpenAI SDK Compatible):
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key="YOUR_FEATHERLESS_API_KEY"
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[{"role": "user", "content": "Hello Reverie Hacks!"}]
)

print(response.choices[0].message.content)
```

#### 🛠️ Tool & IDE Integration Guides:
* **Compatible with:** Cursor, Cline, Roo Code, Aider, n8n, Dify.
* **Docs & Guides:** https://featherless.ai/docs/application-guides

---

Happy Hacking! 🚀
Reverie Hacks 2026 Team
