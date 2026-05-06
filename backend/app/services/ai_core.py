import os
import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class AICore:
    """
    AI Reasoning Layer using Llama-3.3-70b on Groq.
    Cross-references all assets to detect fraud patterns.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None
        if GROQ_AVAILABLE and self.api_key:
            self.client = Groq(api_key=self.api_key)

    async def analyze(self, asset_data: Dict, user_prompt: Optional[str] = None) -> Dict:
        """
        Main analysis pipeline - cross-reference all assets for fraud detection.
        """
        if not self.client:
            return {
                "verdict": "CRITICAL_RISK",
                "score": 0,
                "summary": "API key not configured. Set GROQ_API_KEY environment variable.",
                "evidence": [
                    {"type": "URL", "detail": "Groq API key missing", "severity": "critical"}
                ],
                "recommended_action": "Configure GROQ_API_KEY to enable analysis.",
            }

        start_time = datetime.now()

        # Build analysis prompt
        prompt = self._build_analysis_prompt(asset_data, user_prompt)

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": """You are Guardian LPU, an expert fraud detection AI. Your job is to analyze digital assets for scams, phishing, and fraud.

RULES:
1. Be aggressive in flagging suspicious patterns - better false positives than missed fraud
2. Cross-reference ALL provided data - inconsistencies between promise and reality are red flags
3. Look for: urgency tactics, unrealistic promises, domain mismatches, technical inconsistencies
4. Always respond in valid JSON format exactly matching the requested schema
5. Score 0-100 where 90+ = definitely fraudulent, 70-89 = highly suspicious, 40-69 = caution warranted, <40 = likely safe

