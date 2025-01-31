# SWAT-LC File Documentation

## 1. Simulation Setting File (*.sim)

This file has a format with a title followed by several simulation settings:

<div align="center">
<img src="pics\simsettings.png" alt="simsettings" style="zoom:67%;" />
</div>

The meaning and format of these settings are:

| Item Name  | Format | Description                                                  |
| ---------- | ------ | ------------------------------------------------------------ |
| BUMETHOD   | int    | Build-up governing equations. 0: power build-up, 1: exponential build-up, 2: saturation build-up, 3: half-saturation build-up. |
| WOMETHOD   | int    | Wash-off governing equations. 0: exponential wash-off (basic version), 1: exponential wash-off (flow driven--SWMM like version), 2: rating curve wash-off (directly related to the flow). |
| DOCMETHOD  | int    | DOC simulation methods, 0: organic carbon partitioning coefficient (You et al. 1999), 1: fraction of organic carbon concentration in soil water (adopted by Du et al. 2019). |
| RIVERFLUX  | int    | Option for the consideration of pollutant flux directly accepted by the river water surface, 0: off, 1: on. |
| OUTSTART   | str    | The starting date of the results to be saved into the result file. |
| OUTEND     | str    | The end of the results to be saved into the result file.     |
| SCREENSHOW | int    | Option for printing simulation status, 0:  off, 1: on.       |
| HRUOUT     | int    | Option for the generation of HRU simulation result file, 0: off, 1: on. |
| DOCOUT     | int    | Option for the output of DOC simulation results, 0: off, 1: on. |
| INITYPE    | str    | Definition style of the soil initial condition, SOIL: only based on soil type, LU: only based on land use type, SOIL-LU: based on both the soil type and the land use type. |
| FWATER     | str    | Flag of the water body (The name representing water bodies in your SWAT soil map).  If no water body in the soil map then give it any names that do not duplicate existing soil types. |

## 2. Pollutant Definition File (*.plt)

This file is used to define the pollutant that the user wants to simulate. The definition of DOC is mandatory in this file. It has a txt format (comma separated) with several columns. The information about those columns is listed below:

| Column Name | Format    | Unit       | Description                                                  |
| ----------- | --------- | ---------- | ------------------------------------------------------------ |
| POLLUTANT   | str       | -          | Pollutant name                                               |
| hlw         | float/int | day        | Half-life in water                                           |
| hls         | float/int | day        | Half-life in soil                                            |
| logkoc      | float     | L/kg       | Log value of Koc                                             |
| logkdoc     | float     | L/kg       | Log value of Kdoc                                            |
| cprep       | float     | ng/L       | Global parameter for wet deposition                          |
| riverflux   | float     | ug/(m2*yr) | Global parameter for the pollutant directly received by the water surface. |

## 3. Soil (DOC parameters) Definition File

The .sol file is primarily used to define the DOC parameter, it has a txt format (comma separated) with several columns of parameters for the dissolved DOC calculation. The information about those columns is listed below:

| Column Name | Format | Unit                 | Description                                          |
| ----------- | ------ | -------------------- | ---------------------------------------------------- |
| SOIL        | str    | -                    | SWAT soil name                                       |
| POLLUTANT   | str    | -                    | Pollutant name                                       |
| fdoc        | float  | Dimensionless/(Kg/L) | DOC partitioning/fraction parameter                  |
| cbase       | float  | ng/L                 | Background concentration in the base flow (DOC only) |

## 4. Land Use Definition File (*.lu)

This file is used for the setting of some land-use independent parameters, including build-up and wash-off parameters for the surface runoff and leaching process. It has a txt format (comma separated) with several columns of parameters:

| Column Name | Format | Unit   | Description                                                  |
| ----------- | ------ | ------ | ------------------------------------------------------------ |
| LANDUSE     | str    | -      | Land use name                                                |
| POLLUTANT   | str    | -      | Pollutant name                                               |
| bmax        | float  | kg/km2 |                                                              |
| kbu         | float  | days/- | Build-up Coefficient 1, Saturation build-up: saturation time; Half-saturation build-up: half-saturation time; Other methods: build-up coefficient |
| nbu         | float  | -      | Build-up Coefficient 2, ONLY used in power build-up equation |
| kwov        | float  | -      | Vertical wash-off coefficient 1                              |
| nwov        | float  | -      | Vertical wash-off coefficient 2 (rating curve method)        |
| kwoh        | float  | -      | Horizontal wash-off coefficient 1                            |
| nwoh        | float  | -      | Horizontal wash-off coefficient 2 (rating curve method)      |

