#!/usr/bin/env python3
"""Build an allowlist Brave Goggle from a CSV exported from Google Sheets."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_SOURCE_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1fxu7W_IuWByV1wOSBg0emny4M-1RCS1W1mun_wTcIQY/edit?usp=sharing"
)


@dataclass(frozen=True)
class Site:
    row: int
    brand: str
    domain: str
    category: str
    url: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build goggles/my.goggle from a sheet CSV with a URL column."
    )
    parser.add_argument("source_csv", type=Path, help="CSV exported from the sheet's first tab")
    parser.add_argument("--goggle", type=Path, default=Path("goggles/my.goggle"))
    parser.add_argument("--domains-csv", type=Path, default=Path("data/allowed-sites.csv"))
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--name", default="Sheet Website Allowlist")
    parser.add_argument(
        "--description",
        default="Search only websites listed in the source Google Sheet first tab.",
    )
    return parser.parse_args()


def normalize_domain(url: str) -> str | None:
    candidate = url.strip()
    if not candidate:
        return None
    if "://" not in candidate:
        candidate = "https://" + candidate

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if "." not in host:
        return None
    return host


def read_sites(source_csv: Path) -> tuple[list[Site], int, list[Site], list[tuple[int, str, str]]]:
    rows = list(csv.DictReader(source_csv.open(newline="", encoding="utf-8-sig")))
    sites: list[Site] = []
    duplicate_sites: list[Site] = []
    bad_urls: list[tuple[int, str, str]] = []
    seen_domains: set[str] = set()
    blank_url_count = 0

    for row_index, row in enumerate(rows, start=2):
        brand = (row.get("Brand Name") or row.get("Brand") or "").strip()
        url = (row.get("URL") or row.get("Url") or row.get("url") or "").strip()
        category = (row.get("Category") or "").strip()

        if not url:
            blank_url_count += 1
            continue

        domain = normalize_domain(url)
        if domain is None:
            bad_urls.append((row_index, brand, url))
            continue

        site = Site(row=row_index, brand=brand, domain=domain, category=category, url=url)
        if domain in seen_domains:
            duplicate_sites.append(site)
            continue

        seen_domains.add(domain)
        sites.append(site)

    return sites, blank_url_count, duplicate_sites, bad_urls


def write_domains_csv(path: Path, sites: list[Site]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row", "brand", "domain", "category", "url"])
        for site in sites:
            writer.writerow([site.row, site.brand, site.domain, site.category, site.url])


def goggle_text(
    *,
    name: str,
    description: str,
    source_url: str,
    sites: list[Site],
    blank_url_count: int,
    duplicate_count: int,
) -> str:
    domains = "\n".join(f"$boost,site={site.domain}" for site in sites)
    return f"""! name: {name}
! description: {description}
! public: false
! author: Me
! avatar: #2F6FED
! license: MIT

! Source sheet: {source_url}
! Allowed domains: {len(sites)}
! Blank URL rows skipped: {blank_url_count}
! Duplicate domains skipped: {duplicate_count}
! This is an allowlist Goggle: the generic $discard excludes unmatched results.

$discard

{domains}
"""


def write_goggle(
    path: Path,
    *,
    name: str,
    description: str,
    source_url: str,
    sites: list[Site],
    blank_url_count: int,
    duplicate_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        goggle_text(
            name=name,
            description=description,
            source_url=source_url,
            sites=sites,
            blank_url_count=blank_url_count,
            duplicate_count=duplicate_count,
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    sites, blank_url_count, duplicate_sites, bad_urls = read_sites(args.source_csv)

    if bad_urls:
        for row_index, brand, url in bad_urls:
            print(f"Bad URL at row {row_index}: {brand} -> {url}", file=sys.stderr)
        return 1

    write_domains_csv(args.domains_csv, sites)
    write_goggle(
        args.goggle,
        name=args.name,
        description=args.description,
        source_url=args.source_url,
        sites=sites,
        blank_url_count=blank_url_count,
        duplicate_count=len(duplicate_sites),
    )

    print(f"Allowed domains: {len(sites)}")
    print(f"Blank URL rows skipped: {blank_url_count}")
    print(f"Duplicate domains skipped: {len(duplicate_sites)}")
    if duplicate_sites:
        print("Duplicate domains:")
        for site in duplicate_sites:
            print(f"- row {site.row}: {site.domain} ({site.brand})")
    print(f"Wrote {args.goggle}")
    print(f"Wrote {args.domains_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

