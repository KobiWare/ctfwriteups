#!/usr/bin/env python3
"""Build static writeup website from markdown files."""

import datetime
import html
import re
import shutil
from collections import OrderedDict
from pathlib import Path

import frontmatter
import markdown
import yaml
from jinja2 import Environment, FileSystemLoader
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).parent
TEMPLATES = ROOT / "templates"
SITE = ROOT / "site"

with open(ROOT / "authors.yml") as f:
    AUTHORS = yaml.safe_load(f)

LANG_MAP = {".py": "python", ".c": "c", ".rb": "ruby", ".sh": "bash"}
BLURB_RE = re.compile(r":::blurb\s+(.+?)\n(.*?):::", re.DOTALL)


def process_blurbs(md_text, md_processor):
    """Replace :::blurb Author ... ::: blocks with styled HTML."""
    def replace_blurb(match):
        author_name = match.group(1).strip()
        content = match.group(2).strip()
        author_info = AUTHORS.get(author_name, {})
        author_url = author_info.get("url", "")
        md_processor.reset()
        inner_html = md_processor.convert(content)
        if author_url:
            name_html = f'<a href="{html.escape(author_url)}" class="author-link">{html.escape(author_name)}</a>'
        else:
            name_html = html.escape(author_name)
        return (
            f'<div class="author-blurb">'
            f'<div class="author-blurb-header">{name_html} says:</div>'
            f'<div class="author-blurb-content">{inner_html}</div>'
            f'</div>'
        )
    return BLURB_RE.sub(replace_blurb, md_text)


def slugify(name, used=None):
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if used is not None:
        base = s
        n = 2
        while s in used:
            s = f"{base}-{n}"
            n += 1
        used.add(s)
    return s



def discover_ctfs():
    """Find all CTFs by scanning ctfs/*/ctf.yml."""
    ctfs_dir = ROOT / "ctfs"
    if not ctfs_dir.is_dir():
        return []
    ctfs = []
    for ctf_dir in sorted(ctfs_dir.iterdir()):
        yml_path = ctf_dir / "ctf.yml"
        if not ctf_dir.is_dir() or not yml_path.exists():
            continue
        with open(yml_path) as f:
            data = yaml.safe_load(f)
        data["slug"] = ctf_dir.name
        ctfs.append(data)
    return ctfs


