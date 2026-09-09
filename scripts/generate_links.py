from pathlib import Path
import yaml

# Project root
ROOT = Path(__file__).resolve().parents[1]

# Input/output paths
INPUT_FILE = ROOT / "data" / "links.yml"
OUTPUT_FILE = ROOT / "_generated" / "links.html"


def generate_links():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    html = ['<div class="links">']

    for link in data["links"]:
        label = link["label"]
        href = link["href"]
        icon = link["icon"]
        hint = link.get("hint")
        target = link.get("target")

        attributes = [f'href="{href}"']

        if target:
            attributes.append(f'target="{target}"')
            attributes.append('rel="noopener"')

        html.append("")
        html.append(f'<a class="link-btn" {" ".join(attributes)}>')
        html.append('  <span class="left">')
        html.append(f'    <i class="bi {icon}"></i>')
        html.append(f'    <span class="label">{label}</span>')
        html.append("  </span>")

        if hint:
            html.append(f'  <span class="hint">{hint}</span>')

        html.append("</a>")

    html.append("")
    html.append("</div>")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    print(f"Generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_links()