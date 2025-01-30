# Author: Qianyang Wang
import re


class ParamIO:

    def __init__(self,fpath):
        self.hnd = open(fpath , "r+")
        self.TorNP_locs = [] # locations of title or terms that are not general param
        self.P_locs = [] # locations of general params
        self.TorNP = []
        self.parameters = {}
        self.paratypes = {}
        self.descriptions = {}
        if "sol" in fpath:
            self.sol = True
            self._parsesol(self.hnd)
        elif "hru" in fpath:
            self.lu = self._get_lu_label(self.hnd)
            self.id = self._get_hruid(self.hnd)
            self.subid = self._get_subid(self.hnd)
            self.soiltype =  self._get_soiltype(self.hnd)
            self._parse(self.hnd)
        else:
            self.sol = False
            self._parse(self.hnd)

    def _parse(self,fhnd):
        content = fhnd.readlines()
        for i,r in enumerate(content):
            if "|" not in r or r[0] == "|":
                self.TorNP_locs.append(i)
                self.TorNP.append(r)
            else:
                self.P_locs.append(i)
                value,oth = r.split("|")
                value = value.strip()
                name,des = oth.split(":",1)
                name = name.strip()
                if not value.isdecimal(): # not integer -> float or char
                    if self._isfloat(value):
                        ldec = len(value.split(".")[1])
                        self.paratypes[name] = (float,ldec)
                        self.parameters[name] = round(float(value),ldec)
                    else:
                        self.paratypes[name] = str
                        self.parameters[name] = value
                else:
                    self.paratypes[name] = int
                    self.parameters[name] = int(value)
                self.descriptions[name] = des

    def _parsesol(self,fhnd):
        content = fhnd.readlines()
        for i,r in enumerate(content):
            if i < 7: # title & basic soil info
                self.TorNP_locs.append(i)
                self.TorNP.append(r)
            else:
                if ":" in r:
                    # 2 or more columns due to different soil layers, only consider the first layer for calibration
                    self.P_locs.append(i)
                    name, tvalue = r.split(":")
                    name = name.strip()
                    values = tvalue.split(" ")
                    tvalues = [i for i in values if i != "" and i != "\n"]
                    rep = tvalues[0]
                    if not rep.isdecimal(): # not integer -> float or char
                        if self._isfloat(rep):
                            ldec = len(rep.split(".")[1])
                            self.paratypes[name] = (float,ldec)
                            self.parameters[name] = [round(float(i),ldec) for i in tvalues]
                        else:
                            self.paratypes[name] = str
                            self.parameters[name] = tvalues
                    else:
                        self.paratypes[name] = int
                        self.parameters[name] = [int(i) for i in tvalues]

    def _isfloat(self,string):
        pattern = r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$'
        return bool(re.match(pattern,string))

    def _get_lu_label(self,fhnd):
        line = fhnd.readlines()[0]
        lbl = re.findall(".*?Luse:(.*?) Soil:.*?",line)[0]
        fhnd.seek(0)
        return lbl

    def _get_hruid(self,fhnd):
        line = fhnd.readlines()[0]
        hruid = re.findall(".*?HRU:(.*?) Subbasin:.*?", line)[0]
        fhnd.seek(0)
        return int(hruid)

    def _get_subid(self,fhnd):
        line = fhnd.readlines()[0]
        subid = re.findall(".*?HRU:.*? Subbasin:(.*?) ", line)[0]
        fhnd.seek(0)
        return int(subid)

    def _get_soiltype(self,fhnd):
        line = fhnd.readlines()[0]
        soiltype = re.findall(".*?Soil:(.*?) Slope:.*?", line)[0]
        soiltype = soiltype.strip()
        fhnd.seek(0)
        return soiltype



