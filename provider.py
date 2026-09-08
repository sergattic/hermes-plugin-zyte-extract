"""Zyte Extract API — paid URL-to-clean-text extraction backstop.

Added 2026-09-02: the owner's chosen paid alternative after evaluating
Diffbot (recurring free tier, wired separately as `diffbot-extract`) and
Zyte (genuinely paid, no free recurring tier) side by side. Zyte's
``/v1/extract`` endpoint with ``"article": true`` returns clean structured
JSON (``article.articleBody``) — live-tested 2026-09-02: 34,841 chars from
the same URL used to test every other extract backend that day (exa
44,869 / keenable 48,353 / jina 66,554 / diffbot 43,532) — smallest of the
five but still solid, comparable-quality output, not a broken fallback.

Why paid, and why last: $0.13 per 1,000 HTTP requests, no monthly
minimum, pure pay-as-you-go ($5 free trial credit on signup) — far
cheaper than Exa's $7/1k, but still a real per-call cost with no
subscription or recurring-free offset (unlike Diffbot's 10,000/month
recurring credit). Placed in the extract ladder ahead of exa (the
pricier paid option) but after every free rung, mirroring the same
cheaper-paid-before-pricier-paid logic already used in the SEARCH ladder
for brave ($5/1k) before exa ($7/1k).

Auth: HTTP Basic Auth with the API key as username, empty password (Zyte's
documented auth scheme — confirmed via a live test call). Reads
ZYTE_API_KEY from the environment (sourced via secrets.onepassword.env ->
op://<your-vault>/<item>/<field> in config.yaml — never stored in this
plugin or read from a raw secrets file).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)

_EXTRACT_URL = "https://api.zyte.com/v1/extract"
_DEFAULT_TIMEOUT = 60


class ZyteExtractProvider(WebSearchProvider):
    """Extract-only provider backed by Zyte's Extract API (paid)."""

    @property
    def name(self) -> str:
        return "zyte"

    @property
    def display_name(self) -> str:
        return "Zyte Extract API (paid, $0.13/1k)"

    def is_available(self) -> bool:
        from agent.web_search_provider import get_provider_env

        return bool(get_provider_env("ZYTE_API_KEY"))

    def supports_search(self) -> bool:
        # Zyte's product surface is extraction/scraping infrastructure, not
        # a general web search API — not implemented.
        return False

    def supports_extract(self) -> bool:
        return True

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        return {"success": False, "error": "Zyte is extract-only in this deployment (no web search API)."}

    def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        try:
            from tools.interrupt import is_interrupted

            if is_interrupted():
                return [{"url": u, "title": "", "content": "", "error": "Interrupted"} for u in urls]
        except Exception:
            pass

        from agent.web_search_provider import get_provider_env

        api_key = get_provider_env("ZYTE_API_KEY")
        if not api_key:
            return [{"url": u, "title": "", "content": "", "error": "ZYTE_API_KEY is not set"} for u in urls]

        try:
            import httpx
        except ImportError:
            return [{"url": u, "title": "", "content": "", "error": "httpx is not installed"} for u in urls]

        results: List[Dict[str, Any]] = []
        for url in urls:
            try:
                resp = httpx.post(
                    _EXTRACT_URL,
                    auth=(api_key, ""),
                    json={"url": url, "article": True},
                    timeout=_DEFAULT_TIMEOUT,
                )
                resp.raise_for_status()
                payload = resp.json()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                body = ""
                try:
                    body = exc.response.text[:200] if exc.response is not None else ""
                except Exception:
                    pass
                logger.warning("Zyte HTTP %d for %s: %s", status, url, body)
                results.append({"url": url, "title": "", "content": "", "error": f"HTTP {status}: {body}".rstrip()})
                continue
            except httpx.RequestError as exc:
                logger.warning("Zyte request error for %s: %s", url, exc)
                results.append({"url": url, "title": "", "content": "", "error": str(exc)})
                continue
            except (ValueError, TypeError) as exc:
                logger.warning("Zyte returned non-JSON for %s: %s", url, exc)
                results.append({"url": url, "title": "", "content": "", "error": "Invalid response format"})
                continue

            article = payload.get("article") if isinstance(payload, dict) else None
            if not isinstance(article, dict):
                results.append({"url": url, "title": "", "content": "", "error": "No extractable article content returned"})
                continue

            content = article.get("articleBody") or ""
            # Strip trailing anchor-link glyphs Zyte sometimes captures along
            # with a heading's own anchor icon (live-tested: "Coroutines and
            # tasks ¶" for a page whose real title has no such suffix).
            title = (article.get("headline") or "").strip().rstrip("¶#").strip()
            results.append({
                "url": article.get("canonicalUrl") or article.get("url") or url,
                "title": title,
                "content": content,
                "raw_content": content,
                "metadata": {"description": article.get("description") or ""},
            })
        return results