VERDICT LEVELS:
- SAFE: Legitimate, no concerns
- LOW_RISK: Minor concerns, likely safe
- MEDIUM_RISK: Some red flags, exercise caution
- HIGH_RISK: Serious concerns, likely fraudulent
- CRITICAL_RISK: Confirmed fraud, avoid completely"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # Ensure all required fields exist
            result.setdefault("verdict", "MEDIUM_RISK")
            result.setdefault("score", 50)
            result.setdefault("summary", "Analysis incomplete")
            result.setdefault("evidence", [])
            result.setdefault("recommended_action", "Review manually")

            # Add processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result["processing_time_ms"] = int(processing_time)

            return result

        except Exception as e:
            return {
                "verdict": "MEDIUM_RISK",
                "score": 50,
                "summary": f"Analysis error: {str(e)}",
                "evidence": [{"type": "URL", "detail": f"AI processing error: {str(e)}", "severity": "warning"}],
                "recommended_action": "Please retry the analysis or review manually.",
            }

    def _build_analysis_prompt(self, asset_data: Dict, user_prompt: Optional[str]) -> str:
        """Construct detailed analysis prompt from asset data."""

        prompt_parts = []

        if user_prompt:
            prompt_parts.append(f"USER CONTEXT: {user_prompt}")

        prompt_parts.append("You are analyzing a website screenshot and data to detect scams. Be SPECIFIC about what you see.")

        # URL Analysis
        urls = asset_data.get("urls", [])
        if urls:
            prompt_parts.append(f"\n--- URL DATA ({len(urls)} URLS) ---")
            for url_data in urls:
                if "error" in url_data:
                    prompt_parts.append(f"\nURL: {url_data['url']} - ERROR: {url_data['error']}")
                    continue

                prompt_parts.append(f"\nURL: {url_data.get('final_url', url_data.get('url'))}")
                prompt_parts.append(f"Status: {url_data.get('status_code')}")
                prompt_parts.append(f"Title: {url_data.get('title', 'N/A')}")

                if url_data.get("redirects"):
                    prompt_parts.append(f"Redirects: {len(url_data['redirects'])} (chain: {' -> '.join([r['from'] for r in url_data['redirects'][:3]])})")

                if url_data.get("ssl_info"):
                    ssl = url_data["ssl_info"]
                    prompt_parts.append(f"SSL Valid: {ssl.get('valid', False)}")

                if url_data.get("whois_info"):
                    whois = url_data["whois_info"]
                    if "age_days" in whois:
                        prompt_parts.append(f"Domain Age: {whois['age_days']} days")

                if url_data.get("text_content"):
                    text = url_data["text_content"][:500]
                    prompt_parts.append(f"Content Sample: {text}...")

                if url_data.get("risk_indicators"):
                    prompt_parts.append("Risk Indicators:")
                    for ri in url_data["risk_indicators"]:
                        prompt_parts.append(f"  - [{ri.get('severity', 'info')}] {ri.get('type')}: {ri.get('detail')}")

                if url_data.get("vision_analysis"):
                    vision = url_data["vision_analysis"]
                    prompt_parts.append("\nSCREENSHOT ANALYSIS:")
                    if vision.get('page_description'):
                        prompt_parts.append(f"What the page shows: {vision['page_description']}")
                    if vision.get('brand_detected'):
                        prompt_parts.append(f"Brand detected: {vision['brand_detected']}")
                    if vision.get('findings'):
                        prompt_parts.append(f"Suspicious elements: {vision['findings']}")
                    if vision.get('legitimate_elements'):
                        prompt_parts.append(f"Legitimate elements: {vision['legitimate_elements']}")
                    prompt_parts.append(f"Visual deception score: {vision.get('deception_score', 0)}/100")

        # Document Analysis
        documents = asset_data.get("documents", [])
        if documents:
            prompt_parts.append(f"\n--- DOCUMENT DATA ({len(documents)} FILES) ---")
            for doc in documents:
                prompt_parts.append(f"\nFile: {doc.get('filename')}")
                prompt_parts.append(f"Type: {doc.get('content_type')}")

                if doc.get("metadata"):
                    meta = doc["metadata"]
                    prompt_parts.append(f"Pages: {meta.get('page_count')}, Title: {meta.get('title', 'N/A')}")

                if doc.get("text"):
                    text = doc["text"][:800]
                    prompt_parts.append(f"Content: {text}...")

        prompt_parts.append("\n--- INSTRUCTIONS ---")
        prompt_parts.append("""
CRITICAL: Analyze the content CAREFULLY. Do NOT flag innocent images/files as suspicious.

For IMAGES (not websites):
- If it's a photo, wallpaper, artwork, screenshot of a game, personal photo, etc → Mark as SAFE (score 0-20)
- ONLY flag as suspicious if image contains: fake login forms, crypto scam ads, phishing screenshots, fake bank pages, suspicious QR codes, scam messages

For WEBSITES:
- Analyze if it's actually a scam site or legitimate

Provide analysis in this EXACT JSON format:

{
    "verdict": "CRITICAL_RISK|HIGH_RISK|MEDIUM_RISK|LOW_RISK|SAFE",
    "score": 0-100,
    "summary": "Specific description. For innocent images: 'This appears to be a wallpaper/image file with no scam content'. For scams: 'This shows a fake Chase login page designed to steal passwords'",
    "evidence": [
        {"type": "DESCRIPTION", "detail": "What was analyzed (website, image file, etc)", "severity": "info"},
        {"type": "CONTENT", "detail": "What the content actually shows", "severity": "info"}
    ],
    "recommended_action": "Specific advice. Innocent images: 'No action needed - this is just an image file'. Scams: 'Do not interact with this content'"
}

SCORING:
- 0-20: Safe/innocent (images, photos, wallpapers, legitimate sites)
- 21-40: Low risk (minor concerns)
- 41-69: Medium risk (some suspicious elements)
- 70-89: High risk (likely scam)
- 90-100: Critical (confirmed scam, phishing, fraud)

DO NOT over-analyze innocent images. Most images are SAFE.""")

        return "\n".join(prompt_parts)
