# Electric Vehicle Charging Problem with Partial Observability
This is the official repository for the paper

Veviurko, G.; Böhmer, W.; Mackay L.; de Weerdt, M. _Surrogate DC Microgrid Models for Optimization of Charging Electric Vehicles under Partial Observability_, _Energies **2022**_.

If you have any questions regarding the code or the paper, do not hesitate to contact us at [g.veviurko@tudelft.nl](mailto:g.veviurko@tudelft.nl).

## Installation
### Anaconda
Install Anaconda, following https://docs.anaconda.com/anaconda/install/
Create and activate a virtual environment for the project with Python 3.8 using the following commands:

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
The example versions of the datasets are available in the [data folder](/data).
To get the full data used in the paper, [contact us](mailto:g.veviurko@tudelft.nl).

The experiments from the paper can be replicated by running jupyter notebooks in the notebooks folder.
The folder [notebooks/run_experiments/](/notebooks/run_experiments) contains create_grid and run_planners notebooks.

The notebooks in [create_grid](/notebooks/run_experiments/0.create_grids) are used to create grid topologies and corresponding scenarios which are then used in the simulations.

The [run_planners](/notebooks/run_experiments/1.run_planners.ipynb) notebook runs the simulations using different planners on the grids and scenarios obtained by create_grids.

After [run_planners](/notebooks/run_experiments/1.run_planners.ipynb) notebook is executed and results are saved, plots can be obtained by [/notebooks/analysis/plot_performance.ipynb](/notebooks/analysis/plot_performance.ipynb)