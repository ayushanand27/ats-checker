"""Fetch and extract job description text from a public URL."""

from __future__ import annotations

import re
import urllib.error
import urllib.request

_USER_AGENT = "ResumeMatch/1.0 (+https://github.com/ayushanand27/ats-checker)"
_MAX_BYTES = 500_000


def fetch_jd_from_url(url: str) -> str:
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read(_MAX_BYTES)
            charset = resp.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Could not fetch URL (HTTP {exc.code})") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Could not fetch URL: {exc.reason}") from exc

    html = raw.decode(charset, errors="replace")
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<(br|p|div|li|h[1-6])[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if len(text) < 80:
        raise ValueError("Fetched page had too little text — try paste instead")
    return text[:30000]
