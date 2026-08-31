"""Sync learning HTML into study-site for GitHub Pages deploy."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent.parent.parent  # personal-ai-os/workspace

# (source glob base, dest under study-site)
SYNC_RULES: list[tuple[Path, Path]] = [
    (
        WORKSPACE / "apps/learning/japanese/programs/n3/try-n3",
        ROOT / "japanese/try-n3",
    ),
    (
        WORKSPACE / "apps/learning/japanese/07_日记",
        ROOT / "japanese/diary",
    ),
    (
        WORKSPACE / "apps/learning/shuili",
        ROOT / "shuili",
    ),
    (
        WORKSPACE / "apps/school/キャリアデザイン",
        ROOT / "school/career-design",
    ),
]

HTML_GLOBS = ("*.html",)


def safe_name(path: Path) -> str:
    return path.name


def copy_html_tree(src: Path, dest: Path) -> int:
    if not src.exists():
        print(f"skip (missing): {src}")
        return 0
    count = 0
    for html in src.rglob("*.html"):
        rel = html.relative_to(src)
        # flatten lesson folders: lesson-05-2/image-1.html → lesson-05-2-image-1.html
        if rel.parent != Path("."):
            flat = dest / str(rel.parent).replace("\\", "-").replace("/", "-")
            flat.mkdir(parents=True, exist_ok=True)
            target = flat / html.name
        else:
            target = dest / html.name
            dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(html, target)
        count += 1
    return count


def write_section_index(
    dest: Path,
    *,
    page_title: str,
    heading: str,
    nav_depth: int,
    nav_active: str,
    items: list[tuple[str, str, str]],
    note: str = "",
) -> None:
    """Write index.html listing top-level HTML pages in dest (GitHub Pages needs this)."""
    prefix = "../" * nav_depth
    lines = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<meta name="robots" content="noindex, nofollow">',
        f"<title>{page_title} · Study</title>",
        f'<link rel="stylesheet" href="{prefix}assets/site.css">',
        "</head>",
        "<body>",
        '<nav class="site-nav"><div class="site-nav-inner">',
        f'<a class="brand" href="{prefix}index.html">Study</a>',
        f'<a href="{prefix}index.html">首页</a>',
        f'<a href="{prefix}japanese/index.html">日语</a>',
        f'<a href="{prefix}shuili/index.html"{" class=\"active\"" if nav_active == "shuili" else ""}>水利</a>',
        f'<a href="{prefix}school/career-design/index.html"{" class=\"active\"" if nav_active == "career" else ""}>キャリアデザイン</a>',
        "</div></nav>",
        "<main>",
        '<section class="block">',
        f"<h2>{heading}</h2>",
    ]
    if note:
        lines.append(f'<p style="font-size:.85rem;color:var(--sub);margin-bottom:.75rem">{note}</p>')
    lines.append('<ul class="link-list">')
    if items:
        for href, label, sub in items:
            sub_html = f'<br><span style="font-size:.78rem;color:var(--sub)">{sub}</span>' if sub else ""
            lines.append(f'  <li><a href="{href}">{label}</a>{sub_html}</li>')
    else:
        lines.append("  <li>（暂无内容 — 运行 build_sync.py）</li>")
    lines.extend(["</ul>", "</section>", "</main>", "</body>", "</html>"])
    out = dest / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(items)} items)")


def collect_top_html(dest: Path) -> list[tuple[str, str, str]]:
    """Return (href, label, sub) for each top-level *.html except index.html."""
    labels = {
        "期末复习讲义.html": ("期末复习讲义", "9/4（金）13:30 考试 · 全15章 · 手机可跳转"),
        "金融トラブル_解説.html": ("金融トラブル授業 — 解説", "8/31 キャリアデザイン · 先生の説明"),
    }
    items: list[tuple[str, str, str]] = []
    if not dest.exists():
        return items
    for html in sorted(dest.glob("*.html")):
        if html.name == "index.html":
            continue
        label, sub = labels.get(html.name, (html.stem, ""))
        items.append((html.name, label, sub))
    return items


def write_japanese_index(try_n3_dest: Path) -> None:
    lessons: list[tuple[str, str]] = []
    if try_n3_dest.exists():
        for d in sorted(try_n3_dest.iterdir()):
            if not d.is_dir():
                continue
            m = re.match(r"lesson-(\d+(?:-\d+)?)", d.name)
            if not m:
                continue
            imgs = sorted(d.glob("image-*.html"))
            if imgs:
                lessons.append((m.group(1), f"{d.name}/{imgs[0].name}"))

    lines = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<meta name="robots" content="noindex, nofollow">',
        "<title>日语 · Try N3</title>",
        '<link rel="stylesheet" href="../assets/site.css">',
        "</head>",
        "<body>",
        '<nav class="site-nav"><div class="site-nav-inner">',
        '<a class="brand" href="../index.html">Study</a>',
        '<a href="../index.html">首页</a>',
        '<a href="index.html" class="active">日语</a>',
        "</div></nav>",
        "<main>",
        '<section class="block">',
        "<h2>Try N3 文法卡片</h2>",
        "<ul class=\"link-list\">",
    ]
    for num, href in lessons:
        lines.append(f'  <li><a href="try-n3/{href}">第 {num} 课</a></li>')
    if not lessons:
        lines.append("  <li>（运行 build_sync.py 后自动生成）</li>")
    lines.extend(["</ul>", "</section>", "</main>", "</body>", "</html>"])
    out = ROOT / "japanese/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(lessons)} lessons)")


def main() -> None:
    total = 0
    for src, dest in SYNC_RULES:
        if dest.name == "try-n3":
            dest.mkdir(parents=True, exist_ok=True)
            if src.exists():
                for lesson_dir in sorted(src.glob("lesson-*")):
                    if not lesson_dir.is_dir():
                        continue
                    target_dir = dest / lesson_dir.name
                    target_dir.mkdir(parents=True, exist_ok=True)
                    for html in lesson_dir.glob("*.html"):
                        shutil.copy2(html, target_dir / html.name)
                        total += 1
        else:
            total += copy_html_tree(src, dest)
        print(f"synced {src.name} → {dest.relative_to(ROOT)}")
    write_japanese_index(ROOT / "japanese/try-n3")
    write_section_index(
        ROOT / "shuili",
        page_title="水理学",
        heading="水理学 · 期末复习",
        nav_depth=1,
        nav_active="shuili",
        items=collect_top_html(ROOT / "shuili"),
        note="考试：2026年9月4日（金）13:30–15:00",
    )
    write_section_index(
        ROOT / "school/career-design",
        page_title="キャリアデザイン",
        heading="キャリアデザイン",
        nav_depth=2,
        nav_active="career",
        items=collect_top_html(ROOT / "school/career-design"),
    )
    print(f"total html files: {total}")


if __name__ == "__main__":
    main()
