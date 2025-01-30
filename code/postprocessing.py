import glob

import pandas as pd
import geopandas as gpd
import resultreader
import numpy as np
import swat_param


def lcsubout2shp(tarshp,subout):
    shp = gpd.read_file(tarshp)
    subs = shp["Subbasin"].values
    areas = shp["Area"].values
    lcres = resultreader.LCreader(subout)
    pollutants = set(lcres.metadata["POLLUTANT"].values)
    for p in pollutants:
        loadpa = []  # mg/(km2*day)
        sur_ratio = []
        lat_ratio = []
        gw_ratio = []
        flux_ratio = []
        for id,s in enumerate(subs):
            total = lcres.inquireDataItem(s,p,"MTkg")
            sur = lcres.inquireDataItem(s, p, "MSURkg")
            lat = lcres.inquireDataItem(s,p,"MLATkg")
            sgw = lcres.inquireDataItem(s,p,"MGWkg")
            dgw = lcres.inquireDataItem(s, p, "MDGWkg")
            allgw = sgw + dgw
            flux = lcres.inquireDataItem(s, p, "MFLUXkg")
            s_total = np.sum(total)
            s_sur = np.sum(sur)
            s_lat = np.sum(lat)
            s_gw = np.sum(allgw)
            s_flux = np.sum(flux)
            r_sur = s_sur/s_total
            r_lat = s_lat/s_total
            r_gw = s_gw/s_total
            r_flux = s_flux/s_total
            lpa = 1000000 * np.average(total) / areas[id]

            sur_ratio.append(r_sur)
            lat_ratio.append(r_lat)
            gw_ratio.append(r_gw)
            flux_ratio.append(r_flux)
            loadpa.append(lpa)

        shp[r"LPA_{}".format(p)] = loadpa
        shp["rSur_{}".format(p)] = sur_ratio
        shp["rLat_{}".format(p)] = lat_ratio
        shp["rGw_{}".format(p)] = gw_ratio
        shp["rFlx_{}".format(p)] = flux_ratio
    shp.to_file(tarshp)

def waspconc2shp(tarshp,waspout):
    df = pd.read_csv(waspout,index_col=0)
    shp = gpd.read_file(tarshp)
    reachid = shp["Subbasin"].values
    polluts = ["CHR","NAP"]
    for ip,p in enumerate(polluts):
        concs = []
        stds = []
        for s in reachid:
            data = np.average(df["Reach{}-({})-Total Chemical".format(s,ip+1)])*10**6
            std = np.std(df["Reach{}-({})-Total Chemical".format(s,ip+1)]*10**6)
            concs.append(data)
            stds.append(std)
        shp["{}_Conc".format(p)] = concs
        shp["{}_STD".format(p)] = stds
    shp.to_file(tarshp)

def lcsoilini2shp(tarshp,swatdir,lcdir):

    def cal_avg(depths, params):
        curdepth = 0
        thickness = []
        for d in depths:
            t = d - curdepth
            thickness.append(t)
            curdepth = d
        ave_param = np.sum(np.array(params) * np.array(thickness) / np.sum(thickness))
        return ave_param

    shp = gpd.read_file(tarshp)
    hrugis = shp["HRU_GIS"].values
    lcini = glob.glob(lcdir+"\\*.init")[0]
    lcusrini = glob.glob(lcdir+"\\*.usrinit")[0]
    lcplt = glob.glob(lcdir+"\\*.plt")[0]
    dfplt = pd.read_csv(lcplt)
    dfini = pd.read_csv(lcini)
    dfusrini = pd.read_csv(lcusrini)
    pollutants = dfplt["POLLUTANT"].values

    """"""
    for p in pollutants:
        ctsoil = []
        converted = []
        for h in hrugis:
            hrufile = swatdir + "\\{}.hru".format(h)
            solfile = swatdir + "\\{}.sol".format(h)
            hruparam = swat_param.ParamIO(hrufile)
            solparam = swat_param.ParamIO(solfile)
            globalini = dfini[(dfini["LANDUSE"] == hruparam.lu) & (dfini["SOIL"] == hruparam.soiltype) & (dfini["POLLUTANT"] == p)]
            if globalini.empty is True:
                globalini = 0
            else:
                globalini = float(globalini["ctsoil"].values)
            usrini = dfusrini[(dfusrini["CTLTYPE"] == "SUB") & (dfusrini["ID"] == hruparam.subid) & (dfusrini["POLLUTANT"] == p)]
            if usrini.empty is not True:
                globalini = float(usrini["ctsoil"].values)
            usrini_hru = dfusrini[(dfusrini["CTLTYPE"] == "HRU") & (dfusrini["ID"] == hruparam.id) & (dfusrini["POLLUTANT"] == p)]
            if usrini_hru.empty is not True:
                globalini = float(usrini_hru["ctsoil"].values)
            ctsoil.append(globalini)
            solbd = cal_avg(solparam.parameters["Depth                [mm]"],solparam.parameters["Bulk Density Moist [g/cc]"])
            conc = globalini * 1000/(solbd * 1000000)       # ng/g
            converted.append(conc)
        shp["{}_ngL".format(p[0:3])] = ctsoil
        shp["{}_ngg".format(p[0:3])] = converted
    shp.to_file(tarshp)

