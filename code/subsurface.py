# Author: Qianyang Wang
import numpy as np


def cal_partioning(theta,kdoc,cwdoc,kp,dsoil):
    """
    1. Calculate the soil overall conc/soil water PAH conc. ratio
    Rsoil in Du et al. (2019). doi: j.envsoft.2018.10.011
    2. Calculate the conc. of PAHs in different phases

    :param theta: Soil volumetric water content
    :param kdoc: DOC-water partitioning coeff, L/kg, parameter
    :param cwdoc: Conc. of DOC in soil water (mg/L)
    :param kp: Soild-water partitioning coeff
    :param dsoil: Density of soil solid phase (expressed in mg/L)
    :return: fd, fp, fdoc, fractions in dissolved phase, solid phase, and doc phase
    """
    rsoil = 10**6 * theta + kdoc * theta * cwdoc + kp * dsoil
    fd = 10**6 * theta / rsoil
    fp = kp * dsoil / rsoil
    fdoc = kdoc * theta * cwdoc / rsoil
    return fd, fp, fdoc


def cal_3phase_conc(ctsoil,fd,fp,fdoc):
    """
    Calculate the relative concentration of PAH in 3 phases (water, solid, DOC)
    Relative conc.: The mass of pollutant divided by the whole volume of the soil.
    :param ctsoil: total concentration of PAH in soil
    :param fd: fraction of the dissolved phase
    :param fp: fraction of the solid phase
    :param fdoc: fraction of the doc phase
    """
    cdsoil = ctsoil * fd
    cpsoil = ctsoil * fp
    cdocsoil = ctsoil * fdoc
    return cdsoil, cpsoil, cdocsoil


def cal_lat_load(mlat, mlatstor, Lhill, Ksat,Lattime):
    """
    Calculate the load in the lateral flow to the reach
    """
    mlatrch = mlat + mlatstor
    mrem = mlat + mlatstor - mlatrch
    return mlatrch, mrem


"""
def cal_lat_load2(mlat, mlatstor, Lhill, Ksat,Lattime):
    
    #Calculate the load in the lateral flow to the reach under the time lag effect
    #:param mlat: the mass of pollutant in the lateral flow to the river channel
    #:param mlatstor: the mass of PAH stored in the lateral flow due to the time lag
    #:param Lhill: slope length
    #:param Ksat: saturation hydrological conductivity of the soil layer
    #:return
    #mlatrch: the final mass of pollutant transported to the reach
    #mrem: remained mass of pollutants that are still traveling due to the lag effect
    
    if Lattime != 0:
        ttlag = Lattime                 # Has user defined lateral flow travel time in the parameter file
    else:
        ttlag = 10.4 * Lhill / Ksat     # Does not have user defined lateral flow travel time in the parameter file
    if ttlag == 0:
        r = 1
    else:
        r = 1 - np.exp(-1 / ttlag)

    mlatrch = (mlat + mlatstor) * r
    mrem = mlat + mlatstor - mlatrch
    return mlatrch, mrem
"""

def cal_gw_in_load(mseep, gwlag, mr_1):
    """
    Calculate the load in the groundwater recharge under the time lag effect
    :param mseep: the output of the soil profile
    :param gwlag: ground water time lag (days)
    :param mr_1: the load in the groundwater recharge in the previous time step
    :return msai: the load to the shallow aquifer at the current step
    """
    msai = (1 - np.exp(-1 / gwlag)) * mseep + np.exp(-1 / gwlag) * mr_1
    mr_1 = mseep + mr_1 - msai
    return msai, mr_1




