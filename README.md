# Drifter simulations run in two CIOFS hindcast simulations

This project has the scripts and notebook/markdown report files to run particle simulations using two hindcast versions of the Cook Inlet Operational Forecast System (CIOFS) ROMS model. The plots and pages from this project are in the report located at [ciofs-fresh.axds.co](https://ciofs-fresh.axds.co).

Note that I used git-lfs to track larger files.

## Initial steps

Set up environment with `environment.yml`:

    mamba env create -f environment.yml


## Run the drifter simulations

Activate environment with 

    conda activate ciofs-drifter-sims

The drifter run script is located at `ciofs_drifter_sims/main.py`. It runs particle simulations to match each dataset from the two drifter data catalogs available from [`cook-inlet-catalogs`](https://github.com/axiom-data-science/cook-inlet-catalogs), as well as calculates skill score metrics and makes an overall plot and skill score plots. It can optionally make an animation too. This uses [`particle-tracking-manager`](https://github.com/axiom-data-science/particle-tracking-manager) which wraps [`OpenDrift`](https://github.com/OpenDrift/opendrift) to run the particles.


## Create the report pages

### Individual dataset pages

After the particle simulations have been run and plots have been made, the individual dataset pages can be created to show the plots together. These pages are created with the script `ciofs_drifter_sims/report/write_pages.py`. Both notebooks and myst markdown files are made, but the myst markdown files are compiled by the Jupyter book ultimately.

Note that there is a variable in the script called `not_in_jupyter_book` that can be used to create either Markdown-friendly files for easy viewing when True or changed to False when ready to create files for the Jupyter book. These files use some syntax that cannot be viewed natively in Markdown but will work in Jupyter book.


### Overview pages

The overview pages was made manually as a notebook, then converted to a Myst markdown file for compilation.


## Now what?

Once these steps are complete, complete the other parts of the report. Then compile the Jupyter book report.