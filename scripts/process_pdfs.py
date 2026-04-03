#!/usr/bin/env python3
"""Convert local PDF files into a Markdown folder structure with images."""

from __future__ import annotations

import argparse
import math
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import fitz


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "input"
DROP_DIR = INPUT_DIR / "drop"
OUTPUT_DIR = ROOT / "output"
ERROR_DIR = ROOT / "error"


def require_fitz():
    try:
        import fitz as pymupdf
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "PyMuPDF n'est pas installé. Exécutez `python3 -m pip install -r requirements.txt` "
            "dans un environnement Python disposant de pip."
        ) from exc
    return pymupdf


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def sanitize_stem(stem: str) -> str:
    return slugify(stem).replace("-", "_")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def resolve_document_title(document: fitz.Document, fallback: str) -> str:
    title = (document.metadata or {}).get("title", "")
    if title:
        title = re.sub(r"\s+", " ", title).strip()
    return title or fallback


def collect_input_pdfs(drop_dir: Path) -> list[Path]:
    return sorted(path for path in drop_dir.glob("*.pdf") if path.is_file())


def page_range_for_entry(toc: list[list], index: int, total_pages: int) -> tuple[int, int]:
    current_level, _title, current_page = toc[index]
    start = max(1, current_page)
    end = total_pages

    for next_level, _next_title, next_page in toc[index + 1 :]:
        if next_level <= current_level and next_page > current_page:
            end = next_page - 1
            break

    return start, max(start, end)


def marginal_text_blocks(page: fitz.Page, margin_ratio: float = 0.08) -> list[str]:
    page_height = page.rect.height
    top_limit = page_height * margin_ratio
    bottom_limit = page_height * (1 - margin_ratio)

    blocks: list[str] = []
    for _x0, y0, _x1, y1, text, *_ in page.get_text("blocks"):
        normalized = normalize_text(text)
        if not normalized:
            continue
        if y1 <= top_limit or y0 >= bottom_limit:
            blocks.append(normalized)
    return blocks


def find_repeated_marginal_text(document: fitz.Document) -> set[str]:
    counts: dict[str, int] = {}
    total_pages = max(1, document.page_count)
    min_hits = max(2, math.ceil(total_pages * 0.2))

    for page_index in range(document.page_count):
        page = document.load_page(page_index)
        for text in set(marginal_text_blocks(page)):
            counts[text] = counts.get(text, 0) + 1

    return {text for text, hits in counts.items() if hits >= min_hits}


def extract_body_text_without_headers_footers(page: fitz.Page, repeated_marginal_text: set[str]) -> str:
    chunks: list[tuple[float, float, str]] = []

    for x0, y0, _x1, _y1, text, *_ in page.get_text("blocks"):
        normalized = normalize_text(text)
        if not normalized or normalized in repeated_marginal_text:
            continue
        chunks.append((y0, x0, text.strip()))

    ordered = [text for _, _, text in sorted(chunks, key=lambda item: (item[0], item[1])) if text]
    return "\n\n".join(ordered).strip()


def linkify_urls(text: str) -> str:
    pattern = re.compile(r"(?P<url>https?://[^\s<>()\[\]{}]+)", re.IGNORECASE)

    def replace(match: re.Match[str]) -> str:
        url = match.group("url").rstrip(".,;)")
        return f"[{url}]({url})"

    return pattern.sub(replace, text)


def table_to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""

    normalized = [[(cell or "").strip().replace("\n", " ") for cell in row] for row in rows]
    width = max(len(row) for row in normalized)
    if width == 0:
        return ""

    padded = [row + [""] * (width - len(row)) for row in normalized]
    lines = [
        f"| {' | '.join(padded[0])} |",
        f"| {' | '.join(['---'] * width)} |",
    ]
    lines.extend(f"| {' | '.join(row)} |" for row in padded[1:])
    return "\n".join(lines)


def extract_tables_markdown(page: fitz.Page) -> list[str]:
    tables = page.find_tables()
    markdown_tables: list[str] = []
    for table in tables.tables:
        markdown = table_to_markdown(table.extract())
        if markdown:
            markdown_tables.append(markdown)
    return markdown_tables


def extract_page_links_markdown(page: fitz.Page) -> list[str]:
    links_md: list[str] = []
    seen: set[str] = set()
    for link in page.get_links():
        uri = (link or {}).get("uri")
        if not uri:
            continue
        uri = uri.strip()
        if not uri or uri in seen:
            continue
        seen.add(uri)
        links_md.append(f"- [{uri}]({uri})")
    return links_md


def extract_images_markdown(
    document: fitz.Document,
    page: fitz.Page,
    images_dir: Path,
    image_map: dict[int, str],
    image_counter: list[int],
) -> list[str]:
    image_links: list[str] = []
    for image in page.get_images(full=True):
        xref = image[0]
        if xref not in image_map:
            payload = document.extract_image(xref)
            if not payload:
                continue
            extension = payload.get("ext", "png")
            image_counter[0] += 1
            filename = f"image-{image_counter[0]:03d}.{extension}"
            (images_dir / filename).write_bytes(payload["image"])
            image_map[xref] = filename
        image_links.append(f"![Image extraite page {page.number + 1}](./images/{image_map[xref]})")
    return image_links


