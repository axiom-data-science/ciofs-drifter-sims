"""Copied initially from cook-inlet-catalogs/write_template_notebook.py"""


import os
import subprocess
import nbformat as nbf
import cook_inlet_catalogs as cic
from pathlib import Path
import intake
import report_utils as ru

models = ["CIOFS", "CIOFSFRESH"]

imports = f"""\
import intake
import cook_inlet_catalogs as cic
"""


def write_nb(slug, not_in_jupyter_book):

    nb = nbf.v4.new_notebook()
    
    cat = intake.open_catalog(cic.utils.cat_path(slug))
# Click here to run this notebook in Binder, a hosted environment: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/axiom-data-science/cook-inlet-catalogs/HEAD?labpath=docs%2Fdemo_notebooks%2F{slug}.md)

    text = f"""\
# {cat.metadata['overall_desc']}

{cat.metadata['summary']}

"""

    # imports_cell = nbf.v4.new_code_cell(imports)
    text_cell = nbf.v4.new_markdown_cell(text)
    nb['cells'] = [text_cell]
    # nb['cells'] = [imports_cell, text_cell]        
    
#     text = f"""\
# ## Results for datasets in the catalog
# """
#     text_cell = nbf.v4.new_markdown_cell(text)

#     nb['cells'] += [text_cell]

    # import ciofs_drifter_sims
    from importlib.resources import files

    cat = intake.open_catalog(cic.utils.cat_path(slug))
    dataset_ids = list(cat)
    for dataset_id in dataset_ids:
        skip_dataset = False
        text = f"""\
## {dataset_id}

"""

        for model in models:

            base_dir = Path("..") / model
            # base_dir = files(ciofs_drifter_sims) / model
            if not os.path.exists(f"{base_dir}/{dataset_id}.png"):
                print(f"Skipping {dataset_id}")
                skip_dataset = True
                continue
            print(f"Processing {dataset_id}")

            text += f"""\
### {model}

"""

            # link to animation
            base = f"https://files.axds.co/ciofs_fresh/particle_animations/{model}"
            link = f"{base}/{dataset_id}.mp4"
            text += f"* [Animation]({link})\n\n"

            path = f"{base_dir}/{dataset_id}.png"
            # path = f"{base_dir}/{dataset_id}.png"
            label = ""
            caption = ""
            text += ru.utils.mk_fig(path, label, caption, not_in_jupyter_book, width=90)
            text += "\n\n"

            # path = f"{base_dir}/{dataset_id}.mp4"
            # text += mk_md_video(path, label, caption, 75)
            # text += "\n\n"

            path = f"{base_dir}/{dataset_id}_ss_qhull.png"
            label = ""
            caption = ""
            text += ru.utils.mk_fig(path, label, caption, not_in_jupyter_book, width=75)
            # text += mk_md_fig(path, label, caption, 48)
            path = f"{base_dir}/{dataset_id}_ss_sep.png"
            label = ""
            caption = ""
            text += ru.utils.mk_fig(path, label, caption, not_in_jupyter_book, width=75)
            # text += mk_md_fig(path, label, caption, 48)
        if not skip_dataset:
            text_cell = nbf.v4.new_markdown_cell(text)
            nb['cells'] += [text_cell]
    
    nbf.write(nb, f'{slug}.ipynb')

    # Run jupytext command
    subprocess.run(["jupytext", "--to", "myst", f'{slug}.ipynb'])

if __name__ == "__main__":
    base_dir = Path(".")
    
    not_in_jupyter_book = False
    
    slugs = [
        "drifters_ecofoci",
             "drifters_uaf"
             ]
    
    for slug in slugs:
        # if not (base_dir / f"{slug}.ipynb").is_file():
        print(slug)
        write_nb(slug, not_in_jupyter_book)