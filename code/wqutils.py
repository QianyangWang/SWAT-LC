# Author: Qianyang Wang



def decay(mass, kd):
    """
    :param mass: mass of the load
    :param kd: 1st decay coefficient (1/day)
    :return: the remained mass after the decay process
    """
    mdecay = kd * mass
    mass -= mdecay
    return mass


class Pollutant:

    def __init__(self,name):
        self.name = name
        self.hls = 0            # half-life in soil (days)  applied in soil and soil water
        self.hlw = 0            # half-life in water (days) applied in surface water
        self.dwat = 0           # decay rate of pollutant in surface water = 0.693/halflife
        self.dsoil = 0          # decay rate of pollutant in soil and soil water = 0.693/halflife
        self.cprep = 0          # concentration in the
        self.flux = 0           # dry flux to the surface water (ug/(m2*day))


class DOC(Pollutant):

    def __init__(self, name):
        super().__init__(name)
        #self.fdoc = 0           # fraction of DOC in soil organic matter


class PAH(Pollutant):

    def __init__(self, name):
        super().__init__(name)
        self.koc = 0            # koc (partitioning coeff.)
        self.kdoc = 0           # kdoc L/kg


class Landuse:

    def __init__(self, name):
        self.name = name
        self.bmax = {}          # max build-up
        self.kbu = {}            # build-up coeff
        self.dt = 1  # 1 day
        self.nbu = {}            # build-up coeff2
        self.kwov = {}            # vertical wash-off coeff
        self.nwov = {}            # vertical wash-off coeff2
        self.kwoh = {}            # horizontal wash-off coeff
        self.nwoh = {}            # horizontal wash-off coeff2


class Soil:

    def __init__(self, name):
        self.name = name
        self.fdoc = {}
        self.cbase = {}

