from pathlib import Path
import html
import re

from pybtex.database import parse_file


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

BIB_FILE = ROOT / "data" / "publications.bib"
OUTPUT_DIR = ROOT / "_generated"
OUTPUT_FILE = OUTPUT_DIR / "publications.md"


# ------------------------------------------------------------
# Settings
# ------------------------------------------------------------

MY_LAST_NAME = "Luna"


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def clean_latex(text):
    if not text:
        return ""

    text = str(text)

    replacements = {
        r"\&": "&",
        r"\%": "%",
        r"\_": "_",
        "---": "—",
        "--": "–",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace("{", "").replace("}", "")

    return text.strip()


def initials(first_names):
    """
    Jose       -> J
    Jessica    -> J
    Hongquan   -> H
    Weng Kee   -> WK
    """

    parts = re.findall(r"[A-Za-zÀ-ÿ]+", first_names)

    return "".join(
        part[0].upper()
        for part in parts
        if part
    )


def format_author(person):
    last = " ".join(person.last_names)

    first_parts = (
        list(person.first_names)
        + list(person.middle_names)
    )

    first = " ".join(first_parts)

    init = initials(first)

    author = f"{last}, {init}."

    if last.lower() == MY_LAST_NAME.lower():
        return f"**{author}**"

    return author


def format_authors(entry):
    authors = entry.persons.get("author", [])

    return ", ".join(
        format_author(author)
        for author in authors
    )


def get_url(fields):
    """
    Prefer explicit URL.

    If URL is missing but DOI exists,
    construct a DOI URL.
    """

    url = fields.get("url")

    if url:
        return clean_latex(url)

    doi = fields.get("doi")

    if doi:
        return f"https://doi.org/{clean_latex(doi)}"

    return None


def get_pdf_url(fields):
    """
    Example:

    pdf = {Orthogonal array composite designs for drug combination experiments.pdf}

    becomes:

    /docs/publications/Orthogonal array composite designs for drug combination experiments.pdf
    """

    pdf = fields.get("pdf")

    if not pdf:
        return None

    pdf = clean_latex(pdf)

    return f"/docs/publications/{pdf}"


def format_journal(entry):
    fields = entry.fields

    journal = clean_latex(
        fields.get("journal")
        or fields.get("booktitle")
        or ""
    )

    url = get_url(fields)

    if journal and url:
        return f"[{journal}]({url})"

    return journal


def format_volume_issue_pages(fields):
    volume = clean_latex(
        fields.get("volume", "")
    )

    number = clean_latex(
        fields.get("number", "")
    )

    pages = clean_latex(
        fields.get("pages", "")
    )

    result = ""

    if volume:
        result += volume

        if number:
            result += f"({number})"

    elif number:
        result += f"({number})"

    if pages:
        if result:
            result += f": {pages}"
        else:
            result += pages

    return result


def raw_bibtex(key, entry):
    """
    Construct the BibTeX shown when the user
    clicks the BibTeX button.
    """

    lines = [
        f"@{entry.type}{{{key},"
    ]

    preferred_order = [
        "title",
        "author",
        "journal",
        "booktitle",
        "volume",
        "number",
        "pages",
        "year",
        "publisher",
        "doi",
    ]

    # Title first
    if "title" in entry.fields:
        lines.append(
            f"  title={{{entry.fields['title']}}},"
        )

    # Authors
    if "author" in entry.persons:
        authors = []

        for person in entry.persons["author"]:

            first = " ".join(
                list(person.first_names)
                + list(person.middle_names)
            )

            last = " ".join(person.last_names)

            if first:
                authors.append(
                    f"{last}, {first}"
                )
            else:
                authors.append(last)

        lines.append(
            f"  author={{{' and '.join(authors)}}},"
        )

    # Remaining fields
    remaining_order = [
        "journal",
        "booktitle",
        "volume",
        "number",
        "pages",
        "year",
        "publisher",
        "doi",
    ]

    handled = {
        "title",
        "author",
    }

    for field in remaining_order:

        if field in entry.fields:

            value = entry.fields[field]

            lines.append(
                f"  {field}={{{value}}},"
            )

            handled.add(field)

    # Include any other normal BibTeX fields
    for field, value in entry.fields.items():

        if field in handled:
            continue

        # Website-specific fields
        if field in {"pdf", "url"}:
            continue

        lines.append(
            f"  {field}={{{value}}},"
        )

    # Remove trailing comma from final field
    if len(lines) > 1:
        lines[-1] = lines[-1].rstrip(",")

    lines.append("}")

    return "\n".join(lines)


def publication_markdown(key, entry, number):

    fields = entry.fields

    authors = format_authors(entry)

    title = clean_latex(
        fields.get("title", "")
    )

    journal = format_journal(entry)

    year = clean_latex(
        fields.get("year", "")
    )

    citation_details = (
        format_volume_issue_pages(fields)
    )

    pdf_url = get_pdf_url(fields)

    bibtex_id = f"bibtex-{key}"

    # --------------------------------------------------------
    # Publication citation
    # --------------------------------------------------------

    citation = f"{number}. {authors} {title}."

    if journal:
        citation += f" {journal}."

    if year:
        citation += f" {year}"

    if citation_details:
        citation += f"; {citation_details}"

    # --------------------------------------------------------
    # Inline PDF button
    # --------------------------------------------------------

    pdf_button = ""

    if pdf_url:

        pdf_button = (
            f'<a class="inline-btn" '
            f'href="{html.escape(pdf_url, quote=True)}" '
            f'target="_blank" '
            f'rel="noopener">\n'
            f'  <i class="bi bi-file-earmark-pdf"></i> PDF\n'
            f'</a>'
        )

    # --------------------------------------------------------
    # Inline BibTeX button
    # --------------------------------------------------------

    bibtex_button = (
        f'<button class="inline-btn" '
        f'onclick="toggleBibtex(\'{bibtex_id}\')">\n'
        f'  <i class="bi bi-quote"></i> BibTeX\n'
        f'</button>'
    )

    # --------------------------------------------------------
    # BibTeX box
    # --------------------------------------------------------

    bibtex = raw_bibtex(
        key,
        entry
    )

    bibtex_box = f"""
<div id="{bibtex_id}" class="bibtex-box">
<div class="bibtex-header">
  <span>BibTeX</span>
  <button class="bibtex-copy" onclick="copyBibtex('{bibtex_id}')">
    <i class="bi bi-clipboard"></i>
    <span class="copy-label">Copy</span>
  </button>
</div>
<pre>
{html.escape(bibtex)}
</pre>
</div>
""".strip()

    # --------------------------------------------------------
    # IMPORTANT:
    # No blank line between citation, PDF, and BibTeX button.
    # This keeps them on the same line/paragraph.
    # --------------------------------------------------------

    parts = [citation]

    if pdf_button:
        parts.append(pdf_button)

    parts.append(bibtex_button)

    inline_section = "\n".join(parts)

    # Blank line only before BibTeX box
    return (
        inline_section
        + "\n\n"
        + bibtex_box
    )


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    if not BIB_FILE.exists():
        raise FileNotFoundError(
            f"Bibliography not found:\n{BIB_FILE}"
        )

    bibliography = parse_file(
        str(BIB_FILE)
    )

    entries = list(
        bibliography.entries.items()
    )

    # Sort newest publications first
    entries.sort(
        key=lambda item: int(
            item[1].fields.get(
                "year",
                "0"
            )
        ),
        reverse=True,
    )

    publications = []

    for number, (key, entry) in enumerate(
        entries,
        start=1
    ):

        publications.append(
            publication_markdown(
                key,
                entry,
                number,
            )
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        "\n\n".join(publications) + "\n",
        encoding="utf-8",
    )

    print(
        f"Generated {len(publications)} publication(s)"
    )

    print(
        f"Output: {OUTPUT_FILE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()