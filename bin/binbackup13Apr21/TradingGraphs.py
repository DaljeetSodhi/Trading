# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 16:11:46 2020

@author: dsodh
"""

import pandas as pd
import GlobalVars as gv
import GraphUtils as gu
import TradeUtils as tu
import OtherUtils as ou
import datetime as dt

FnO=ou.GetFnOList()
DaysData=tu.AddDaysInfo(FnO)
#tu.DisplayData(DaysData, 'Day','Short')
#print('Shape of Data : ', DaysData.shape)
#DaysData=DaysData[DaysData['RSI'] >= 40]
#print('After filter Shape of Data : ', DaysData.shape)
CombData=tu.AddIntraDay(DaysData, '15m')
#CombData=tu.AddPerCols(CombData, 'I')
#print('Columns : ', CombData.columns)
tu.DisplayData(CombData, 'Intra', 'Short')
print('Process Finished ', dt.datetime.now())

"""
ToTrade = gv.RptDir+'0'+gv.RepFiles['ToTrade']    
ToTrade=pd.read_csv(ToTrade)
for i, Row in ToTrade.iterrows():
    gu.DrawGraphForStock(Row['Stock'])
"""