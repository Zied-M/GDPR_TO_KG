#!/usr/bin/env python3
"""Scrape pilot GDPR article source text for Sprint 1.2 KG grounding.

This adapts the LexiGen reference scraper in scripts/gdpr/scrapping_reference.py:
- fetch GDPR article index
- fetch article pages
- extract article structure
- parse paragraphs/subparts
- save structured CSV and JSON outputs
"""

from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "https://gdpr-info.eu/"
PILOT_ARTICLES = ["5", "6", "7", "12", "13", "14", "15", "17", "32", "46"]
REQUEST_SLEEP_SECONDS = 0.3
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "kg" / "source"
OUTPUT_CSV_PATH = OUTPUT_DIR / "gdpr_articles_structured.csv"
OUTPUT_JSON_PATH = OUTPUT_DIR / "gdpr_articles_structured.json"


def fetch_article_index(base_url: str = BASE_URL) -> dict[str, str]:
    """Fetch article URLs from the gdpr-info.eu index.

    Falls back to the stable gdpr-info.eu article URL pattern if the index
    layout changes but the individual article pages remain available.
    """
    response = requests.get(base_url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    toc = soup.find("div", class_="liste-inhaltsuebersicht dsgvo")

    article_urls: dict[str, str] = {}
    if toc:
        for art_div in toc.select("div.artikel"):
            link = art_div.find("a", href=True)
            number_span = art_div.find("span", class_="nummer")
            if not link or not number_span:
                continue
            match = re.search(r"(\d+)", number_span.get_text(" ", strip=True))
            if match:
                article_urls[match.group(1)] = urljoin(base_url, link["href"])

    for article_number in PILOT_ARTICLES:
        article_urls.setdefault(article_number, urljoin(base_url, f"art-{article_number}-gdpr/"))
    return article_urls


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_article_title(soup: BeautifulSoup, article_number: str) -> str:
    heading = soup.find("h1")
    if heading:
        text = clean_text(heading.get_text(" ", strip=True))
        text = re.sub(rf"^Art\.?\s*{re.escape(article_number)}\s*GDPR\s*[-–:]\s*", "", text, flags=re.I)
        return text or heading.get_text(" ", strip=True)
    return ""


def strip_leading_marker(text: str) -> str:
    return clean_text(re.sub(r"^\(?[a-z0-9]+\)?[\.\)]?\s*", "", text, count=1, flags=re.I))


def parse_paragraph_marker(text: str) -> tuple[str | None, str]:
    match = re.match(r"^\(?(\d+)\)?[\.\)]?\s*(.*)$", text)
    if match:
        return match.group(1), clean_text(match.group(2))
    return None, text


def parse_point_marker(text: str, fallback_index: int) -> tuple[str, str]:
    match = re.match(r"^(?:\(([a-z])\)|([a-z])[\.\)])\s*(.*)$", text, flags=re.I)
    if match:
        return (match.group(1) or match.group(2)).lower(), clean_text(match.group(3))
    return chr(96 + fallback_index), text


def extract_nested_list_items(
    list_tag: Tag,
    paragraph: str | None,
    parent_point: str | None = None,
) -> list[dict[str, str | None]]:
    # gdpr-info.eu wraps some point lists in one or more <ol> elements that carry no
    # <li> of their own (Art 14(2) is <ol><ol><ol><li>...; Art 6(1) and 6(3) are
    # <ol><ol><li>...). find_all("li", recursive=False) finds nothing on such a
    # wrapper, so the recursion dead-ends and the points are never emitted. Descend
    # through wrapper-only lists first. A list that already has direct <li> children
    # is left exactly as it was.
    while not list_tag.find_all("li", recursive=False):
        wrappers = list_tag.find_all(["ol", "ul"], recursive=False)
        if len(wrappers) != 1:
            break
        list_tag = wrappers[0]

    subparts: list[dict[str, str | None]] = []
    for index, item in enumerate(list_tag.find_all("li", recursive=False), start=1):
        raw_text = clean_text(item.get_text(" ", strip=True))
        nested = item.find(["ol", "ul"], recursive=False)

        if paragraph is None and parent_point is None:
            paragraph_id = str(index)
            subparts.append(
                {
                    "subpart_id": paragraph_id,
                    "paragraph": paragraph_id,
                    "point": None,
                    "text": raw_text,
                }
            )
            if nested:
                subparts.extend(extract_nested_list_items(nested, paragraph_id))
            continue

        point, text_without_marker = parse_point_marker(raw_text, index)
        point_path = f"{parent_point}.{point}" if parent_point else point
        subpart_id = f"{paragraph}.{point_path}" if paragraph else point_path
        subparts.append(
            {
                "subpart_id": subpart_id,
                "paragraph": paragraph,
                "point": point_path,
                "text": text_without_marker,
            }
        )

        if nested:
            subparts.extend(extract_nested_list_items(nested, paragraph, parent_point=point_path))
    return subparts


def fetch_article_structure(article_number: str, url: str) -> dict:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    entry = soup.find("div", class_="entry-content")
    subparts: list[dict[str, str | None]] = []

    if not entry:
        return {
            "article_number": article_number,
            "title": extract_article_title(soup, article_number),
            "url": url,
            "subparts": subparts,
        }

    current_paragraph: str | None = None
    generated_paragraph = 0

    for child in entry.children:
        if isinstance(child, Tag) and child.name == "div" and "empfehlung-erwaegungsgruende" in child.get("class", []):
            break

        if isinstance(child, Tag) and child.name == "p":
            text = clean_text(child.get_text(" ", strip=True))
            if not text:
                continue
            paragraph, paragraph_text = parse_paragraph_marker(text)
            if paragraph is None:
                generated_paragraph += 1
                paragraph = str(generated_paragraph)
                paragraph_text = text
            else:
                generated_paragraph = max(generated_paragraph, int(paragraph))
            current_paragraph = paragraph
            subparts.append(
                {
                    "subpart_id": paragraph,
                    "paragraph": paragraph,
                    "point": None,
                    "text": paragraph_text,
                }
            )

        elif isinstance(child, Tag) and child.name in {"ol", "ul"}:
            subparts.extend(extract_nested_list_items(child, current_paragraph))

    return {
        "article_number": article_number,
        "title": extract_article_title(soup, article_number),
        "url": url,
        "subparts": subparts,
    }


def write_outputs(articles: dict[str, dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_payload = {
        "metadata": {
            "source": "gdpr-info.eu",
            "articles": PILOT_ARTICLES,
            "status": "scraped_source_text",
        },
        "articles": articles,
    }
    OUTPUT_JSON_PATH.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "article_number",
                "article_url",
                "article_title",
                "subpart_id",
                "source_paragraph",
                "source_point",
                "subpart_text",
            ],
        )
        writer.writeheader()
        for article in articles.values():
            for subpart in article["subparts"]:
                writer.writerow(
                    {
                        "article_number": article["article_number"],
                        "article_url": article["url"],
                        "article_title": article["title"],
                        "subpart_id": subpart["subpart_id"],
                        "source_paragraph": subpart["paragraph"],
                        "source_point": subpart["point"],
                        "subpart_text": subpart["text"],
                    }
                )


def main() -> int:
    article_urls = fetch_article_index()
    articles: dict[str, dict] = {}

    for article_number in PILOT_ARTICLES:
        url = article_urls[article_number]
        article = fetch_article_structure(article_number, url)
        articles[article_number] = article
        print(f"Article {article_number} parsed with {len(article['subparts'])} subparts")
        time.sleep(REQUEST_SLEEP_SECONDS)

    write_outputs(articles)
    subpart_count = sum(len(article["subparts"]) for article in articles.values())
    print(f"Saved {len(articles)} articles and {subpart_count} subparts to {OUTPUT_DIR}")
    print(f"CSV: {OUTPUT_CSV_PATH}")
    print(f"JSON: {OUTPUT_JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
