from __future__ import annotations

import hashlib
import html
import json
import os
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

USER_AGENT = "ChinaTechXPoc/0.1 (+https://github.com/Creatiny/china-tech-x-poc)"
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean_text(value: str | None, limit: int = 1600) -> str:
    value = html.unescape(value or "")
    value = TAG_RE.sub(" ", value)
    value = WS_RE.sub(" ", value).strip()
    return value[:limit]


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _node_text(node: ET.Element, names: list[str]) -> str | None:
    for child in list(node):
        local = child.tag.rsplit("}", 1)[-1]
        if local in names and child.text:
            return child.text.strip()
    return None


def _atom_link(entry: ET.Element) -> str | None:
    for child in list(entry):
        if child.tag.rsplit("}", 1)[-1] == "link":
            href = child.attrib.get("href")
            rel = child.attrib.get("rel", "alternate")
            if href and rel in ("alternate", ""):
                return href
    return None


def parse_feed(body: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(body)
    items: list[dict[str, Any]] = []
    rss_items = [n for n in root.iter() if n.tag.rsplit("}", 1)[-1] == "item"]
    if rss_items:
        for n in rss_items:
            title = clean_text(_node_text(n, ["title"]), 500)
            link = _node_text(n, ["link"])
            guid = _node_text(n, ["guid", "id"]) or link
            desc = clean_text(_node_text(n, ["description", "encoded", "summary", "content"]))
            pub = _node_text(n, ["pubDate", "date", "published", "updated"])
            author = clean_text(_node_text(n, ["author", "creator"]), 200)
            if not title:
                continue
            items.append({
                "source_item_id": guid,
                "canonical_url": link,
                "title": title,
                "excerpt": desc,
                "author": author,
                "published_at": parse_datetime(pub),
            })
        return items

    atom_entries = [n for n in root.iter() if n.tag.rsplit("}", 1)[-1] == "entry"]
    for n in atom_entries:
        title = clean_text(_node_text(n, ["title"]), 500)
        link = _atom_link(n)
        entry_id = _node_text(n, ["id"]) or link
        desc = clean_text(_node_text(n, ["summary", "content"]))
        pub = _node_text(n, ["published", "updated"])
        author = ""
        for child in list(n):
            if child.tag.rsplit("}", 1)[-1] == "author":
                author = clean_text(_node_text(child, ["name"]), 200)
        if not title:
            continue
        items.append({
            "source_item_id": entry_id,
            "canonical_url": link,
            "title": title,
            "excerpt": desc,
            "author": author,
            "published_at": parse_datetime(pub),
        })
    return items


def _request(url: str, state: dict[str, Any] | None, *, accept: str | None = None) -> tuple[int, bytes, dict[str, str]]:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    if state:
        if state.get("etag"):
            headers["If-None-Match"] = state["etag"]
        if state.get("last_modified"):
            headers["If-Modified-Since"] = state["last_modified"]
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read(1_500_000), {
                "etag": r.headers.get("ETag") or "",
                "last_modified": r.headers.get("Last-Modified") or "",
            }
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return 304, b"", {}
        raise


def fetch_rss(source: dict[str, Any], state: dict[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, str], bool]:
    status, body, meta = _request(source["url"], state, accept="application/rss+xml, application/atom+xml, application/xml, text/xml, */*")
    if status == 304:
        return [], meta, True
    return parse_feed(body), meta, False


def fetch_github_releases(source: dict[str, Any], state: dict[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, str], bool]:
    repo = source["repo"]
    url = f"https://api.github.com/repos/{repo}/releases?per_page=10"
    headers_state = state
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if headers_state:
        if headers_state.get("etag"):
            headers["If-None-Match"] = headers_state["etag"]
        if headers_state.get("last_modified"):
            headers["If-Modified-Since"] = headers_state["last_modified"]
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            status = r.status
            body = r.read(1_500_000)
            meta = {"etag": r.headers.get("ETag") or "", "last_modified": r.headers.get("Last-Modified") or ""}
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return [], {}, True
        raise
    data = json.loads(body)
    out = []
    for rel in data:
        title = rel.get("name") or rel.get("tag_name") or f"Release {repo}"
        out.append({
            "source_item_id": str(rel.get("id") or rel.get("node_id") or rel.get("html_url")),
            "canonical_url": rel.get("html_url"),
            "title": clean_text(title, 500),
            "excerpt": clean_text(rel.get("body"), 1600),
            "author": ((rel.get("author") or {}).get("login") or ""),
            "published_at": parse_datetime(rel.get("published_at") or rel.get("created_at")),
        })
    return out, meta, False


def fetch_source(source: dict[str, Any], state: dict[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, str], bool]:
    kind = source.get("kind")
    if kind == "rss":
        return fetch_rss(source, state)
    if kind == "github_releases":
        return fetch_github_releases(source, state)
    raise ValueError(f"unsupported source kind: {kind}")


def fingerprint(source_id: str, item: dict[str, Any]) -> str:
    identity = item.get("source_item_id") or item.get("canonical_url") or f"{item.get('title','')}|{item.get('published_at','')}"
    return hashlib.sha256(f"{source_id}|{identity}".encode("utf-8", errors="ignore")).hexdigest()
