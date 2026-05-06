import base64
from typing import Dict, List
from io import BytesIO

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class VisionEngine:
    """
    Vision analysis using Llama-3.2-11b-vision on Groq.
    Analyzes screenshots for UI deception and visual red flags.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.client = None
        if GROQ_AVAILABLE and api_key:
            self.client = Groq(api_key=api_key)

    async def analyze_screenshot(self, screenshot_b64: str, context: str = "") -> Dict:
        """
        Analyze a screenshot for visual deception indicators.
        """
        if not self.client:
            return {
                'error': 'Groq client not initialized. Set GROQ_API_KEY.',
                'findings': []
            }

        try:
            # Prepare the image for vision model
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this website screenshot. Describe exactly what you see.

URL context: {context or 'Unknown website'}

First, describe the page:
- What type of site is this? (bank login, crypto exchange, online store, social media, etc)
- What brand/company name do you see?
- What is the main action being asked? (login, sign up, invest, buy, download)
- What text/headlines are prominently displayed?

Then identify any red flags:
- Fake login that will steal passwords
- Fake brand logos (Chase, PayPal, MetaMask, Amazon, etc)
- "Act now" urgency tactics
- Promises of free money/crypto
- Poor grammar/spelling
- Fake trust badges

Respond in JSON format:
{{
    "page_description": "What the page claims to be (e.g., 'Chase bank login page', 'Crypto investment platform promising 500% returns')",
    "brand_detected": "actual brand name or 'unknown/fake'",
    "suspicious_elements": ["list specific suspicious things you spotted"],
    "legitimate_elements": ["list things that look genuine"],
    "confidence": "high/medium/low",
    "deception_score": 0-100,
    "notes": "detailed observations about the visual design"
}}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{screenshot_b64}"
                            }
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=messages,
                temperature=0.1,
                max_tokens=1024
            )

            content = response.choices[0].message.content

            # Parse JSON response (handle markdown code blocks)
            import json
            import re

            # Extract JSON from markdown if present
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)

            try:
                vision_result = json.loads(content)
            except json.JSONDecodeError:
                vision_result = {
                    "suspicious_elements": [content],
                    "confidence": "low",
                    "brand_detected": "unknown",
                    "deception_score": 50,
                    "notes": "Could not parse structured response"
                }

            return {
                'page_description': vision_result.get('page_description', ''),
                'findings': vision_result.get('suspicious_elements', []),
                'legitimate_elements': vision_result.get('legitimate_elements', []),
                'confidence': vision_result.get('confidence', 'low'),
                'brand_detected': vision_result.get('brand_detected', 'unknown'),
                'deception_score': vision_result.get('deception_score', 0),
                'notes': vision_result.get('notes', ''),
                'raw_response': content
            }

        except Exception as e:
            return {
                'error': str(e),
                'findings': [],
                'confidence': 'low',
                'deception_score': 0
            }

    async def batch_analyze(self, screenshots: List[Dict]) -> List[Dict]:
        """Analyze multiple screenshots."""
        results = []
        for screenshot in screenshots:
            result = await self.analyze_screenshot(
                screenshot.get('data', ''),
                screenshot.get('url', '')
            )
            results.append(result)
        return results