def discover_challenges(ctf_slug, allowed_categories=None):
    """Walk category directories under a CTF and discover challenges from challenge.yml files."""
    ctf_root = ROOT / "ctfs" / ctf_slug
    if not ctf_root.is_dir():
        return []
    used_slugs = set()

    challenges = []
    for cat_dir in sorted(ctf_root.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue
        if allowed_categories is not None and cat_dir.name not in allowed_categories:
            continue
        for chal_dir in sorted(cat_dir.iterdir()):
            yml_path = chal_dir / "challenge.yml"
            if not yml_path.exists():
                continue
            with open(yml_path) as f:
                chal_yml = yaml.safe_load(f)

            writeup_path = chal_dir / "writeup.md"
            if not writeup_path.exists():
                print(f"  SKIP {cat_dir.name}/{chal_dir.name}: no writeup.md")
                continue

            # Parse writeup frontmatter
            post = frontmatter.load(writeup_path)
            authors_str = post.get("author", "")
            credits_str = post.get("credit", "")
            authors = [a.strip() for a in authors_str.split(",") if a.strip()] if authors_str else []
            credits = [c.strip() for c in credits_str.split(",") if c.strip()] if credits_str else []

            # Load solve scripts from scripts/ directory
            scripts = []
            scripts_dir = chal_dir / "scripts"
            if scripts_dir.is_dir():
                for fpath in sorted(scripts_dir.iterdir()):
                    if fpath.is_file():
                        content = fpath.read_text()
                        lang = LANG_MAP.get(fpath.suffix, "")
                        try:
                            lexer = get_lexer_by_name(lang) if lang else TextLexer()
                        except Exception:
                            lexer = TextLexer()
                        highlighted = highlight(content, lexer, HtmlFormatter(nowrap=True))
                        scripts.append({
                            "filename": fpath.name,
                            "content": html.escape(content),
                            "highlighted": highlighted,
                            "lang": lang,
                            "path": fpath,
                        })

            md_text = post.content
            flags = chal_yml.get("flags", [])
            flag = flags[0] if flags else ""

            # Get files listed in challenge.yml
            chal_files = chal_yml.get("files", [])

            challenges.append({
                "name": chal_yml["name"],
                "category": cat_dir.name,
                "slug": slugify(chal_yml["name"], used_slugs),
                "flag": flag,
                "authors": [{"name": a, "url": AUTHORS.get(a, {}).get("url", "")} for a in authors],
                "credits": [{"name": c, "url": AUTHORS.get(c, {}).get("url", "")} for c in credits],
                "scripts": scripts,
                "md_text": md_text,
                "chal_yml": chal_yml,
                "dir": f"{ctf_slug}/{cat_dir.name}/{chal_dir.name}",
                "chal_files": chal_files,
            })

    return challenges


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=False)
    env.globals["year"] = datetime.date.today().year
    md = markdown.Markdown(extensions=["fenced_code", "tables", "codehilite"],
                           extension_configs={"codehilite": {"guess_lang": False, "css_class": "codehilite"}})

    ctf_summaries = []
    all_ctfs = discover_ctfs()

    for ctf in all_ctfs:
        ctf_dir = SITE / ctf["slug"]
        ctf_dir.mkdir(exist_ok=True)
        print(f"Building {ctf['name']} -> {ctf['slug']}/")

        all_challenges = discover_challenges(ctf["slug"], ctf.get("categories"))
        challenges = []
        for chal in all_challenges:
            md.reset()
            processed_md = process_blurbs(chal["md_text"], md)
            md.reset()
            html_content = md.convert(processed_md)

            chal_dir = ROOT / "ctfs" / ctf["slug"] / chal["category"] / chal["slug"]

            # Copy all files from dist/ to output (for writeup references)
            dist_dir_src = chal_dir / "dist"
            if dist_dir_src.is_dir():
                dist_dir = ctf_dir / chal["slug"] / "dist"
                dist_dir.mkdir(parents=True, exist_ok=True)
                for fpath in dist_dir_src.iterdir():
                    if fpath.is_file():
                        shutil.copy2(fpath, dist_dir / fpath.name)

            # Copy files listed in challenge.yml to site output (for download section)
            file_names = []
            if chal["chal_files"]:
                for file_ref in chal["chal_files"]:
                    file_names.append(Path(file_ref).name)

            # Copy solve scripts to site output
            if chal["scripts"]:
                scripts_dir = ctf_dir / "scripts" / chal["slug"]
                scripts_dir.mkdir(parents=True, exist_ok=True)
                for script in chal["scripts"]:
                    shutil.copy2(script["path"], scripts_dir / script["filename"])

            # Render challenge description as markdown
            md.reset()
            desc_html = md.convert(chal["chal_yml"].get("description", ""))
            md.reset()

            chal_data = {
                "name": chal["name"],
                "category": chal["category"],
                "authors": chal["authors"],
                "credits": chal["credits"],
                "slug": chal["slug"],
                "flag": chal["flag"],
                "content": html_content,
                "scripts": chal["scripts"],
                "chal_yml": chal["chal_yml"],
                "desc_html": desc_html,
                "dist_files": file_names,
            }
            challenges.append(chal_data)

            tmpl = env.get_template("writeup.html")
            page = tmpl.render(ctf_name=ctf["name"], depth=2, **chal_data)
            writeup_dir = ctf_dir / chal["slug"]
            writeup_dir.mkdir(parents=True, exist_ok=True)
            (writeup_dir / "index.html").write_text(page)
            script_info = f" + {len(chal['scripts'])} script(s)" if chal["scripts"] else ""
            print(f"  {chal['slug']}/ <- {chal['dir']}{script_info}")

        # Group by category in order specified by ctf.yml (fallback: alphabetical)
        category_order = ctf.get("categories", sorted(set(c["category"] for c in challenges)))
        categories = OrderedDict()
        for cat_name in category_order:
            display_name = cat_name.capitalize()
            cat_chals = sorted([c for c in challenges if c["category"] == cat_name], key=lambda c: c["name"])
            if cat_chals:
                categories[display_name] = cat_chals

        tmpl = env.get_template("index.html")
        page = tmpl.render(ctf_name=ctf["name"], depth=1, challenges=challenges, categories=categories)
        (ctf_dir / "index.html").write_text(page)

        total_scripts = sum(len(c["scripts"]) for c in challenges)
        print(f"  index.html ({len(challenges)} challenges, {total_scripts} scripts)")

        ctf_summaries.append({
            "name": ctf["name"],
            "slug": ctf["slug"],
            "date": ctf.get("date", ""),
            "challenge_count": len(challenges),
            "placement": ctf.get("placement", ""),
            "ctftime_url": ctf.get("ctftime_url", ""),
        })

    # Render top-level home page
    tmpl = env.get_template("home.html")
    page = tmpl.render(ctfs=ctf_summaries)
    (SITE / "index.html").write_text(page)
    print(f"\nHome page: index.html ({len(ctf_summaries)} CTF(s))")

    # Copy static assets to site root
    shutil.copy2(ROOT / "static" / "style.css", SITE / "style.css")

    print(f"Site built in {SITE}/")


if __name__ == "__main__":
    build()
