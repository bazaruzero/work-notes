#!/usr/bin/env python3
"""
new_post.py — initialize a new post and automatically rebuild the indexes.

Usage:

  # create a new post (indexes will be rebuilt automatically)
  python scripts/new_post.py my-post-slug \
      --title "Post title" \
      --categories postgresql,backup \
      [--pinned] [--author admin] [--description "..."]

  # rebuild indexes only (README.md + categories/*.md)
  python scripts/new_post.py --rebuild

Dependencies:
  pip install pyyaml
"""
import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Error: PyYAML is required. Install it with: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
CATEGORIES_DIR = ROOT / "categories"
README = ROOT / "README.md"

FRONTMATTER_RE = re.compile(
    r"^<!--\s*\n---\s*\n(.*?)\n---\s*\n-->\s*\n(.*)$",
    re.DOTALL,
)

MARKERS = {
    "pinned": ("<!-- AUTO:PINNED:BEGIN -->", "<!-- AUTO:PINNED:END -->"),
    "latest": ("<!-- AUTO:LATEST:BEGIN -->", "<!-- AUTO:LATEST:END -->"),
    "categories": ("<!-- AUTO:CATEGORIES:BEGIN -->", "<!-- AUTO:CATEGORIES:END -->"),
    "posts": ("<!-- AUTO:POSTS:BEGIN -->", "<!-- AUTO:POSTS:END -->"),
}


# ---------- parsing posts ----------

def parse_post(post_file: Path) -> dict | None:
    slug = post_file.parent.name
    if post_file.name != f"{slug}.md":
        print(f"  skipping {post_file}: filename != folder name", file=sys.stderr)
        return None
    text = post_file.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        print(f"  skipping {post_file}: no frontmatter found", file=sys.stderr)
        return None
    meta = yaml.safe_load(m.group(1)) or {}
    meta.setdefault("title", slug)
    meta.setdefault("slug", slug)
    meta.setdefault("categories", [])
    meta.setdefault("tags", [])
    meta.setdefault("pinned", False)
    meta.setdefault("created", date.today())
    meta.setdefault("updated", meta["created"])
    cats = meta["categories"]
    if isinstance(cats, str):
        cats = [c.strip() for c in cats.split(",")]
    meta["categories"] = [str(c).strip().lower() for c in cats if c]
    meta["_path"] = post_file
    return meta


def load_posts() -> list[dict]:
    posts = []
    for post_dir in sorted(POSTS_DIR.iterdir()):
        if not post_dir.is_dir():
            continue
        md_files = list(post_dir.glob("*.md"))
        if not md_files:
            continue
        post = parse_post(md_files[0])
        if post:
            posts.append(post)
    return posts


# ---------- replacing auto-blocks ----------

def replace_block(text: str, begin: str, end: str, content: str) -> str:
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    block = f"{begin}\n{content}\n{end}"
    if not pattern.search(text):
        return text.rstrip() + f"\n\n{block}\n"
    return pattern.sub(lambda _: block, text)


# ---------- building indexes ----------

def post_link(post: dict, rel_to: Path) -> str:
    rel = os.path.relpath(post["_path"], start=rel_to.parent).replace(os.sep, "/")
    return f"[{post['title']}]({rel})"


def rebuild_categories(posts: list[dict]) -> None:
    CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)

    cats_from_posts = {c for p in posts for c in p["categories"]}
    existing = {f.stem for f in CATEGORIES_DIR.glob("*.md")}

    for cat in sorted(cats_from_posts - existing):
        (CATEGORIES_DIR / f"{cat}.md").write_text(
            f"# {cat}\n\n"
            f"{MARKERS['posts'][0]}\n{MARKERS['posts'][1]}\n",
            encoding="utf-8",
        )
        print(f"  + created category: categories/{cat}.md")

    for cat_file in sorted(CATEGORIES_DIR.glob("*.md")):
        cat = cat_file.stem
        items = sorted(
            [p for p in posts if cat in p["categories"]],
            key=lambda p: str(p.get("created", "")),
            reverse=True,
        )
        if items:
            lines = [f"- {p.get('created', '')} — {post_link(p, cat_file)}" for p in items]
            content = "\n".join(lines)
        else:
            content = ""
        begin, end = MARKERS["posts"]
        text = cat_file.read_text(encoding="utf-8")
        new_text = replace_block(text, begin, end, content)
        if new_text != text:
            cat_file.write_text(new_text, encoding="utf-8")
            print(f"  ~ updated categories/{cat}.md")