def extract_section_markdown(
    document: fitz.Document,
    start_page: int,
    end_page: int,
    images_dir: Path,
    image_map: dict[int, str],
    image_counter: list[int],
    repeated_marginal_text: set[str],
) -> str:
    chunks: list[str] = []

    for page_index in range(start_page - 1, end_page):
        page = document.load_page(page_index)
        text = extract_body_text_without_headers_footers(page, repeated_marginal_text)
        if text:
            chunks.append(linkify_urls(text))

        for table_index, table_md in enumerate(extract_tables_markdown(page), start=1):
            chunks.append(f"## Tableau {table_index} (page {page_index + 1})\n\n{table_md}")

        links_md = extract_page_links_markdown(page)
        if links_md:
            chunks.append(f"## Liens (page {page_index + 1})\n\n" + "\n".join(links_md))

        chunks.extend(extract_images_markdown(document, page, images_dir, image_map, image_counter))

    return "\n\n".join(chunks).strip()


def write_section_file(path: Path, title: str, body: str) -> None:
    content = body or "_Section vide après extraction._"
    path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")


def write_document_index(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    lines = [f"# {title}", "", "## Table des matières", ""]
    for section_title, filename in sections:
        lines.append(f"- [{section_title}](./{filename})")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def move_pdf_into_output(pdf_path: Path, document_dir: Path) -> Path:
    document_dir.mkdir(parents=True, exist_ok=True)
    target = document_dir / pdf_path.name
    shutil.copy2(pdf_path, target)
    return target


def move_to_error(pdf_path: Path, error_dir: Path, exc: Exception) -> None:
    target_dir = error_dir / sanitize_stem(pdf_path.stem)
    target_dir.mkdir(parents=True, exist_ok=True)
    error_file = target_dir / "error.md"
    error_file.write_text(
        "\n".join(
            [
                f"# Erreur de conversion: {pdf_path.name}",
                "",
                f"- PDF source: `{pdf_path}`",
                f"- Erreur: `{type(exc).__name__}: {exc}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def process_pdf(pdf_path: Path, output_dir: Path, error_dir: Path, force: bool) -> Path | None:
    fitz = require_fitz()

    try:
        with fitz.open(pdf_path) as preview:
            document_title = resolve_document_title(preview, pdf_path.stem)
    except Exception as exc:
        move_to_error(pdf_path, error_dir, exc)
        return None

    document_key = sanitize_stem(document_title)
    document_dir = output_dir / document_key

    if document_dir.exists():
        if not force:
            print(f"Extraction ignorée, sortie existante: {document_dir}")
            return document_dir
        shutil.rmtree(document_dir, ignore_errors=True)

    stored_pdf = move_pdf_into_output(pdf_path, document_dir)
    images_dir = document_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    sections: list[tuple[str, str]] = []
    image_map: dict[int, str] = {}
    image_counter = [0]

    try:
        with fitz.open(stored_pdf) as document:
            repeated_marginal_text = find_repeated_marginal_text(document)
            toc = document.get_toc(simple=True)

            if toc:
                for index, (_level, section_title, _page) in enumerate(toc, start=1):
                    start_page, end_page = page_range_for_entry(toc, index - 1, document.page_count)
                    filename = f"{index:02d}-{slugify(section_title)}.md"
                    body = extract_section_markdown(
                        document,
                        start_page,
                        end_page,
                        images_dir,
                        image_map,
                        image_counter,
                        repeated_marginal_text,
                    )
                    write_section_file(document_dir / filename, section_title, body)
                    sections.append((section_title, filename))
            else:
                filename = "01-document-complet.md"
                body = extract_section_markdown(
                    document,
                    1,
                    document.page_count,
                    images_dir,
                    image_map,
                    image_counter,
                    repeated_marginal_text,
                )
                write_section_file(document_dir / filename, document_title, body)
                sections.append((document_title, filename))
    except Exception as exc:
        shutil.rmtree(document_dir, ignore_errors=True)
        move_to_error(pdf_path, error_dir, exc)
        return None

    write_document_index(document_dir / "index.md", document_title, sections)
    print(f"Extraction terminée: {pdf_path.name} -> {document_dir}")
    return document_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convertit des PDF locaux en structure Markdown.")
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--drop-dir", type=Path, default=DROP_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--error-dir", type=Path, default=ERROR_DIR)
    parser.add_argument("--pdf", type=Path, help="Chemin d'un PDF unique à traiter.")
    parser.add_argument("--force", action="store_true", help="Remplace une extraction existante.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.input_dir.mkdir(parents=True, exist_ok=True)
    args.drop_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.error_dir.mkdir(parents=True, exist_ok=True)

    pdfs = [args.pdf] if args.pdf else collect_input_pdfs(args.drop_dir)
    if not pdfs:
        print(f"Aucun PDF trouvé dans {args.drop_dir}")
        return 0

    require_fitz()

    converted = 0
    for pdf_path in pdfs:
        if not pdf_path.exists():
            print(f"PDF introuvable: {pdf_path}")
            continue
        result = process_pdf(pdf_path, args.output_dir, args.error_dir, args.force)
        if result is not None:
            converted += 1

    print(f"Documents convertis: {converted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
