"""Social scraping agent for GitHub and LeetCode with LinkedIn manual fallback."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

import httpx


class SocialScrapingAgent:
    """Collect public social signals for an employee profile."""

    GITHUB_API = "https://api.github.com"
    LEETCODE_API = "https://leetcode.com/graphql"

    def __init__(self, github_token: str | None = None) -> None:
        """Store optional GitHub auth for higher rate limits."""

        self.github_token = github_token or ""

    async def run(
        self,
        *,
        github_username: str | None,
        linkedin_url: str | None,
        leetcode_username: str | None,
        linkedin_manual: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Fetch all supported social sources and return a unified payload."""

        github_data = await self._fetch_github(github_username.strip()) if github_username and github_username.strip() else {}
        leetcode_data = await self._fetch_leetcode(leetcode_username.strip()) if leetcode_username and leetcode_username.strip() else {}
        linkedin_data = dict(linkedin_manual or {})
        if linkedin_url:
            linkedin_data.setdefault("profile_url", linkedin_url.strip())
        return {
            "github": github_data,
            "linkedin": linkedin_data,
            "leetcode": leetcode_data,
        }

    async def _fetch_github(self, username: str) -> dict[str, Any]:
        """Fetch public GitHub repositories and summarize them."""

        headers = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            repo_response = await client.get(
                f"{self.GITHUB_API}/users/{username}/repos",
                params={"per_page": 12, "sort": "updated"},
                headers=headers,
            )
            repo_response.raise_for_status()
            repos = repo_response.json()

            summarized_repos: list[dict[str, Any]] = []
            language_totals: Counter[str] = Counter()
            total_stars = 0

            for repo in repos:
                languages_response = await client.get(repo["languages_url"], headers=headers)
                languages = languages_response.json() if languages_response.is_success else {}
                contents_response = await client.get(f"{self.GITHUB_API}/repos/{username}/{repo['name']}/contents", headers=headers)
                contents = contents_response.json() if contents_response.is_success and isinstance(contents_response.json(), list) else []
                names = {str(item.get("name", "")).lower() for item in contents if isinstance(item, dict)}

                repo_languages = {language: int(bytes_used) for language, bytes_used in (languages or {}).items()}
                for language, bytes_used in repo_languages.items():
                    language_totals[language] += bytes_used

                total_stars += int(repo.get("stargazers_count", 0) or 0)
                summarized_repos.append(
                    {
                        "name": repo.get("name", ""),
                        "description": repo.get("description") or "",
                        "url": repo.get("html_url") or "",
                        "stars": int(repo.get("stargazers_count", 0) or 0),
                        "forks": int(repo.get("forks_count", 0) or 0),
                        "topics": list(repo.get("topics", []) or []),
                        "languages": list(repo_languages.keys()),
                        "language_bytes": repo_languages,
                        "has_tests": any(token in names for token in {"test", "tests", "__tests__"}),
                        "has_ci": ".github" in names or ".github/workflows" in names,
                        "last_commit": repo.get("pushed_at") or "",
                    }
                )

            return {
                "username": username,
                "repos": summarized_repos,
                "top_languages": [item[0] for item in language_totals.most_common(5)],
                "total_stars": total_stars,
                "last_synced_at": datetime.now(UTC).isoformat(),
            }

    async def _fetch_leetcode(self, username: str) -> dict[str, Any]:
        """Fetch public LeetCode stats via GraphQL."""

        query = """
        query getUserProfile($username: String!) {
          matchedUser(username: $username) {
            submitStats {
              acSubmissionNum {
                difficulty
                count
              }
            }
            profile {
              ranking
            }
            languageProblemCount {
              languageName
              problemsSolved
            }
          }
        }
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                self.LEETCODE_API,
                json={"query": query, "variables": {"username": username}},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            matched_user = (response.json().get("data", {}) or {}).get("matchedUser")
            if not matched_user:
                return {"username": username, "solved": {"easy": 0, "medium": 0, "hard": 0}, "languages_used": []}

            counts = {item.get("difficulty", "").lower(): int(item.get("count", 0) or 0) for item in matched_user.get("submitStats", {}).get("acSubmissionNum", [])}
            languages_used = [
                item.get("languageName", "")
                for item in matched_user.get("languageProblemCount", [])
                if int(item.get("problemsSolved", 0) or 0) > 0
            ]
            return {
                "username": username,
                "solved": {
                    "easy": counts.get("easy", 0),
                    "medium": counts.get("medium", 0),
                    "hard": counts.get("hard", 0),
                },
                "contest_rating": int(matched_user.get("profile", {}).get("ranking", 0) or 0),
                "languages_used": languages_used,
                "last_synced_at": datetime.now(UTC).isoformat(),
            }
