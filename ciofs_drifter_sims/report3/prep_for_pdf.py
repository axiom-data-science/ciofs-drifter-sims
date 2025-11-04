import re
import subprocess
from pathlib import Path

# --- 1. Find all overview.ipynb files ---
notebooks = list(Path(".").rglob("overview.ipynb"))

# --- 2. Convert and clean each notebook ---
for nb_path in notebooks:
    md_path = nb_path.with_suffix(".md")

    print(f"Converting {nb_path} → {md_path}")
    subprocess.run(["jupytext", "--to", "myst", str(nb_path)], check=True)

    # --- 3. Read the generated MyST Markdown file ---
    text = md_path.read_text(encoding="utf-8")

    # --- 4a. Force run_pdf = True ---
    text = re.sub(r"run_pdf\s*=\s*\w+", "run_pdf = True", text)

    # --- 4b. Remove glue figure blocks (div-wrapped and simple) ---
    glue_pattern = re.compile(
        r"""
        (
            # --- Match B: div-wrapped glue figure ---
            ````\{div\}\s*full-width\s*\n
            ```\{glue:figure\}\s*[\w\-_]+\s*\n
            :name:\s*".*?"\s*\n
            (?:.*?\n)*?
            ```\s*\n
            ````
        )
        |
        (
            # --- Match A: simple glue figure ---
            ```\{glue:figure\}\s*[\w\-_]+\s*\n
            :name:\s*".*?"\s*\n
            (?:.*?\n)*?
            ```
        )
        """,
        re.DOTALL | re.VERBOSE,
    )

    # Remove all glue figure blocks
    text = glue_pattern.sub("", text)

    # --- 5. Write cleaned Markdown back ---
    md_path.write_text(text, encoding="utf-8")

    print(f"✅ Cleaned {md_path}")

print("🎉 Done! All overview.ipynb files converted, run_pdf set to True, and HTML glue figure blocks removed.")
