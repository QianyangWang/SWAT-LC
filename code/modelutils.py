# Author: Qianyang Wang
from swat_param import ParamIO
from swat_res import SWATreader
import os
import glob
import configparser
import numpy as np
import pandas as pd
import datetime
from wqutils import PAH,DOC,Landuse,Soil
from surface import power_build_up, exp_build_up, sat_build_up, half_sat_build_up
from surface import exponential_wash_off,rating_curve_wash_off,exponential_wash_off_q


class PROJmanager:

    def __init__(self, swatdir, lcdir):
        self.bumth = None
        self.womth = None

        self.swatdir = swatdir
        os.chdir(self.swatdir)
        self.settings = {}
        self.glbparam = {}
        self.scan_swat_settings()
        self.sublist = []
        self.scan_sub()
        self.load_swat_result()  # input series for the SWAT_LC
        self.lcdir = lcdir
        os.chdir(self.lcdir)
        self.lu = {}
        self.pollutants = []
        self.soils = {}
        self.scan_lc_pollutants()
        self._pollutant_sequence()
        self.scan_lc_landuse()
        self.scan_lc_settings()
        self.scan_lc_sol()
        self.check_conflict()
        self.ini_state_vars()
        self.set_ini_cond()
        self.scan_usr_lu_params()
        self.scan_usr_flux()


    def scan_swat_settings(self):
        print("Scanning SWAT simulation settings...")
        cio = ParamIO("file.cio")
        self.settings["NBYR"] = cio.parameters["NBYR"]
        self.settings["IYR"] = cio.parameters["IYR"]
        self.settings["IDAF"] = cio.parameters["IDAF"]
        self.settings["IDAL"] = cio.parameters["IDAL"]
        self.settings["NYSKIP"] = cio.parameters["NYSKIP"]

    def scan_swan_glbparams(self):
        print("Scanning SWAT global parameters...")
        bsn = ParamIO("basins.bsn")
        self.glbparam["SURLAG"] = bsn.parameters["SURLAG"]

    def scan_lc_settings(self):
        print("Loading SWAT_LC pollutant parameters...")
        budict = {0:power_build_up, 1:exp_build_up, 2:sat_build_up,3:half_sat_build_up}
        wodict = {0:exponential_wash_off,1:exponential_wash_off_q,2:rating_curve_wash_off}
        flist = glob.glob(self.lcdir + "\*.sim")
        if len(flist) > 1:
            raise RuntimeError("There are more than 1 global setting files in the project folder.")
        elif len(flist) == 0:
            raise FileNotFoundError("There is no SWAT_LC global setting file (.sim) in the folder.")
        simfile = flist[0]
        config = configparser.ConfigParser()
        with open(simfile) as f:
            config.read_file(f)
            bumth = int(config.get("General Settings", "BUMETHOD"))     # build-up method
            womth = int(config.get("General Settings", "WOMETHOD"))     # wash-off method
            docmth = int(config.get("General Settings", "DOCMETHOD"))
            outstart = config.get("General Settings", "OUTSTART")
            outend = config.get("General Settings", "OUTEND")
            screenshow = int(config.get("General Settings", "SCREENSHOW"))
            hruout = int(config.get("General Settings", "HRUOUT"))
            docout = int(config.get("General Settings", "DOCOUT"))
            initype = config.get("General Settings", "INITYPE")
            flagwater = config.get("General Settings", "FWATER")
            riverflux = int(config.get("General Settings", "RIVERFLUX"))
        self.bumth = budict[bumth]
        self.womth = wodict[womth]
        self.outstart = datetime.datetime.strptime(outstart,"%Y-%m-%d")
        self.outend = datetime.datetime.strptime(outend,"%Y-%m-%d")
        self.screenshow = screenshow
        self.hruout = hruout
        self.docout = docout
        self.initype = initype
        self.flagwater = flagwater
        self.docmth = docmth
        self.riverflux = riverflux


    def scan_sub(self):
        print("Scanning SWAT project structure...")
        subpath = glob.glob("*.sub")
        subpath.remove("output.sub")
        for p in subpath:
            subname = int(p[:5])
            subobj = SUBBASIN(name=subname)
            subobj.scan_hru(subname,subobj.area)
            rtepath = p[:-4] + ".rte"
            rparam = ParamIO(rtepath)
            width = rparam.parameters["CHW2"]       # channel width in m
            length = rparam.parameters["CH_L2"]     # channel length in km
            area = width * length * 1000            # water surface area in m2
            subobj.watsurf = area
            self.sublist.append(subobj)

    def load_swat_result(self):
        print("Loading SWAT simulation results...")
        reader = SWATreader(self.swatdir)
        reader.read_hru()
        reader2 = SWATreader(self.swatdir)
        reader2.read_sub()
        for s in self.sublist:
            subpcp = reader2.inquireSUB(s.name, "PRECIPmm")
            s.add_input("PRECIP",subpcp)
            for h in s.hrulist:
                pcp = reader.inquireHRU(h.id,"PRECIPmm")
                perc = reader.inquireHRU(h.id,"PERCmm")
                surq = reader.inquireHRU(h.id,"SURQ_GENmm")
                surqrch = reader.inquireHRU(h.id, "SURQ_CNTmm")
                swini = reader.inquireHRU(h.id, "SW_INITmm")
                swend = reader.inquireHRU(h.id, "SW_ENDmm")
                gwrchg = reader.inquireHRU(h.id, "GW_RCHGmm")
                latq = reader.inquireHRU(h.id, "LATQGENmm")
                latqrch = reader.inquireHRU(h.id,"LATQCNTmm")
                wyld = reader.inquireHRU(h.id, "WYLDmm")
                revap = reader.inquireHRU(h.id, "REVAPmm")
                sast = reader.inquireHRU(h.id, "SA_STmm")
                dast = reader.inquireHRU(h.id, "DA_STmm")
                tloss = reader.inquireHRU(h.id, "TLOSSmm")
                snowmelt = reader.inquireHRU(h.id, "SNOMELTmm")
                gwq = reader.inquireHRU(h.id,"GW_Qmm")
                dgwq = reader.inquireHRU(h.id,"GW_Q_Dmm")

                h.add_input("PRECIP",pcp)
                h.add_input("PERC",perc)
                h.add_input("SURQ",surq)
                h.add_input("SWINI",swini)
                h.add_input("SWEND", swend)
                h.add_input("GWRCHG",gwrchg)
                h.add_input("LATQ",latq)
                h.add_input("LATQRCH",latqrch)
                h.add_input("WYLD", wyld)
                h.add_input("REVAP", revap)
                h.add_input("SAST",sast)
                h.add_input("DAST",dast)
                h.add_input("TLOSS",tloss)
                h.add_input("SNOMELT",snowmelt)
                h.add_input("SURQRCH", surqrch)
                h.add_input("GWQ",gwq)
                h.add_input("DGWQ",dgwq)

    def scan_lc_pollutants(self):
        print("Loading SWAT_LC pollutant parameters...")
        flist = glob.glob(self.lcdir + "\*.plt")
        if len(flist) > 1:
            raise RuntimeError("There are more than 1 pollutant setting files in the project folder.")
        elif len(flist) == 0:
            raise FileNotFoundError("There is no SWAT_LC pollutant setting file in the folder.")
        pltfile = flist[0]
        df = pd.read_csv(pltfile,header=0)
        if "DOC" not in df["POLLUTANT"].values:
            raise RuntimeError("There is not DOC settings in the .plt file, it is a mandatory pollutant species.")
        for r in df.itertuples():
            if getattr(r,"POLLUTANT") == "DOC":
                obj = DOC("DOC")
                obj.hlw = getattr(r,"hlw")
                obj.hls = getattr(r,"hls")
                obj.dwat = 0.693 / obj.hlw
                obj.dsoil = 0.693 / obj.hls
                obj.cprep = getattr(r,"cprep")
                obj.flux = float(getattr(r,"riverflux"))
            else:
                obj = PAH(getattr(r,"POLLUTANT"))
                obj.hlw = getattr(r,"hlw")
                obj.hls = getattr(r,"hls")
                obj.dwat = 0.693 / obj.hlw
                obj.dsoil = 0.693 / obj.hls
                obj.koc = 10**float(getattr(r,"logkoc"))
                obj.kdoc = 10**float(getattr(r,"logkdoc"))
                obj.cprep = getattr(r,"cprep")
                obj.flux = float(getattr(r, "riverflux"))
            self.pollutants.append(obj)

    def scan_lc_landuse(self):
        #print("Loading SWAT_LC landuse parameters...")
        flist = glob.glob(self.lcdir + "\*.lu")
        if len(flist) > 1:
            raise RuntimeError("There are more than 1 landuse setting files in the project folder.")
        elif len(flist) == 0:
            raise FileNotFoundError("There is no SWAT_LC landuse setting file in the folder.")
        lufile = flist[0]
        df = pd.read_csv(lufile,header=0)
        luvalues = list(set(df["LANDUSE"].values))
        for l in luvalues:
            sdf = df[df["LANDUSE"] == l]
            luobj = Landuse(name=l)
            for r in sdf.itertuples():
                luobj.bmax[getattr(r,"POLLUTANT")] = getattr(r,"bmax")
                luobj.kbu[getattr(r, "POLLUTANT")] = getattr(r, "kbu")
                luobj.nbu[getattr(r, "POLLUTANT")] = getattr(r, "nbu")
                luobj.kwov[getattr(r, "POLLUTANT")] = getattr(r, "kwov")
                luobj.nwov[getattr(r, "POLLUTANT")] = getattr(r, "nwov")
                luobj.kwoh[getattr(r, "POLLUTANT")] = getattr(r, "kwoh")
                luobj.nwoh[getattr(r, "POLLUTANT")] = getattr(r, "nwoh")
            self.lu[l] = luobj

    def scan_lc_sol(self):
        print("Loading SWAT_LC soil parameters...")
        flist = glob.glob(self.lcdir + "\*.sol")
        if len(flist) > 1:
            raise RuntimeError("There are more than 1 pollutant setting files in the project folder.")
        elif len(flist) == 0:
            raise FileNotFoundError("There is no SWAT_LC soil setting file in the folder.")
        solfile = flist[0]
        df = pd.read_csv(solfile, header=0)
        if "DOC" not in df["POLLUTANT"].values:
            raise RuntimeError("There is not DOC settings in the .sol file, it is a mandatory pollutant species.")
        plist = list(set(df["POLLUTANT"].values))
        slist = list(set(df["SOIL"].values))
        for s in slist:
            obj = Soil(s)
            for p in plist:
                row = df[(df["SOIL"]==s) & (df["POLLUTANT"]==p)]
                obj.fdoc[p] = float(row["fdoc"].values)
                obj.cbase[p] = float(row["cbase"].values)
            self.soils[s] = obj

    def check_conflict(self):
        flist = glob.glob(self.lcdir + "\*.conflict")
        if len(flist) > 1:
            raise RuntimeError("There are more than 1 conflict setting files in the project folder.")
        elif len(flist) == 0:
            raise FileNotFoundError("There is no SWAT_LC conflict setting file in the folder.")
        conflictf = flist[0]
        df = pd.read_csv(conflictf, header=0)
        conflictsoil = list(set(df["SOIL"].values))
        for s in self.sublist:
            for h in s.hrulist:
                if h.soiltype in conflictsoil:
                    if len(df[(df["SOIL"]==h.soiltype) & (df["LU"]==h.lu)])>0:
                        h.soiltype = df[(df["SOIL"]==h.soiltype) & (df["LU"]==h.lu)]["RSOIL"].values[0]
                        h.lutype = df[(df["SOIL"] == h.soiltype) & (df["LU"] == h.lu)]["RLU"].values[0]
                    elif df[df["SOIL"]==h.soiltype]["LU"].values[0] =="ANY":
                        h.soiltype = df[df["SOIL"] == h.soiltype]["RSOIL"].values[0]
                        h.lu = df[df["SOIL"] == h.soiltype]["RLU"].values[0]

    def ini_state_vars(self):
        print("Initializing SWAT_LC state variables...")
        for s in self.sublist:
            for p in self.pollutants:
                substvar = StateVariables(p.name)
                s.add_state_vars(p.name, substvar)
                for h in s.hrulist:
                        hrustvar = StateVariables(p.name)
                        h.add_state_vars(p.name,hrustvar)

    def set_ini_cond(self):
        print("Setting initial conditions...")
        # scan the global initial condition settings
        flist = glob.glob(self.lcdir + "\*.init")
        if len(flist) > 1:
            raise RuntimeError("There are more than 1 initial condition files in the project folder.")
        if len(flist) == 1:
            condfile = flist[0]
            df = pd.read_csv(condfile,header=0)
            for s in self.sublist:
                for h in s.hrulist:
                    for p in self.pollutants:
                        if self.initype == "SOIL":
                            inir = df[(df["SOIL"] == h.soiltype) & (df["POLLUTANT"] == p.name)]
                        elif self.initype == "LU":
                            inir = df[(df["LANDUSE"] == h.lu) & (df["POLLUTANT"] == p.name)]
                        elif self.initype == "SOIL-LU":
                            inir = df[(df["LANDUSE"] == h.lu) & (df["SOIL"] == h.soiltype) & (df["POLLUTANT"] == p.name)]
                        else:
                            raise NotImplementedError("The setting of initial condition only accepts SOIL, LU, or SOIL-LU.")
                        if len(inir) > 0:
                            ctsoil = float(inir["ctsoil"].values)
                            msoil = ctsoil * h.vsoil / 10**9    # kg
                            h.stvars[p.name].msoil = msoil

        # scan the user defined initial condition settings
        # the user-specific settings have higher priority
        fusrlist = glob.glob(self.lcdir + "\*.usrinit")
        if len(fusrlist) > 1:
            raise RuntimeError("There are more than 1 user-specific initial condition files in the project folder.")
        if len(fusrlist) == 1:
            usrfile = fusrlist[0]
            df2 = pd.read_csv(usrfile,header=0)
            subdf2 = df2[df2["CTLTYPE"]=="SUB"]
            hrudf2 = df2[df2["CTLTYPE"]=="HRU"]
            subval = subdf2["ID"].values
            hruval = hrudf2["ID"].values
            if len(subdf2.index) > 0:
                for s in self.sublist:
                    if s.name in subval:
                        for p in self.pollutants:
                            row = subdf2[(subdf2["ID"]==s.name) & (subdf2["POLLUTANT"]==p.name)]
                            if len(row.index) == 1:  # only valid if there is no conflict
                                for sh in s.hrulist:
                                    ctsoil = float(row["ctsoil"].values)
                                    msoil = ctsoil * sh.vsoil / 10 ** 9  # kg
                                    sh.stvars[p.name].msoil = msoil
                            elif len(row.index) > 1:
                                raise UserWarning("There are some conflicts in the user-specific sub-basin ini condition settings.")

            if len(hrudf2.index) > 0:
                for s in self.sublist:
                    for sh in s.hrulist:
                        if sh.id in hruval:
                            for p in self.pollutants:
                                row = hrudf2[(hrudf2["ID"] == sh.id) & (hrudf2["POLLUTANT"] == p.name)]
                                if len(row.index) == 1:  # only valid if there is no conflict
                                    ctsoil = float(row["ctsoil"].values)
                                    msoil = ctsoil * sh.vsoil / 10 ** 9  # kg
                                    sh.stvars[p.name].msoil = msoil
                                elif len(row.index) > 1:
                                    raise UserWarning("There are some conflicts in the user-specific hru ini condition settings.")


    def _pollutant_sequence(self):
        for p in self.pollutants:
            if p.name == "DOC":
                id = self.pollutants.index(p)
                if id != 0:
                    self.pollutants.insert(0, self.pollutants.pop(id))
                    break


    def scan_usr_lu_params(self):
        # scan the user-defined LU parameters (designed for regional variability)
        usrluflist = glob.glob(self.lcdir + "\*.usrlu")
        if len(usrluflist) > 1:
            raise RuntimeError("There are more than 1 user-specific initial condition files in the project folder.")
        if len(usrluflist) == 1:
            usrlu = usrluflist[0]
            df = pd.read_csv(usrlu, header=0)
            subdf = df[df["CTLTYPE"]=="SUB"]
            hrudf = df[df["CTLTYPE"]=="HRU"]
            subval = subdf["ID"].values
            hruval = hrudf["ID"].values
            for s in self.sublist:
                if s.name in subval:
                    for p in self.pollutants:
                        row = subdf[(subdf["ID"] == s.name) & (subdf["POLLUTANT"] == p.name)]
                        if len(row.index) == 1:  # only valid if there is no conflict
                            for sh in s.hrulist:
                                sh.usrlu[p.name] = True
                                sh.bmax[p.name] = float(row["bmax"].values)
                                sh.kbu[p.name] = float(row["kbu"].values)
                                sh.nbu[p.name] = float(row["nbu"].values)
                                sh.kwov[p.name] = float(row["kwov"].values)
                                sh.nwov[p.name] = float(row["nwov"].values)
                                sh.kwoh[p.name] = float(row["kwoh"].values)
                                sh.nwoh[p.name] = float(row["nwoh"].values)

                        else:
                            for sh in s.hrulist:
                                sh.usrlu[p.name] = False

                else:
                    for sh in s.hrulist:
                        for p in self.pollutants:
                            sh.usrlu[p.name] = False

                # overwrite the sub-basin setting using the hru setting
                for sh in s.hrulist:
                    if sh.id in hruval:
                        for p in self.pollutants:
                            rowadv = hrudf[(hrudf["ID"] == sh.id) & (hrudf["POLLUTANT"] == p.name)]
                            if len(rowadv.index) == 1:
                                sh.usrlu[p.name] = True
                                sh.bmax[p.name] = float(rowadv["bmax"].values)
                                sh.kbu[p.name] = float(rowadv["kbu"].values)
                                sh.nbu[p.name] = float(rowadv["nbu"].values)
                                sh.kwov[p.name] = float(rowadv["kwov"].values)
                                sh.nwov[p.name] = float(rowadv["nwov"].values)
                                sh.kwoh[p.name] = float(rowadv["kwoh"].values)
                                sh.nwoh[p.name] = float(rowadv["nwoh"].values)

        else:
            for s in self.sublist:
                for p in self.pollutants:
                    for sh in s.hrulist:
                        sh.usrlu[p.name] = False

    def scan_usr_flux(self):
        usrfluxflist = glob.glob(self.lcdir + "\*.usrflux")
        if len(usrfluxflist) > 1:
            raise RuntimeError("There are more than 1 user-specific flux setting files in the project folder.")
        if len(usrfluxflist) == 1:
            usrflux = usrfluxflist[0]
            df = pd.read_csv(usrflux, header=0)
            subval = df["RCH"].values
            for s in self.sublist:
                if s.name in subval:
                    for p in self.pollutants:
                        row = df[(df["RCH"] == s.name) & (df["POLLUTANT"] == p.name)]
                        if len(row.index) == 1:
                            s.usrflux[p.name] = True
                            s.cprep[p.name] = float(row["cprep"].values)
                            s.riverflux[p.name] = float(row["riverflux"].values)
                        else:
                            s.usrflux[p.name] = False
                else:
                    for p in self.pollutants:
                        s.usrflux[p.name] = False
        else:
            for s in self.sublist:
                for p in self.pollutants:
                    s.usrflux[p.name] = False



