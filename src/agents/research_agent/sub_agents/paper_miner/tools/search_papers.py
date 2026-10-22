"""Concord: open-access PDF links from OpenAlex and arXiv, replacing the Google Programmable Search call
(no key needed; responses are cached by concord.literature)."""
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

import requests

from concord.config import env
from concord.literature import _get


def search_papers(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search open literature (OpenAlex open-access works, arXiv) and return links to their PDFs.

    Args:
        query: The search query (e.g., 'Pt3Co nanoparticles EXAFS').
        max_results: Maximum URLs to return.

    Returns:
        dict with status ("ok" | "error"), query, urls (PDF links), total and an optional message.
    """
    max_results = max(1, min(int(max_results), 50))
    urls: List[str] = []
    try:
        params = {"search": query, "filter": "open_access.is_oa:true", "per_page": max_results, "select": "best_oa_location"}
        if key := env().get("OPENALEX_API_KEY"):
            params["api_key"] = key
        for w in _get("https://api.openalex.org/works", params, secret=("api_key",)).get("results", []):
            if url := (w.get("best_oa_location") or {}).get("pdf_url"):
                urls.append(url)
        feed = ET.fromstring(_get("https://export.arxiv.org/api/query",
                                  {"search_query": " AND ".join(f"all:{w}" for w in query.split()), "max_results": max_results}))
        for e in feed.findall("{http://www.w3.org/2005/Atom}entry"):
            urls.append(e.findtext("{http://www.w3.org/2005/Atom}id", "").replace("/abs/", "/pdf/"))
    except (requests.RequestException, ET.ParseError, ValueError) as exc:
        return {"status": "error", "query": query, "urls": urls, "total": len(urls), "message": f"{type(exc).__name__}: {exc}"}
    unique = list(dict.fromkeys(u for u in urls if u))[:max_results]
    return {"status": "ok", "query": query, "urls": unique, "total": len(unique)}
