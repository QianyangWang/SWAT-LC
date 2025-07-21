# Author: Qianyang Wang
import os.path
import time
import numpy as np
from modelutils import PROJmanager
import datetime
import pandas as pd
import surface
import subsurface
import outcrop
from wqutils import decay
import progressbar


class Simulation:

    def __init__(self,SWATdir,LCdir):
        self.mdl_struct = PROJmanager(SWATdir,LCdir)
        print("Load SWAT model successfully.")
        self.start = datetime.date(year=self.mdl_struct.settings["IYR"] + self.mdl_struct.settings["NYSKIP"], month= 1, day=1) \
                     + datetime.timedelta(days=self.mdl_struct.settings["IDAF"] - 1)
        self.end = datetime.date(year=self.mdl_struct.settings["IYR"] + self.mdl_struct.settings["NBYR"] - 1, month= 1, day=1) \
                     + datetime.timedelta(days=self.mdl_struct.settings["IDAL"] - 1)
        self.dateseries = pd.date_range(start=self.start,end=self.end)
        self.outdateseries = pd.date_range(start=self.mdl_struct.outstart,end=self.mdl_struct.outend)
        total_calc = len(self.dateseries) * len(self.mdl_struct.sublist)
        self.pgbar = progressbar.ProgressBar(total_calcs=total_calc)
        self.outhrupath = LCdir + "\lcproj.hruout"
        self.outsubpath = LCdir + "\lcproj.subout"

    def __repr__(self):
        pass

    def run(self):
        if self.mdl_struct.screenshow != 0:
            print("Starting simulation...")
        fhnd = open(self.outhrupath,"w")
        fhnd2 = open(self.outsubpath,"w")
        self.write_hruheader(fhnd)
        self.write_subheader(fhnd2)
        pg = 0
        if self.mdl_struct.screenshow != 0:
            self.pgbar.update(pg)
        airtmp_ts = self.mdl_struct.SWATTmp  # for outcrop erosion temperature correction
        for id,d in enumerate(self.dateseries):
            tmp = airtmp_ts[id]
            for sub in self.mdl_struct.sublist:
                subpcp = sub.input["PRECIP"][id]
                """
                0. Channel Outcrops Erosion Process:
                Incorporate this if the outcrop erosion process is the dominant sources of PACs in the basin. A modified rating curve like equation is used.
                
                Reference:
                Brandon R. Hill, Colin A. Cooke, Alberto V. Reyes, and Murray K. Gingras
                Environmental Science & Technology Article ASAP
                DOI: 10.1021/acs.est.5c02074
                """
                rchflow = sub.input["Flow"][id]
                rchwidth = sub.width
                if sub.hasoutcrop is True:
                    for pollutant in self.mdl_struct.pollutants:
                        # DOC simulation does not consider outcrop erosion
                        if pollutant.name != "DOC":
                            cocp = sub.cocp[pollutant.name]
                            kocp = sub.kocp[pollutant.name]
                            nocp = sub.nocp[pollutant.name]
                            qwcr = sub.qwcr[pollutant.name]
                            ea = sub.ea[pollutant.name]
                            t0 = sub.t0[pollutant.name]
                            outcropmass = outcrop.washload_equation_m(cocp,kocp,rchflow,rchwidth,nocp,qwcr,ea,t0,tmp)
                            sub.stvars[pollutant.name].out_mt += outcropmass
                            sub.stvars[pollutant.name].out_mocp = outcropmass
                        else:
                            sub.stvars[pollutant.name].out_mocp = 0

                # land processes
                for hru in sub.hrulist:
                    pcp = hru.input["PRECIP"][id]
                    smt = hru.input["SNOMELT"][id]
                    surq = hru.input["SURQ"][id]
                    surqrch = hru.input["SURQRCH"][id]
                    perq = hru.input["PERC"][id]
                    swini = hru.input["SWINI"][id]
                    swend = hru.input["SWEND"][id]
                    gwrchg = hru.input["GWRCHG"][id]
                    latq = hru.input["LATQ"][id]
                    latqrch = hru.input["LATQRCH"][id]
                    wyld = hru.input["WYLD"][id]
                    revap = hru.input["REVAP"][id]
                    sast = hru.input["SAST"][id]
                    dast = hru.input["DAST"][id]
                    gwq = hru.input["GWQ"][id]
                    dgwq = hru.input["DGWQ"][id]
                    wat = pcp + smt
                    for pollutant in self.mdl_struct.pollutants:

                        """
                        I. SURFACE PROCESS:
                        
                        *Basic Principle:
                        --Mass balance. accu = accu + bu - wo - decay; srmv = wat * crain + wo - decay
                        
                        *Assumptions: 
                        --The mass removed by the rainfall process has 2 transport pathways: 1) exported by the surface runoff; 2) go into the soil layer.
                        --For the rating curve method, the total wash-off load (including path1 and path2) is related to the rainfall.
                        --The quantity into the surface runoff can be determined by the overall conc. and the surface runoff. If the rainfall event does
                          not generate the surface runoff, then all the wash-off load will go into the soil layer.
                        """

                        if hru.usrlu[pollutant.name]:
                            # the user defined LU settings have higher priority
                            bmax = hru.bmax[pollutant.name]
                            kbu = hru.kbu[pollutant.name]
                            nbu = hru.nbu[pollutant.name]
                        else:
                            bmax = self.mdl_struct.lu[hru.lu].bmax[pollutant.name]
                            kbu = self.mdl_struct.lu[hru.lu].kbu[pollutant.name]
                            nbu = self.mdl_struct.lu[hru.lu].nbu[pollutant.name]

                        if wat == 0:
                            # 1. Dry days, build-up
                            if self.mdl_struct.bumth == surface.sat_build_up:
                                # saturation build-up -> does not need antecedent dry days, decay considered
                                oriaccu = hru.stvars[pollutant.name].maccu / hru.area  # kg/km2
                                oriaccu = decay(oriaccu, pollutant.dsoil)
                                mpa = self.mdl_struct.bumth(bmax, kbu, oriaccu)
                            else:
                                # exp, pow, half-sat build-up -> need antecedent dry days, decay not considered
                                hru.stvars[pollutant.name].drydays += 1
                                oriaccu = hru.stvars[pollutant.name].maccu / hru.area  # kg/km2
                                mpa = oriaccu # exp, half-sat method, decay not considered, mass will be added on wet day
                            mhrmv = 0
                            csrmv = 0
                            soilin = 0
                        else:
                            if self.mdl_struct.bumth == surface.sat_build_up:
                                # 1. Wet days, no build-up for sat build-up
                                oriaccu = hru.stvars[pollutant.name].maccu / hru.area  # kg/km2
                                oriaccu = decay(oriaccu, pollutant.dsoil)
                                mpa = oriaccu
                            else:
                                # 1. Wet days, add the dry days build-up for exp, pow, half-sat methods
                                if hru.stvars[pollutant.name].drydays != 0:
                                    oriaccu = hru.stvars[pollutant.name].maccu / hru.area  # kg/km2
                                    # power, exp, half-sat build-up, mpa: mass per unit area, kg/km2
                                    if self.mdl_struct.bumth == surface.power_build_up:
                                        mpa = self.mdl_struct.bumth(bmax, kbu, nbu, oriaccu,hru.stvars[pollutant.name].drydays)
                                    else:
                                        mpa = self.mdl_struct.bumth(bmax, kbu, oriaccu,hru.stvars[pollutant.name].drydays)
                                else:
                                    oriaccu = hru.stvars[pollutant.name].maccu / hru.area  # kg/km2
                                    mpa = oriaccu
                                hru.stvars[pollutant.name].drydays = 0

                            # 2. Mass (per unit area) of the pollutant in the generated surface runoff due to wet deposition
                            if sub.usrflux[pollutant.name]:
                                mrainh = surq * 10 ** 6 * sub.cprep[pollutant.name] / 10 ** 12      # mm * km2 * 10**6 -> L  cprep: ng/L/10**12 -> kg/L  mrain:kg/HRU.AREA
                                mrainv = (wat - surq) * 10 ** 6 * sub.cprep[pollutant.name] / 10 ** 12
                            else:
                                mrainh = surq * 10**6 * pollutant.cprep/10**12                      # mm * km2 * 10**6 -> L  cprep: ng/L/10**12 -> kg/L  mrain:kg/HRU.AREA
                                mrainv = (wat - surq) * 10**6 * pollutant.cprep/10**12
                            # 3. Wash-off
                            if hru.usrlu[pollutant.name]:
                                # the user defined LU settings have higher priority
                                kwov = hru.kwov[pollutant.name]
                                nwov = hru.nwov[pollutant.name]
                                kwoh = hru.kwoh[pollutant.name]
                                nwoh = hru.nwoh[pollutant.name]
                            else:
                                kwov = self.mdl_struct.lu[hru.lu].kwov[pollutant.name]
                                nwov = self.mdl_struct.lu[hru.lu].nwov[pollutant.name]
                                kwoh = self.mdl_struct.lu[hru.lu].kwoh[pollutant.name]
                                nwoh = self.mdl_struct.lu[hru.lu].nwoh[pollutant.name]
                            if self.mdl_struct.womth == surface.exponential_wash_off:
                                mpa, mwov = self.mdl_struct.womth(mpa, kwov)                     # nwo not used in the case of basic exponential_wash_off
                                mpa, mwoh = self.mdl_struct.womth(mpa, kwoh)
                            elif self.mdl_struct.womth == surface.exponential_wash_off_q:
                                mpa, mwov = self.mdl_struct.womth(mpa, kwov, wat - surq)         # for Q-driven exponential_wash_off_q
                                mpa, mwoh = self.mdl_struct.womth(mpa, kwoh, surq)
                            else:
                                mpa, mwov = self.mdl_struct.womth(mpa, kwov, wat - surq, nwov)   # rating curve -> removed mass directly related to the runoff intensity
                                mpa, mwoh = self.mdl_struct.womth(mpa, kwoh, surq, nwoh)         # rating curve -> removed mass directly related to the runoff intensity
                            # 4. Mass Re-distribution
                            mhrmv = (mrainh + mwoh) * hru.area
                            if surq != 0:
                                csrmv = (mhrmv / (surq * hru.area)) * 10**6                      # conc. of surface removal: kg/(km2 * mm) = mg/L, mg/L = 10**6 ng/L
                            else:
                                csrmv = 0
                            soilin = (mrainv + mwov) * hru.area                                  # Mass go into the soil layer due to the infiltration process, kg

                        # kg mass to the river channel due to the time lag effect
                        msurfstor = decay(hru.stvars[pollutant.name].msurfstor,pollutant.dwat)   # decay of the mass stored in the traveling water
                        msurrch,msurfstor = surface.surface_lag(mhrmv,
                                                                msurfstor,
                                                                hru.NORparam["SURLAG"],
                                                                hru.NORparam["SLSUBBSN"],
                                                                hru.NORparam["HRU_SLP"],
                                                                hru.NORparam["OV_N"],
                                                                hru.area,
                                                                sub.NORparam["CH_L1"] * hru.NORparam["HRU_FR"],
                                                                sub.NORparam["CH_S1"],
                                                                sub.NORparam["CH_N1"])

                        """
                        II. Subsurface Process - Soil Layer
                        
                        *Basic Principle:
                        --Mass balance. Msoil = Msoil + soilin - perco - lat - decay 
                        --Three phase partitioning (PACs only).
                        
                        *Assumptions: 
                        --The conc. of DOC is a fraction of the soil organic carbon.
                        --Three phase partitioning occurred before the percolating occurred, but after the evapotranspiration.
                        --As the soil carbon cycle and the is too complicated, the DOC simulation does not consider the mass from the 
                          surface process, the concentration of DOC is only related to the soil organic carbon, which is a constant value
                          but varies with the soil type. The fdoc is 1/Kd of OC (Kg/L), see the value range at 
                          You et al. 1999, Partitioning of organic matter in soils: effects of pH and water/soil ratio DOI10.1016/S0048-9697(99)00024-8
                        --After the lateral flow generated, the pollutant load will move with the lateral flow to the reach simultaneously.
                        """
                        vswc = (swend + perq + latq) * hru.area * 1000                      # mm * km2 = 1000 m3,
                        #vswc = (swend + perq + latq - revap) * hru.area * 1000             # mm * km2 = 1000 m3,
                        if pollutant.name == "DOC":
                            if hru.usrsol[pollutant.name]:
                                fdoc = hru.fdoc[pollutant.name]
                            else:
                                fdoc = self.mdl_struct.soils[hru.soiltype].fdoc[pollutant.name]
                            if self.mdl_struct.docmth == 0:
                                csoc = 10**6 * hru.morgc/hru.msolid                         # mg/kg
                                cdoc = csoc * fdoc                                          # mg/L fdoc -> oc partitioning coeff kg/L (1/L/kg)
                                mdoc = cdoc * vswc/1000                                     # kg
                            else:
                                if vswc != 0:
                                    csoc = 10**3 * hru.morgc/vswc                           # kg/m3 = g/L * 1000 = mg/L
                                    cdoc = csoc * fdoc                                      # mg/L fdoc -> doc ratio
                                else:
                                    cdoc = 0
                                mdoc = cdoc * vswc/1000                                     # kg
                            #msoil = soilin + mdoc  # kg mass of DOC in solution phase
                            msoilrem = mdoc                                                 # not used

                            # No partitioning calculation for the organic carbon
                            if vswc != 0:
                                cswc = 10**9 * mdoc/vswc                                    # kg/m3 = g/L = 10**9 ng/L -> Conc.
                            else:
                                cswc = 0
                            mper = 0                                                        # do not consider interaction for DOC
                            mlat = cswc * latq * hru.area / 10**6
                            #mlat = cswc * latqrch * hru.area / 10 ** 6
                            mlatstor = decay(hru.stvars[pollutant.name].mlatstor, pollutant.dwat)
                            mlatrch, mlatrem = subsurface.cal_lat_load(mlat,
                                                                       mlatstor,
                                                                       hru.NORparam["SLSOIL"],
                                                                       hru.SOLparam["KSAT"],
                                                                       hru.NORparam["LAT_TTIME"])
                            # not used for DOC, keep the same format
                            cdsoil = 0
                            cpsoil = 0
                            cdocsoil = 0
                            ctsoil = 0
                        else:
                            if hru.soiltype != self.mdl_struct.flagwater:
                                msoilori = decay(hru.stvars[pollutant.name].msoil,pollutant.dsoil)
                            else:
                                msoilori = decay(hru.stvars[pollutant.name].msoil, pollutant.dwat)

                            # geoflux -> leakage from other formations/bitumen layer
                            if hru.usrsol[pollutant.name]:
                                geoflux = hru.geoflux[pollutant.name]
                            else:
                                geoflux = self.mdl_struct.soils[hru.soiltype].geoflx[pollutant.name] # ug/(m2 year)
                            geoflxkg = geoflux * hru.area / (365 * 1000)    # ug/(m2 year) * km2 -> ug/(m2 year) * (1000000 m2/ 365) / 1000000000

                            msoil = soilin + msoilori + geoflxkg
                            if vswc != 0:
                                cswc = 10**9 * msoil/vswc                                   # kg/m3 -> g/L -> 10**9 ng/L
                            else:
                                cswc = 0
                            ctsoil = 10**9 * msoil/hru.vsoil                                # kg/m3 == g/L == 10**9 ng/L
                            theta = vswc/hru.vsoil                                          # volumetric soil water content
                            kp = pollutant.koc * hru.SOLparam["ORGC"]/100
                            dsoil = 2.65 * 10**6                                            # soil solid density 2.65 kg/L -> 2.65 * 10**6 mg/L
                            cwdoc = hru.stvars["DOC"].cw / 10**6                            # conc. of DOC in water, ng/L/10**6 = mg/L
                            fd, fp, fdoc = subsurface.cal_partioning(theta,pollutant.kdoc,cwdoc,kp,dsoil)
                            cdsoil, cpsoil, cdocsoil = subsurface.cal_3phase_conc(ctsoil,fd,fp,fdoc)
                            if vswc != 0:
                                mlat = ((cdsoil + cdocsoil) * hru.vsoil)/vswc * (latq * hru.area)/10**6         # (ng/L * m3)/ m3 * mm * km2/10**6 -> kg; dissolved mass/vswc -> cw; cw * latq -> mdlat
                                mper = ((cdsoil + cdocsoil) * hru.vsoil)/vswc * (perq * hru.area)/10**6         # kg
                            else:
                                mlat = 0
                                mper = 0
                            msoilrem = msoil - mlat - mper
                            mlatstor = decay(hru.stvars[pollutant.name].mlatstor,pollutant.dwat)
                            mlatrch, mlatrem = subsurface.cal_lat_load(mlat,
                                                                       mlatstor,
                                                                       hru.NORparam["SLSOIL"],
                                                                       hru.SOLparam["KSAT"],
                                                                       hru.NORparam["LAT_TTIME"])


                        """
                        III. Subsurface Process - Groundwater
                        
                        *Assumptions:
                        --The aquifer is treated as a reservoir (just like the SWAT model), no solid-water partitioning considered.
                        --Well mixed storage.
                        """
                        if pollutant.name == "DOC":
                            if hru.usrsol[pollutant.name]:
                                cgw = hru.cbase[pollutant.name]
                            else:
                                cgw = self.mdl_struct.soils[hru.soiltype].cbase[pollutant.name]
                            mgwrch = cgw * gwq * hru.area / 10 ** 6                         # ng/L * mm * km2 = ng/L * 1000m3 = mg; mg/10**6 = kg
                            mdgwrch = cgw * dgwq * hru.area / 10 ** 6
                            msarem = 0  # keep the format
                            mdarem = 0
                            mperrem = 0
                            mrevap = 0
                            cdgw = cgw
                        else:
                            mperstor = decay(hru.stvars[pollutant.name].mperstor,pollutant.dsoil)
                            mgwi, mperrem = subsurface.cal_gw_in_load(mper,
                                                                      hru.GWparam["GW_DELAY"],
                                                                      mperstor)
                            msai = mgwi * (1 - hru.GWparam["RCHRG_DP"])                     # percent of percolating water into the shallow aquifer
                            msa = decay(hru.stvars[pollutant.name].msa,pollutant.dsoil)
                            mgw = msa + msai
                            if sast + gwq > 0:
                                cgw = mgw/((sast + gwq) * hru.area) * 10**6                 # ng/L
                            else:
                                cgw = 0
                            mgwrch = cgw * gwq * hru.area / 10**6                           # ng/L * mm * km2 = ng/L * 1000m3 = mg; mg/10**6 = kg
                            mrevap = cgw * revap * hru.area / 10**6
                            msarem = mgw - mgwrch - mrevap
                            msoilrem += mrevap                                              # re-calculate the mass remained in the soil layer

                            mdai = mgwi - msai
                            mda = decay(hru.stvars[pollutant.name].mda,pollutant.dsoil)
                            mdgw = mda + mdai
                            if dast + dgwq > 0:
                                cdgw = mdgw/((dast + dgwq) * hru.area) * 10**6
                            else:
                                cdgw = 0

                            mdgwrch = cdgw * dgwq * hru.area / 10**6
                            mdarem = mdgw - mdgwrch

                        """
                        IV. Overall Mass and Concentration to the Reach 
                        """
                        mtrch = msurrch + mlatrch + mgwrch + mdgwrch                    # kg
                        if wyld != 0:
                            ctrch = 10**6 * mtrch / (wyld * hru.area)                   # ng/L
                        else:
                            ctrch = 0

                        """
                        V. Other Variables
                        """
                        if surqrch != 0:
                            csurrch = 10**6 * msurrch / (surqrch * hru.area)            # ng/L
                        else:
                            csurrch = 0
                        if latqrch != 0:
                            clatrch = 10**6 * mlatrch / (latqrch * hru.area)            # ng/L
                        else:
                            clatrch = 0

                        """
                        V. Update HRU State Variables
                        """
                        # 1. surface storage
                        hru.stvars[pollutant.name].maccu = mpa * hru.area               # kg stored in the state variable

                        # 2. traveling storage
                        hru.stvars[pollutant.name].msurfstor = msurfstor
                        hru.stvars[pollutant.name].mlatstor = mlatrem
                        hru.stvars[pollutant.name].mperstor = mperrem

                        # 3. soil layer storage
                        hru.stvars[pollutant.name].msoil = msoilrem

                        # 4. groundwater storage
                        hru.stvars[pollutant.name].msa = msarem
                        hru.stvars[pollutant.name].mda = mdarem

                        # 5. concentration
                        hru.stvars[pollutant.name].csurf = csrmv
                        hru.stvars[pollutant.name].cw = cswc
                        hru.stvars[pollutant.name].ctsoil = ctsoil
                        hru.stvars[pollutant.name].cpsoil = cpsoil
                        hru.stvars[pollutant.name].cdsoil = cdsoil
                        hru.stvars[pollutant.name].cdocsoil = cdocsoil
                        hru.stvars[pollutant.name].csaq = cgw

                        # 6. other variables
                        hru.stvars[pollutant.name].msurf = mhrmv
                        hru.stvars[pollutant.name].mlat = mlat
                        hru.stvars[pollutant.name].mper = mper
                        hru.stvars[pollutant.name].mrevap = mrevap
                        hru.stvars[pollutant.name].out_msurf = msurrch
                        hru.stvars[pollutant.name].out_mlat = mlatrch
                        hru.stvars[pollutant.name].out_mgw = mgwrch
                        hru.stvars[pollutant.name].out_mt = mtrch
                        hru.stvars[pollutant.name].out_concs = csurrch
                        hru.stvars[pollutant.name].out_concl = clatrch
                        hru.stvars[pollutant.name].out_concg = cgw
                        hru.stvars[pollutant.name].out_conct = ctrch

                        """
                        VI. Update SUBBASIN State Variables
                        """
                        sub.stvars[pollutant.name].out_msurf += msurrch
                        sub.stvars[pollutant.name].out_mlat += mlatrch
                        sub.stvars[pollutant.name].out_mgw += mgwrch
                        sub.stvars[pollutant.name].out_mdgw += mdgwrch
                        sub.stvars[pollutant.name].out_mt += mtrch

                        """
                        VII. Write HRU Output
                        """
                        if self.mdl_struct.hruout != 0:
                            if d in self.outdateseries:
                                if (pollutant.name == "DOC" and self.mdl_struct.docout != 0) or pollutant.name != "DOC":
                                    self.write_hrurow(fhnd,d,sub.name,hru.id,pollutant.name,mtrch,msurrch,mlatrch,mgwrch,mdgwrch,ctrch,clatrch,cgw,cdgw,ctsoil)

                if self.mdl_struct.riverflux == 1:
                    for pollutant in self.mdl_struct.pollutants:
                        if sub.usrflux[pollutant.name]:
                            fluxmass = sub.watsurf * (sub.riverflux[pollutant.name] / 365) / (10 ** 9)      # m2 * ug/(m2 * yr) ug -> kg
                        else:
                            fluxmass = sub.watsurf * (pollutant.flux/365) / (10 ** 9)                       # m2 * ug/(m2 * yr) ug -> kg
                        if subpcp != 0:
                            if sub.usrflux[pollutant.name]:
                                fluxmass += sub.watsurf * subpcp * sub.cprep[pollutant.name] / (10 ** 12)   # m2 * mm -> 0.001 m3 -> L    ng/10**12 -> kg
                            else:
                                fluxmass +=  sub.watsurf * subpcp * pollutant.cprep/(10**12)                # m2 * mm -> 0.001 m3 -> L    ng/10**12 -> kg
                        sub.stvars[pollutant.name].out_mrchflux = fluxmass
                        sub.stvars[pollutant.name].out_mt += fluxmass

                """
                VIII. Write SUBBASIN Output
                """

                for pollutant in self.mdl_struct.pollutants:
                    if d in self.outdateseries:
                        if (pollutant.name == "DOC" and self.mdl_struct.docout != 0) or pollutant.name != "DOC":
                            self.write_subrow(fhnd2,d,sub.name,pollutant.name,
                                              sub.stvars[pollutant.name].out_mt,
                                              sub.stvars[pollutant.name].out_msurf,
                                              sub.stvars[pollutant.name].out_mlat,
                                              sub.stvars[pollutant.name].out_mgw,
                                              sub.stvars[pollutant.name].out_mdgw,
                                              sub.stvars[pollutant.name].out_mrchflux,
                                              sub.stvars[pollutant.name].out_mocp)

                    sub.stvars[pollutant.name].reset0()

                pg += 1
                if self.mdl_struct.screenshow != 0:
                    self.pgbar.update(pg)
        fhnd.close()


    def write_hrurow(self,fhnd,date,subname,hruid,pollutant,mtrch,msurrch,mlatrch,mgwrch,mdgwrch,ctrch,clatrch,cgwrch,cdgwrch,ctsoil):
        date = date.strftime("%Y-%m-%d")
        row = f"{date},{subname},{hruid},{pollutant},{mtrch},{msurrch},{mlatrch},{mgwrch},{mdgwrch},{ctrch},{clatrch},{cgwrch},{cdgwrch},{ctsoil}\n"
        fhnd.write(row)

    def write_hruheader(self,fhnd):
        headers = ",".join(["DATE","SUB","HRU","POLLUTANT","MTkg","MSURkg","MLATkg","MGWkg","MDGWkg","CTng/L","CLATng/L","CGWng/L","CDGWng/L","CTSOILng/L"]) + "\n"
        fhnd.write(headers)

    def write_subrow(self,fhnd,date,subname,pollutant,mtrch,msurrch,mlatrch,mgwrch,mdgwrch,mflux,mocp):
        date = date.strftime("%Y-%m-%d")
        row = f"{date},{subname},{pollutant},{mtrch},{msurrch},{mlatrch},{mgwrch},{mdgwrch},{mflux},{mocp}\n"
        fhnd.write(row)

    def write_subheader(self,fhnd):
        headers = ",".join(["DATE","SUB","POLLUTANT","MTkg","MSURkg","MLATkg","MGWkg","MDGWkg","MFLUXkg","MOCPkg"]) + "\n"
        fhnd.write(headers)



if __name__ == "__main__":
    lcpath = os.path.split(os.path.abspath(__file__))[0]
    s = Simulation(r"AthacascaSWAT",lcpath)
    s.run()