class SUBBASIN:

    def __init__(self,name):
        self.name = name
        self.hrulist = []
        self.NORparam = {}
        self.area = self.scan_param()
        self.input = {}
        self.stvars = {}
        self.watsurf = 0
        self.usrflux = {}
        self.cprep = {}
        self.riverflux = {}


    def scan_hru(self,subname,subarea):
        hrupath = glob.glob("{}*.hru".format(str(self.name).zfill(5)))
        for p in hrupath:
            hruname = int(p[5:9])
            hruobj = HRU(subname,subarea,hruname)
            self.hrulist.append(hruobj)

    def scan_param(self):
        fname = str(self.name).zfill(5) + "0000"
        fsub = ParamIO(fname + ".sub")
        area = fsub.parameters["SUB_KM"]
        self.NORparam["SUB_KM"] = fsub.parameters["SUB_KM"]
        self.NORparam["CH_L1"] = fsub.parameters["CH_L1"]
        self.NORparam["CH_S1"] = fsub.parameters["CH_S1"]
        self.NORparam["CH_W1"] = fsub.parameters["CH_W1"]
        self.NORparam["CH_N1"] = fsub.parameters["CH_N1"]
        return area

    def __repr__(self):
        names = []
        for i in self.hrulist:
            names.append("HRU{}".format(i.name))
        hruinfo = ",".join(names)
        return f"SUB{self.name}({hruinfo})"

    def add_state_vars(self, name, objvars):
        """
        :param name: pollutant name
        :param objvars: state variables for a given pollutant
        :return:
        """
        self.stvars[name] = objvars

    def add_input(self, varname, dataseries):
        """
        Load the input series (SWAT result series).
        :param varname:
        :param dataseries:
        :return:
        """
        self.input[varname] = dataseries


