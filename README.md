# The official repository for the paper "Surrogate DC Microgrid Models for Optimization of Charging Electric Vehicles under Partial Observability "
## Installation
### Anaconda
Install Anaconda, following https://docs.anaconda.com/anaconda/install/
Create virtual environment for the project, e.g.:

```conda create -n evcp python=3.8```

```conda activate evcp```
### Python packages
First, install the packages from the requirements.txt file:

```conda install -c conda-forge --yes --file requirements.txt```

```pip install pycairo```

Then, install the optimization packages.
Importantly, Mosek might require a license. For more information, see here: 
https://www.mosek.com/products/academic-licenses/

```conda install -c mosek mosek```

```conda install -c conda-forge pyomo```

```conda install -c conda-forge ipopt glpk```

## Usage

The experiments from the paper can be replicated by running jupyter notebooks in the notebooks folder.
The folder [notebooks/run_experiments/](/notebooks/run_experiments) contains create_grid and run_planners notebooks.

THe notebooks in [create_grid](/notebooks/run_experiments/0.create_grids) are used to create grid topologies and corresponding scenarios which are then used in the simulations.

The [run_planners](/notebooks/run_experiments/1.run_planners.ipynb) notebook runs the simulations using different planners on the grids and scenarios obtained by create_grids.

After[run_planners](/notebooks/run_experiments/1.run_planners.ipynb) notebook is executed and results are saved, plots can be obtained by [/notebooks/analysis/plot_performance.ipynb](/notebooks/analysis/plot_performance.ipynb)