def rebuild_readme(posts: list[dict]) -> None:
    text = README.read_text(encoding="utf-8")

    cats = sorted({c for p in posts for c in p["categories"]})
    cat_block = "\n\n".join(f"- [{c}](categories/{c}.md)" for c in cats) or "_No categories yet._"
    text = replace_block(text, *MARKERS["categories"], cat_block)

    pinned = sorted(
        [p for p in posts if p.get("pinned")],
        key=lambda p: str(p.get("created", "")),
        reverse=True,
    )
    pinned_block = "\n".join(f"- {post_link(p, README)}" for p in pinned) or "_No pinned posts._"
    text = replace_block(text, *MARKERS["pinned"], pinned_block)

    latest = sorted(
        [p for p in posts if not p.get("pinned")],
        key=lambda p: str(p.get("created", "")),
        reverse=True,
    )
    latest_block = "\n".join(
        f"- {p.get('created', '')} — {post_link(p, README)}" for p in latest
    ) or "_No posts yet._"
    text = replace_block(text, *MARKERS["latest"], latest_block)

    README.write_text(text, encoding="utf-8")
    print("  ~ updated README.md")


def rebuild_all() -> None:
    print("Building indexes...")
    posts = load_posts()
    print(f"  found posts: {len(posts)}")
    rebuild_categories(posts)
    rebuild_readme(posts)
    print("Done.")


# ---------- creating a post ----------

POST_TEMPLATE = """\
<!--
---
title: "{title}"
slug: {slug}
created: {today}
updated: {today}
author: {author}
categories: [{categories}]
tags: []
pinned: {pinned}
description: "{description}"
---
-->

# {title}

## Table of Contents

- [Docs](#docs)
- [Environment](#environment)

## Docs

- [source example 1](https://example1.com)
- [source example 2](https://example2.com)


## Environment

- Host
    - Provider: XXX
    - Device: XXX
    - CPU: XXX
    - RAM: XXX
    - Disk: XXX
    - OS: XXX
    - Virtualization: XXX
- Virtual Machine
    - vCPU: XXX
    - RAM: XXX
    - OS: XXX
- Soft:
    - PostgreSQL Database vXXX


![](images/example.png)

---

<p align="center"><strong><sub>DISCLAIMER</sub></strong></p>

<p align="center">
<sub>
The information presented here is intended for informational purposes only.
The author assumes no responsibility or liability for any damages resulting
from the application of the techniques described herein. Use this content at
your own risk.
<br><br>
Always create backups and test configurations thoroughly before implementing
them in live environments.
</sub>
</p>
"""


def new_post(args) -> None:
    slug = args.slug.lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        sys.exit(f"Invalid slug: {slug!r}. Use kebab-case (a-z, 0-9, hyphens).")

    post_dir = POSTS_DIR / slug
    post_file = post_dir / f"{slug}.md"
    if post_file.exists():
        sys.exit(f"Post already exists: {post_file}")

    categories = (
        [c.strip().lower() for c in args.categories.split(",") if c.strip()]
        if args.categories else []
    )
    today = date.today().isoformat()

    post_dir.mkdir(parents=True, exist_ok=True)
    (post_dir / "images").mkdir(exist_ok=True)
    (post_dir / "files").mkdir(exist_ok=True)
    (post_dir / "images" / ".gitkeep").write_text("", encoding="utf-8")
    (post_dir / "files" / ".gitkeep").write_text("", encoding="utf-8")

    content = POST_TEMPLATE.format(
        title=args.title.replace('"', '\\"'),
        slug=slug,
        today=today,
        author=args.author,
        categories=", ".join(categories),
        pinned="true" if args.pinned else "false",
        description=(args.description or "").replace('"', '\\"'),
    )
    post_file.write_text(content, encoding="utf-8")
    print(f"Created post: {post_file.relative_to(ROOT)}")
    rebuild_all()


def main() -> None:
    parser = argparse.ArgumentParser(description="Blog post management tool.")
    parser.add_argument("slug", nargs="?", help="Slug of the new post (kebab-case).")
    parser.add_argument("--title", help="Post title.")
    parser.add_argument("--categories", help="Comma-separated categories: postgresql,backup.")
    parser.add_argument("--author", default="admin", help="Author (default: admin).")
    parser.add_argument("--description", default="", help="Short post description.")
    parser.add_argument("--pinned", action="store_true", help="Pin the post.")
    parser.add_argument("--rebuild", action="store_true", help="Only rebuild indexes.")
    args = parser.parse_args()

    if args.rebuild:
        rebuild_all()
        return
    if not args.slug:
        parser.error("specify a post slug or use --rebuild")
    if not args.title:
        parser.error("--title is required for a new post")
    new_post(args)


if __name__ == "__main__":
    main()