class HRU:

    def __init__(self, subname,subarea,name):
        """
        HRU class for SWAT_LC calculation.
        :param name: code of the HRU in
        """
        self.sub = subname
        self.name = name
        self.id = None
        self.lu = None
        self.soiltype = None
        self.NORparam = {}  # Normal Parameter
        self.GWparam = {}   # Ground Parameter
        self.SOLparam = {}  # Soil Parameter
        self.scan_param()
        self.area = subarea * self.NORparam["HRU_FR"]
        self.vsoil = self.area * self.SOLparam["DEPTH"] * 1000  # unit: m3
        self.msolid = 1000 * self.vsoil * self.SOLparam["SOLBD"] * (1 - self.SOLparam["ROCK"]/100)  # unit: g/cc-> ton/m3 * m3 -> ton -》 1000 kg
        self.morgc = self.msolid * self.SOLparam["ORGC"]/100 # kg  # orgc ratio/100
        self.input = {}
        self.stvars = {}
        self.usrlu = {}
        self.bmax = {}
        self.kbu = {}
        self.nbu = {}
        self.kwov = {}
        self.nwov = {}
        self.kwoh = {}
        self.nwoh = {}


    def __repr__(self):
        return f"HRU{self.name}"

    def scan_param(self):
        fname = str(self.sub).zfill(5) + str(self.name).zfill(4)

        fhru = ParamIO(fname + ".hru")
        self.NORparam["HRU_FR"] = fhru.parameters["HRU_FR"]         # Fraction of subbasin area contained in HRU
        self.NORparam["HRU_SLP"] = fhru.parameters["HRU_SLP"]       # Slope stepness [m/m]
        self.NORparam["SLSOIL"] = fhru.parameters["SLSOIL"]         # Slope length for lateral subsurface flow [m]
        self.NORparam["SLSUBBSN"] = fhru.parameters["SLSUBBSN"]     # Average slope length [m]
        self.NORparam["LAT_TTIME"] = fhru.parameters["LAT_TTIME"]   # Lateral flow trave time [days]
        self.NORparam["HRU_FR"] = fhru.parameters["HRU_FR"]         # Fraction of subbasin area contained in HRU
        self.NORparam["SURLAG"] = fhru.parameters["SURLAG"]         # Surface runoff lag coeff of the HRU
        self.NORparam["OV_N"] = fhru.parameters["OV_N"]             # Manning's n for the overland flow
        self.lu = fhru.lu
        self.id = fhru.id
        self.soiltype = fhru.soiltype

        fgw = ParamIO(fname + ".gw")
        self.GWparam["SHALLST"] = fgw.parameters["SHALLST"]         # Initial depth of water in the shallow aquifer [mm]
        self.GWparam["GW_DELAY"] = fgw.parameters["GW_DELAY"]       # Groundwater delay [days]
        self.GWparam["GW_SPYLD"] = fgw.parameters["GW_SPYLD"]       # Specific yield of the shallow aquifer [m3/m3]
        self.GWparam["RCHRG_DP"] = fgw.parameters["RCHRG_DP"]       # Deep aquifer percolation fraction

        fsol = ParamIO(fname + ".sol")
        # calculate the weighted average parameters for the soil layer to simplify the model structure
        def cal_avg(depths,params):
            curdepth = 0
            thickness = []
            for d in depths:
                t = d - curdepth
                thickness.append(t)
                curdepth = d
            ave_param = np.sum(np.array(params) * np.array(thickness)/np.sum(thickness))
            return ave_param

        self.SOLparam["DEPTH"] = max(fsol.parameters["Depth                [mm]"])
        self.SOLparam["SOLBD"] = cal_avg(fsol.parameters["Depth                [mm]"], fsol.parameters["Bulk Density Moist [g/cc]"])
        self.SOLparam["KSAT"] = cal_avg(fsol.parameters["Depth                [mm]"], fsol.parameters["Ksat. (est.)      [mm/hr]"])
        self.SOLparam["ORGC"] = cal_avg(fsol.parameters["Depth                [mm]"], fsol.parameters["Organic Carbon [weight %]"])
        self.SOLparam["ROCK"] = cal_avg(fsol.parameters["Depth                [mm]"],fsol.parameters["Rock Fragments   [vol. %]"])

    def add_input(self, varname, dataseries):
        """
        Load the input series (SWAT result series).
        :param varname:
        :param dataseries:
        :return:
        """
        self.input[varname] = dataseries

    def add_state_vars(self, name, objvars):
        """
        :param name: pollutant name
        :param objvars: state variables for a given pollutant
        :return:
        """
        self.stvars[name] = objvars


