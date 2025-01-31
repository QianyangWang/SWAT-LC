# Author: Qianyang Wang
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np



class LCreader:

    def __init__(self,path):
        self.path = path
        self.metadata = self.readout()

    def readout(self):
        metadata = pd.read_csv(self.path,index_col=0,header=0)
        return metadata

    def inquireDataItem(self,id,pollutantname,itemname):
        if "hruout" in self.path:
            df = self.metadata[(self.metadata["HRU"] == id) & (self.metadata["POLLUTANT"] == pollutantname)][itemname]
        else:
            df = self.metadata[(self.metadata["SUB"] == id) & (self.metadata["POLLUTANT"] == pollutantname)][itemname]
        #arr = np.array(df).flatten()
        return df

    def toWASP8db(self,path=None):
        if not "subout" in self.path:
            raise NotImplementedError("The current version only accept the sub-basin output.")
        else:
            data = self.metadata.iloc[:,0:3]
            data["SUB"] = data["SUB"].map(lambda x: "Reach{}".format(x))
            data["SUB"].rename("STATION")
            data["POLLUTANT"].rename("VARIABLE")
            data["MTkg"].rename("VALUE")
            if path:
                data.to_excel(path)
            else:
                data.to_excel("SWATLC_WASPDB.xlsx")