## 5. Soil Initial Condition Setting File (*.init)

This file is used to set the initial concentration (total mass/total soil volume, ng/L) of pollutants in the soil layer. It has a txt format (comma separated) with several columns. The columns of this file is **changing** with the setting of **INITYPE** in the **SWAT-LC simulation setting file (*.sim)**.

| Column Name | Format | Unit | Description                                        |
| ----------- | ------ | ---- | -------------------------------------------------- |
| LANDUSE     | str    | -    | Land use name, required in LU and SOIL-LU mode.    |
| SOIL        | str    | -    | Soil type name, required in SOIL and SOIL-LU mode. |
| POLLUTANT   | str    | -    | Pollutant name. (Mandatory)                        |
| ctsoil      | float  | ng/L | Total concentration in the soil layer.             |

## 6. Soil-Land Use Conflict Setting File (*.conflict, Optional)

This file is an optional setting file to inform the model of the potential conflicts between the SWAT soil map and land use data. For example, if the soil map has a "Water Body" type, while the land use map has a different type on the same location due to the differences (resolution etc.) between the data sources. This conflict caused by the water body may cause calculation mistakes. Therefore, we provide this file to reset the patches with conflicts. It has a txt format (comma separated) with four columns.

| Column Name | Format | Description                                                  |
| ----------- | ------ | ------------------------------------------------------------ |
| SOIL        | str    | The original soil name in SWAT. It should be same as that presented in your SWAT model, if **ANY** is given in this column, all the land use types will be included. |
| LU          | str    | The original land use name in SWAT. It should be same as that presented in your SWAT model, if **ANY** is given in this column, all the soil types will be included. |
| RSOIL       | str    | The reset soil name.                                         |
| RLU         | str    | The reset land use name.                                     |

Example:

| SOIL  | LU   | RSOIL | RLU  |
| ----- | ---- | ----- | ---- |
| WATER | ANY  | WATER | WATR |

In this example, the land use types of HRUs with a "WATER" soil type will be considered as the new land use (WATR) regardless of what their original land uses are.

## 7. User Defined River Direct Flux (*.usrflux, Optional)

This file is used when the local settings of the direct flux accepted by the river are desired. It can be used to represent the spatial variability of the dry and wet depositions. It has a txt format (comma separated) with four columns.

| Column Name | Format | Unit       | Description                                     |
| ----------- | ------ | ---------- | ----------------------------------------------- |
| RCH         | int    | -          | River channel index                             |
| POLLUTANT   | str    | -          | Pollutant name                                  |
| cprep       | float  | ng/L       | Concentration in precipitation                  |
| riverflux   | float  | ug/(m2*yr) | Routine flux into accepted by the water surface |

## 8. User Defined Land Use Setting File (*.usrlu, Optional)

This file is used when the local settings of the land use parameters are desired. The consideration of the local effect can either be sub-basin scale or HRU scale, depending on the given control type (**CTLTYPE**). It has a txt format (comma separated) with ten columns.

| Column Name | Format | Unit | Description                                                  |
| ----------- | ------ | ---- | ------------------------------------------------------------ |
| CTLTYPE     | str    | -    | Control type. SUB: sub-basin; HRU: Hydrological response unit. **The HRU settings have higher priority than sub-basin settings**. |
| ID          | int    | -    | Index of the sub-basin or HRU                                |
| POLLUTANT   | str    | -    | Pollutant name                                               |
| bmax        | -      | -    | Same as the *.lu file                                        |
| kbu         | -      | -    | -                                                            |
| nbu         | -      | -    | -                                                            |
| kwov        | -      | -    | -                                                            |
| nwov        | -      | -    | -                                                            |
| kwoh        | -      | -    | -                                                            |
| nwoh        | -      | -    | -                                                            |

## 9. User Defined Soil Initial Conditions (*.usrinit, Optional)

This file is used when the local settings of the soil initial conditions are desired.

| Column Name | Format | Unit | Description                                                  |
| ----------- | ------ | ---- | ------------------------------------------------------------ |
| CTLTYPE     | str    | -    | Control type. SUB: sub-basin; HRU: Hydrological response unit. **The HRU settings have higher priority than sub-basin settings**. |
| ID          | int    | -    | Index of the sub-basin or HRU                                |
| POLLUTANT   | str    | -    | Pollutant name                                               |
| ctsoil      | float  | ng/L | Soil initial concentration (pollutant mass/soil volume)      |