class StateVariables:

    def __init__(self,name):

        self.name = name

        # State variables for calculation
        self.maccu = 0      # Accumulated mass on the surface (kg)
        self.msurf = 0      # Mass in the generated surface runoff (kg)
        self.mlat = 0       # Mass in the generated lateral flow (kg)
        self.mper = 0       # Mass in the percolating water (kg)
        self.msurfstor = 0  # Mass stored in the surface runoff that is still traveling to the river channel (kg)
        self.mlatstor = 0   # Mass stored in the lateral flow that is still traveling to the river channel (kg)
        self.mperstor = 0
        self.msoil = 0      # Mass in the soil (kg)
        self.msa = 0        # Mass in the shallow aquifer (kg)
        self.mda = 0        # Mass in the deep aquifer (kg)
        self.mrevap = 0     # Mass moving into the soil due to the water deficiencies (kg)
        self.csurf = 0      # Pollutant concentration in the generated surface runoff (ng/L)
        self.ctsoil = 0     # Total concentration of the pollutant in the soil (ng/L)
        self.cpsoil = 0     # Solid phase pollutant concentration in the soil (ng/L)
        self.cdsoil = 0     # Dissolved phase pollutant concentration in the soil (ng/L)
        self.cdocsoil = 0   # DOC phase pollutant concentration in the soil (ng/L)
        self.csaq = 0       # Pollutant concentration in the shallow aquifer (ng/L)
        self.cdaq = 0       # Pollutant concentration in the deep aquifer (ng/L)
        self.cw = 0         # Pollutant concentration in the soil water (cw * theta = cdsoil, mg/L)
        self.drydays = 0    # dry days for mass accumulation

        # Output variables
        self.out_msurf = 0  # Mass in the surface runoff to the river channel (DOC:kg, PAH:mg)
        self.out_mlat = 0   # Mass in the lateral flow to the river channel (DOC:kg, PAH:mg)
        self.out_mgw = 0    # Mass in the ground water flow to the river channel (DOC:kg, PAH:mg)
        self.out_mdgw = 0
        self.out_mrchflux = 0  # Mass to the river channel
        self.out_mt = 0     # Total mass flow into the reach (kg)
        self.out_concs = 0  # Final concentration in the surface runoff to the reach (ng/L)
        self.out_concl = 0  # Final concentration in the lateral flow to the reach (ng/L)
        self.out_concg = 0  # Final concentration in the groundwater to the reach (ng/L)
        self.out_conct = 0  # Final concentration in the total water yield (ng/L)


    def reset0(self):
        for attr in dir(self):
            if "__" not in attr and "reset0" not in attr and attr != "name":
                self.__setattr__(attr,0)



"""
scanner = PROJmanager(r"D:\SWATcalibration\process1",r"D:\SWAT_LC")
"""

