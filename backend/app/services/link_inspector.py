import asyncio
import base64
import ssl
import socket
import whois
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse

try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class LinkInspector:
    """
    Advanced web link analysis using Playwright.
    Extracts DOM, meta-tags, SSL info, redirect chains, and screenshots.
    """

    def __init__(self):
        self.playwright = None
        self.browser = None

    async def initialize(self):
        """Initialize Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def cleanup(self):
        """Cleanup browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def inspect_url(self, url: str) -> Dict:
        """
        Comprehensive URL inspection.
        Returns metadata, content, screenshot, and security analysis.
        """
        if not PLAYWRIGHT_AVAILABLE:
            return self._fallback_inspection(url)

        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        )

        page = await context.new_page()

        try:
            # Capture redirect chain
            redirects = []
            final_url = url

            async def handle_route(route, request):
                if request.redirected_from:
                    redirects.append({
                        'from': request.redirected_from.url,
                        'to': request.url
                    })
                await route.continue_()

            await page.route("**/*", handle_route)

            # Navigate with timeout
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            final_url = page.url

            # Extract page data
            page_data = await self._extract_page_data(page)

            # Capture screenshot
            screenshot_bytes = await page.screenshot(type='jpeg', quality=80)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            # SSL and domain analysis
            domain_info = await self._analyze_domain(final_url)

            return {
                'url': url,
                'final_url': final_url,
                'status_code': response.status if response else None,
                'redirects': redirects,
                'title': page_data['title'],
                'meta_tags': page_data['meta'],
                'forms': page_data['forms'],
                'links': page_data['links'],
                'text_content': page_data['text'][:5000],
                'screenshot': screenshot_b64,
                'ssl_info': domain_info['ssl'],
                'whois_info': domain_info['whois'],
                'risk_indicators': self._identify_risk_indicators(
                    page_data, domain_info, redirects
                )
            }

        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'risk_indicators': [{'type': 'ACCESS_ERROR', 'detail': str(e)}]
            }
        finally:
            await context.close()

    async def _extract_page_data(self, page: 'Page') -> Dict:
        """Extract comprehensive page data."""
        return await page.evaluate('''() => {
            const meta = {};
            document.querySelectorAll('meta').forEach(m => {
                const name = m.getAttribute('name') || m.getAttribute('property');
                if (name) meta[name] = m.getAttribute('content');
            });

            const forms = Array.from(document.querySelectorAll('form')).map(f => ({
                action: f.action,
                method: f.method,
                hasPassword: !!f.querySelector('input[type="password"]'),
                inputs: Array.from(f.querySelectorAll('input')).map(i => i.name)
            }));

            const links = Array.from(document.querySelectorAll('a')).map(a => ({
                href: a.href,
                text: a.textContent.trim().slice(0, 100)
            })).slice(0, 20);

            return {
                title: document.title,
                meta: meta,
                forms: forms,
                links: links,
                text: document.body.innerText.slice(0, 10000)
            };
        }''')

    async def _analyze_domain(self, url: str) -> Dict:
        """Analyze domain SSL and WHOIS data."""
        parsed = urlparse(url)
        domain = parsed.netloc

        result = {'ssl': {}, 'whois': {}}

        # SSL Analysis
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    result['ssl'] = {
                        'valid': True,
                        'issuer': cert.get('issuer'),
                        'not_after': cert.get('notAfter'),
                        'subject': cert.get('subject')
                    }
        except Exception as e:
            result['ssl'] = {'valid': False, 'error': str(e)}

        # WHOIS Analysis
        try:
            w = whois.whois(domain)
            result['whois'] = {
                'registrar': w.registrar,
                'creation_date': str(w.creation_date) if w.creation_date else None,
                'expiration_date': str(w.expiration_date) if w.expiration_date else None,
                'age_days': self._calculate_domain_age(w.creation_date)
            }
        except Exception as e:
            result['whois'] = {'error': str(e)}

        return result

    def _calculate_domain_age(self, creation_date) -> Optional[int]:
        """Calculate domain age in days."""
        if not creation_date:
            return None
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        try:
            age = (datetime.now() - creation_date).days
            return age
        except:
            return None

    def _identify_risk_indicators(self, page_data: Dict, domain_info: Dict, redirects: List) -> List[Dict]:
        """Identify potential risk indicators."""
        indicators = []

        # Check for password forms
        password_forms = [f for f in page_data['forms'] if f.get('hasPassword')]
        if password_forms:
            indicators.append({
                'type': 'LOGIN_FORM',
                'severity': 'warning',
                'detail': f'Page contains {len(password_forms)} password input field(s)'
            })

        # Check for suspicious meta tags
        meta = page_data.get('meta', {})
        if any('verify' in k.lower() or 'verification' in k.lower() for k in meta.keys()):
            indicators.append({
                'type': 'META_VERIFICATION',
                'severity': 'info',
                'detail': 'Site has verification meta tags'
            })

        # Check redirects
        if len(redirects) > 2:
            indicators.append({
                'type': 'EXCESSIVE_REDIRECTS',
                'severity': 'warning',
                'detail': f'{len(redirects)} redirects detected in chain'
            })

        # Check domain age
        whois = domain_info.get('whois', {})
        age_days = whois.get('age_days')
        if age_days is not None:
            if age_days < 1:
                indicators.append({
                    'type': 'DOMAIN_AGE',
                    'severity': 'critical',
                    'detail': f'Domain registered today ({age_days} days old)'
                })
            elif age_days < 7:
                indicators.append({
                    'type': 'DOMAIN_AGE',
                    'severity': 'critical',
                    'detail': f'Domain very new ({age_days} days old)'
                })
            elif age_days < 30:
                indicators.append({
                    'type': 'DOMAIN_AGE',
                    'severity': 'warning',
                    'detail': f'Domain registered recently ({age_days} days old)'
                })

        # Check SSL
        ssl_info = domain_info.get('ssl', {})
        if not ssl_info.get('valid'):
            indicators.append({
                'type': 'SSL_ISSUE',
                'severity': 'warning',
                'detail': 'SSL certificate issue detected'
            })

        return indicators

    def _fallback_inspection(self, url: str) -> Dict:
        """Fallback when Playwright is not available."""
        return {
            'url': url,
            'error': 'Playwright not available - install with: pip install playwright && playwright install',
            'risk_indicators': []
        }
