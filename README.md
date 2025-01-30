# SWAT-LC

<img src="https://img.shields.io/badge/Version-1.0-brightgreen" /><img src="https://img.shields.io/badge/Language-Python-blue" />	

## Introduction

Characterized by complex behaviors in the environment, the mechanism-based simulation of Polycyclic Aromatic Compounds (PACs) at a basin scale presents significant challenges, underscoring the need for more accessible tools. This code repository introduces a Python extension called “SWAT-LC,” designed specifically based on the SWAT hydrologic model architecture for this purpose. SWAT-LC describes the terrestrial fate and transport processes of PACs for each Hydrological Response Unit (HRU) and sub-basin through a series of build-up, wash-off, partitioning, and decay equations. Using the PACs load calculated by SWAT-LC in conjunction with flow generation simulation results from SWAT, the concentration of PACs in the river can then be modeled using WASP8. Leveraging this extension alongside the SWAT2WASP toolkit (https://github.com/QianyangWang/SWAT2WASP), users can establish a more integrated SWAT—SWAT-LC—WASP8 modeling framework with greater ease. This code repository is a part of the work presented in the paper entitled “Simulation of Polycyclic Aromatic Compounds in the Athabasca River Basin: Integrated Models and Insights”. The architecture of the SWAT—SWAT-LC—WASP8 modeling framework is as follows:

<img src="pics\ModelStructure.jpg" alt="ModelStructure" style="zoom: 50%  width="400";" />

The SWAT-LC model reads the input variables (HRU and river features, HRU water yield time series, etc.) from an existing SWAT simulation project folder, and then simulates the PACs for each HRU. Subsequently, it calculates the summation of the HRU pollutant loads for each sub-catchment. Functionalities can subsequently be used to convert the SWAT-LC output into WASP8 external database, which can be used as the input for WASP8 in-stream fate and transport modelling.

<img src="pics\ModelStructure2.jpg" alt="ModelStructure2" style="zoom:67%;" />

## Major Governing Processes

SWAT-LC incorporates four primary storage layers: surface storage, soil storage, shallow groundwater storage, and deep groundwater storage. In each independent Hydrological Response Unit (HRU), the concentration of PACs is assumed to be homogeneously distributed across these layers. In the surface layer, PACs can accumulate during dry periods. Conversely, during wet days, wash-off processes occur, leading to the movement of PACs. This flux is divided into horizontal wash-off—where PACs move with surface runoff into the river—and vertical wash-off—where PACs leach into the soil layer. Within the soil layer, three-phase partitioning equations (Du et al. 2019; Han et al. 2022) are employed to calculate the concentration of PACs in dissolved, solid, and DOC-adsorbed phases. PACs can then either migrate to the river through lateral flow or infiltrate into the aquifer via percolation. In the groundwater storage layer, PACs can contribute to riverine flows through baseflow, further influencing their concentration in surface waters.

<img src="pics\SWATLCprocesses.jpg" alt="SWATLCprocesses" style="zoom: 67%;" />

## Usage

The major steps to prepare a SWAT-LC simulation include:

1. Prepare a SWAT model (with full results) to provide the required basin structure and input variables (e.g. precipitation, snow melt, surface runoff, lateral flow, and etc.)

2. Prepare the required SWAT-LC setting files, including:

   | File Name             | Format | Description                                                  |
   | --------------------- | ------ | ------------------------------------------------------------ |
   | *.sim                 | txt    | Simulation setting file to inform the options (simulation period, governing equations, and etc.) for modelling. |
   | *.plt                 | txt    | Pollutant definition file.                                   |
   | *.sol                 | txt    | Soil (DOC parameters) definition file.                       |
   | *.lu                  | txt    | Land use (build-up wash-off parameters) definition file.     |
   | *.init                | txt    | Soil initial condition (concentration) setting file.         |
   | *.conflict (optional) | txt    | Soil and land use conflict definition file (to resolve the overlap issues between the soil map and land use, generally occurs on water bodies) |
   | *.usrflux (optional)  | txt    | Local settings of the direct flux (e.g. air depositions) into the river, which has a higher priority than the global parameter. |
   | *.usrlu (optional)    | txt    | Local settings of the build-up and wash-off parameters.      |
   | *.usrinit (optional)  | txt    | Local settings of the soil initial concentration.            |

3. Define your SWAT-LC project folder and run the "main.py".

   ```python
   if __name__ == "__main__": 	
       # SWAT-LC project folder
       lcpath = os.path.split(os.path.abspath(__file__))[0]
    	# SWAT model folder
    	s = Simulation(r"D:\AthaSWAT\swat1522",lcpath) # class Simulation in the main.py
   	s.run()
   ```

   ![ModelRun](pics\ModelRun.png)

4. Use the "resultreader.py" to convert the SWAT-LC results into WASP8 external database.

   ```python
   # if dirtectly run the script
   lc = LCreader(r"D:\SWAT_LC\lcproj.subout")
   lc.toWASP8db(path=r"D:\SWAT2WASP\SWATLC_WASPDB.xlsx")
   
   # if import the module
   import resultreader
   lc = resultreader.LCreader(r"D:\SWAT_LC\lcproj.subout")
   lc.toWASP8db(path=r"D:\SWAT2WASP\SWATLC_WASPDB.xlsx")
   ```

## Reference

1. Du, X., Shrestha, N.K., Wang, J., 2019. Integrating organic chemical simulation module into SWAT model with application for PAHs simulation in Athabasca oil sands region, Western Canada. Environmental Modelling & Software 111 (4), 432–443.
2. Han, Y., Du, X., Farjad, B., Goss, G., Gupta, A., Faramarzi, M., 2022. A numerical modeling framework for simulating the key in-stream fate processes of PAH decay in Muskeg River Watershed, Alberta, Canada. The Science of the total environment 848, 157246.
