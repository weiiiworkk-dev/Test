#!/usr/bin/env python3
"""Simple BBC News crawler.

Fetches BBC News homepage and outputs article metadata.
"""
from __future__ import annotations

import argparse
import json
from typing import Iterable
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

BBC_NEWS_URL = "https://www.bbc.com/news"
BBC_RSS_URL = "https://feeds.bbci.co.uk/news/rss.xml"


class BBCNewsCrawler:
    def __init__(self, base_url: str = BBC_NEWS_URL) -> None:
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/119.0 Safari/537.36"
                )
            }
        )

    def fetch(self) -> str:
        response = self.session.get(self.base_url, timeout=15)
        response.raise_for_status()
        return response.text

    def parse_articles(self, html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        articles: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for link in soup.select("a[href]"):
            href = link.get("href", "").strip()
            if not href:
                continue
            if not href.startswith("/news") and not href.startswith("https://www.bbc.com/news"):
                continue
            url = urljoin(self.base_url, href)
            if url in seen_urls:
                continue

            title = link.get_text(strip=True)
            if not title:
                continue

            seen_urls.add(url)
            articles.append({"title": title, "url": url})

        return articles

    def fetch_rss(self, rss_url: str = BBC_RSS_URL) -> list[dict[str, str]]:
        feed = feedparser.parse(rss_url)
        if feed.bozo:
            raise ValueError(f"Failed to parse RSS feed: {feed.bozo_exception}")

        items: list[dict[str, str]] = []
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue
            items.append(
                {
                    "title": title,
                    "url": link,
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                }
            )
        return items


def print_json(items: Iterable[dict[str, str]]) -> None:
    print(json.dumps(list(items), ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl BBC News headlines.")
    parser.add_argument(
        "--limit", type=int, default=20, help="Maximum number of articles to output"
    )
    parser.add_argument(
        "--rss-url", default=BBC_RSS_URL, help="RSS feed URL to crawl"
    )
    args = parser.parse_args()

    crawler = BBCNewsCrawler()
    try:
        articles = crawler.fetch_rss(args.rss_url)
    except Exception:
        html = crawler.fetch()
        articles = crawler.parse_articles(html)
    print_json(articles[: args.limit])


if __name__ == "__main__":
    main()
