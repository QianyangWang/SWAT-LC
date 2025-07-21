# Author: Qianyang Wang
import pandas as pd
import numpy as np
import mysql.connector
from sqlalchemy import create_engine


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

    def toWASP8dbMySQL(self, db_config=None):
        """
        :param db_config:
                db_config: 数据库配置字典，格式:
            {
                'host': 'localhost',
                'user': 'username',
                'password': 'password',
                'database': 'SWATLC_SSP126_2050s',
                'table':"chrnap"
            }
        :return:
        """


        if not "subout" in self.path:
            raise NotImplementedError("The current version only accepts the sub-basin output.")

        data = self.metadata.iloc[:, 0:3].copy()
        data["SUB"] = data["SUB"].map(lambda x: f"Reach{x}")
        data = data.reset_index()
        data = data.rename(columns={
            "DATE":"TIME",
            "SUB": "STATION",
            "POLLUTANT": "VARIABLE",
            "MTkg": "VALUE"
        })
        data["TIME"] = pd.to_datetime(data["TIME"]).dt.strftime("%-m/%-d/%Y") #WASP time format
        engine = create_engine('mysql+pymysql://{}:{}@{}:3306/{}'.format(db_config["user"],db_config["password"],
                                                                          db_config["host"],db_config["database"]))
        data.to_sql(db_config["table"], con=engine, if_exists='append', index=False)




