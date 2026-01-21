"""Template manager for fetching and caching .gitignore templates from GitHub."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable, TypedDict

import requests


class TemplateData(TypedDict):
    """Type definition for template data."""

    name: str
    content: str
    description: str
    url: str


class TemplateManager:
    """Manages .gitignore templates from GitHub's gitignore repository."""

    CACHE_DIR = Path.home() / ".gno"
    TEMPLATES_FILE = CACHE_DIR / "templates.json"
    GITHUB_API = "https://api.github.com/repos/github/gitignore/contents"

    def __init__(self, progress_callback: Callable[[str], None] | None = None) -> None:
        """Initialize the template manager."""
        self.templates: dict[str, TemplateData] = {}
        self.progress_callback = progress_callback
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _log(self, message: str) -> None:
        """Log a progress message."""
        if self.progress_callback:
            self.progress_callback(message)

    def _request(
        self, url: str, retries: int = 3, timeout: int = 30
    ) -> requests.Response:
        """Make a request with retry logic."""
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt < retries - 1:
                    wait = 2**attempt
                    self._log(f"Retry {attempt + 1}/{retries} in {wait}s...")
                    time.sleep(wait)
                else:
                    raise e
        raise requests.RequestException("Request failed")

    def fetch_templates(self) -> bool:
        """Fetch all .gitignore templates from GitHub."""
        try:
            self.templates = {}

            self._log("Fetching root templates...")
            response = self._request(self.GITHUB_API)
            self._process_response(response.json())

            self._log("Fetching global templates...")
            response = self._request(f"{self.GITHUB_API}/Global")
            self._process_response(response.json(), prefix="Global/")

            self._log("Fetching community templates...")
            response = self._request(f"{self.GITHUB_API}/community")
            self._process_response(response.json(), prefix="community/", recurse=True)

            self._log(f"Caching {len(self.templates)} templates...")
            self._save_cache()
            return True
        except requests.RequestException as e:
            self._log(f"Error: {e}")
            return False

    def _process_response(
        self, items: list[dict], prefix: str = "", recurse: bool = False
    ) -> None:
        """Process GitHub API response and fetch template contents."""
        for item in items:
            if item["type"] == "dir" and recurse:
                try:
                    self._log(f"  Fetching {prefix}{item['name']}/...")
                    resp = self._request(item["url"])
                    self._process_response(
                        resp.json(), prefix=f"{prefix}{item['name']}/", recurse=True
                    )
                except requests.RequestException:
                    continue
                continue

            if item["type"] != "file" or not item["name"].endswith(".gitignore"):
                continue

            name = item["name"].replace(".gitignore", "")
            display_name = f"{prefix}{name}" if prefix else name
            self._log(f"  Fetching {display_name}...")

            try:
                resp = self._request(item["download_url"], retries=2, timeout=10)
                content = resp.text
            except requests.RequestException:
                self._log(f"  Failed to fetch {display_name}")
                continue

            self.templates[display_name.lower()] = {
                "name": display_name,
                "content": content,
                "description": f"{name} gitignore patterns",
                "url": item["html_url"],
            }

    def _save_cache(self) -> None:
        """Save templates to the cache file."""
        with open(self.TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.templates, f, indent=2)

    def load_cache(self) -> bool:
        """Load templates from the cache file."""
        if not self.TEMPLATES_FILE.exists():
            return False
        try:
            with open(self.TEMPLATES_FILE, encoding="utf-8") as f:
                self.templates = json.load(f)
            return True
        except (json.JSONDecodeError, OSError):
            return False

    def ensure_templates(self) -> bool:
        """Ensure templates are available, loading from cache or fetching."""
        return self.load_cache() or self.fetch_templates()

    def get_template(self, name: str) -> TemplateData | None:
        """Get a specific template by name (case-insensitive)."""
        return self.templates.get(name.lower())

    def get_all_templates(self) -> list[TemplateData]:
        """Get all templates sorted by name."""
        return sorted(self.templates.values(), key=lambda t: t["name"].lower())

    def search_templates(self, query: str) -> list[TemplateData]:
        """Search templates by name."""
        q = query.lower()
        results = []

        for t in self.templates.values():
            name = t["name"].lower()
            if name == q:
                results.append((0, t))
            elif name.startswith(q):
                results.append((1, t))
            elif q in name:
                results.append((2, t))

        results.sort(key=lambda x: (x[0], x[1]["name"].lower()))
        return [t for _, t in results]
