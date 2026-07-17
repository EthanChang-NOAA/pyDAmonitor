[pyDAmonitor book](https://pyDAmonitor.github.io/docs) (showcases plots and results)

# pyDAmonitor
Safeguarding invaluable DA investments by vigilantly monitoring DA performance in both real-time and retrospective scenarios.

## Details
Data assimilation (DA) is a critical component of modern weather forecasting and earth system modeling; it enables the integration of atmospheric observations into models to increase forecast accuracy. 

pyDAmonitor automatically reads both JEDI and GSI diagnostic files to create a comprehensive set of statistics, plots, and maps of key assimilation metrics like OmB (Observation minus Background) and OmA (Observation minus Analysis), innovation distribution, etc. It aims to facilitate and speed up analysis of DA performance in both real-time and retrospective scenarios.

[pyDAmonitor book](https://pyDAmonitor.github.io/docs)

[Working with pyDAmonitor](https://github.com/pyDAmonitor/pyDAmonitor/wiki/work-with-pyDAmonitor)  

Check the [wiki](https://github.com/pyDAmonitor/pyDAmonitor/wiki) for more information

## Creating the `pyDAmonitor` conda environment
The `pyDAmonitor` scripts and notebooks depend on several Python packages. These dependencies are listed in `environment.yaml`, which can be used to create a dedicated Conda environment. By default, this environment is named `pyDAmonitor`.

On the supported HPC platforms (`Hera, Ursa, Gaea, Orion, Hercules, and Derecho`), the `pyDAmonitor` Conda environment is already installed and can be loaded with:
```
source pyDAmonitor/ush/load_pyDAmonitor.sh
```

On other platforms where the pyDAmonitor environment is not available, you can create and activate it by running:
```
git clone https://github.com/pyDAmonitor/pyDAmonitor.git
conda env create -f pyDAmonitor/environment.yaml
conda activate pyDAmonitor
```
**NOTE:** Sample data are pre-staged on supported platforms for a quick start. If you need the sample data on other platforms, feel free to reach out to the pyDAmonitor team.
