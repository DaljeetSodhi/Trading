import pandas as pd
import GlobalVars as gv
import GraphUtils as gu
import TradeUtils as tu
import OtherUtils as ou
import datetime as dt
import yfinance as yf
import StrategyUtils as su


#%matplotlib qt5
"""
print('Process Started ', dt.datetime.now())
Stock='BHEL.NS'
StockData=pd.read_csv(gv.HistDir+Stock+'.csv', index_col=0)
gu.DrawGraphs(Stock, StockData)
"""
#print(tu.GetDailyData(['NMDC.NS'], 3))


#su.FindFnOCircuits()
DaysData=tu.ProcessDaysData()
#print(DaysData[['Stock','Close','YHigh', 'YLow','YLHP','DHigh1P', 'DLow1P']])
#tu.DayAnalysis(DaysData)

"""
print('Getting FnO list')
FnO=ou.GetFnOList()
FnO=FnO.head()
print('Getting Market Cap')
Attrib=tu.GetAttrib(FnO)
print(Attrib)

DaysData=tu.AddDaysInfo(FnO)

#    su.FindND30mMove(DaysData, PrevDays)
#tu.DisplayData(DaysData, 'Day','Short')
#tu.DisplayData(DaysData, 'Day','Long')
#CombData=tu.AddIntraDay(DaysData, '15m')
#tu.DisplayData(CombData, 'Intra', 'Short')
#print(BulkData.head(1))
"""