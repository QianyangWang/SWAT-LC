import numpy as np



def washload_equation_m(cocp,kocp,q,w,nocp,qwcr,ea,t0,t):
    """
    A modified washload equation

    :param cocp: outcrop count coefficient
    :param kocp: daily outcrop erosion intensity coefficient, kg/m2 * 86400 s/day
    :param q: flow cms
    :param w: river width
    :param nocp: outcrop erosion exponent
    :param qwcr: threshold/critical water flux (Q/Width)
    :return m: kg daily erosion mass
    """
    m = cocp * kocp * np.exp(ea/8.314 * (1/t0 - 1/t)) * np.maximum(q/w - qwcr,0) ** nocp  # air temperature corrected
    return m


def washload_equation_m1(cocp,kocp,q,w,nocp,qwcr):
    """
    A modified washload equation

    :param cocp: outcrop count coefficient
    :param kocp: daily outcrop erosion intensity coefficient, kg/m2 * 86400 s/day
    :param q: flow cms
    :param w: river width
    :param nocp: outcrop erosion exponent
    :param qwcr: threshold/critical water flux (Q/Width)
    :return m: kg daily erosion mass
    """
    if q/w > qwcr:

        m = cocp * kocp * np.maximum(q/w,0) ** nocp
    else:
        m = 0
    return m

