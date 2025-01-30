# Author: Qianyang Wang
import numpy as np

"""
Dry deposition & Other terrestrial process: build-up
Wet deposition: rain concentration
Load calc.: wash-off
"""


def power_build_up(bmax,k,n,accum,dt=1):
    """
    Power build-up
    :param bmax: max build-up (kg/km3)
    :param k:
    :param dt:
    :param n:
    :param accum:
    :return:
    """
    b = k * dt**n
    accum += b
    return min(bmax,accum)


def exp_build_up(bmax,k,n,accum,dt=1):
    """
    Exponential build-up
    :param bmax: max build-up (kg/km3)
    :param k:
    :param dt:
    :return:
    """
    b = bmax * (1 - np.exp(-k * dt))
    accum += b
    return min(bmax,accum)


def sat_build_up(bmax,k,accum,dt=1):
    """
    Saturation build-up--constant accumulation rate -> not the half-saturation version
    :param bmax: max build-up (kg/km3)
    :param k:
    :param dt:
    :return:
    """
    b = bmax * dt / (k + dt)
    accum += b
    return min(bmax,accum)



def exponential_wash_off(m,k,dt=1):

    """
    The most basic format of the exponential wash-off
    the wash-off quantity at any time is proportional to the remaining pollutant buildup. Typically used in
    urban catchments.
    :param m: current mass
    :param k: coefficient
    :param dt: time step
    :return:
    """
    w = m * (1 - np.exp(-k*dt))
    remain = m - w
    return remain, w


def exponential_wash_off_q(m,k,q,dt=1):
    """
    Refer to the SWMM wash-off process without the power term. The wash-off quantity at any time
    is proportional to the remaining pollutant buildup. Typically used in urban catchments. The wash-off
    rate is also a function of flow generated.
    :param m: current mass
    :param k: coefficient
    :param dt: time step
    :return:
    """
    w = m * (1 - np.exp(-k*q*dt))
    remain = m - w
    return remain, w

def rating_curve_wash_off(m,k,q,n):
    """
    Rating curve wash-off process. Used more frequently in natural catchments.
    :param m: coefficient
    :param k: coefficient
    :param q: flow rate cfs -- q * fLU * A
    :param n: coefficient
    :return:
    """
    w = min(m,k*q**n)
    remain = m - w
    return remain, w


def surface_lag(m,mt_1,surlag,Lslp,slp,nov,area,Lrch,slprch,nrch):
    """
    This function calculates the time lag of the generated surface runoff to the
    river channel, as well as the time lag of the pollutant load due to the same effect.
    The calculation processes in it is converted from the SWAT source code into Python.
    :param m: Mass of the pollutant load generated in the current time step (any unit)
    :param mt_1: Mass of the pollutant load stored due to the lag effect (any unit)
    :param surlag: HRU surlag
    :param Lslp: Length of the HRU slope (m)
    :param slp: HRU slope
    :param nov: Manning's n for the overland flow
    :param area: HRU area = sub-basin area * HRU fraction
    :param Lrch: Length of the tributary river channel
    :param slprch: Slope of the reach
    :param nrch: Manning's n of the river channel
    :return:
    msurf: Mass of the pollutant to the river channel
    mt_1: Mass of the pollutant stored
    """

    m = m + mt_1
    tov = 0.0556 * (Lslp * nov)**0.6/slp**0.3
    tch = 0.62 * Lrch * nrch**0.75/(area**0.125*slprch**0.375)
    tconc = tov + tch
    msurf = m * (1 - np.exp(-surlag/tconc))
    mt_1 = m - msurf

    return msurf, mt_1