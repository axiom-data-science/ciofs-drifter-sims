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

    # --- 4a. Force run_pdf = False, regardless of previous value ---
    text = re.sub(r"run_pdf\s*=\s*\w+", "run_pdf = False", text)

    # --- 4b. Remove figure blocks that reference build_figures/*.png ---

    # Matches both formats:
    # +++
    #
    # ```{figure} build_figures/*.png
    # :name: "*"
    # *
    # ```
    #
    # and
    #
    # +++
    #
    # ````{div} full-width
    # ```{figure} build_figures/*.png
    # :name: "*"
    # *
    # ```
    # ````
    figure_pattern = re.compile(
        r"""
        \+\+\+\s*\n
        (?:
            ````\{div\}.*?\n               # optional div wrapper start
            ```\{figure\}\s*build_figures/.*?\.png.*?```\n````   # inner + closing div
            |
            ```\{figure\}\s*build_figures/.*?\.png.*?```         # simple figure block
        )
        """,
        re.DOTALL | re.VERBOSE,
    )

    # Remove all matching figure blocks
    text = figure_pattern.sub("", text)

    # --- 5. Write cleaned Markdown back ---
    md_path.write_text(text, encoding="utf-8")

    print(f"✅ Cleaned {md_path}")

print("🎉 Done! All overview.ipynb files converted, run_pdf set to False, and PNG figure blocks removed.")
