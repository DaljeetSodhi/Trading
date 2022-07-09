import pandas as pd
import numpy as np
import os
pd.options.mode.chained_assignment = None  # default='warn'

import datetime as dt
import GlobalVars as gv
import OtherUtils as ou
import StockUtils as su
import TradeUtils as tu
#from yahoo_fin import stock_info as si
from nsetools import Nse
import talib
import yfinance as yf

def FindND30mMove(DaysData, ToPrevDays = 0):
# to find out opening 30 min percentage high movement of stocks 
    ListOfStocks=' '.join(DaysData['Stock'].tolist())

    print(DaysData.tail(1))
    Start=dt.datetime.now() - dt.timedelta(days=abs(ToPrevDays))
    End=Start+dt.timedelta(days=2)
    Start = Start.strftime('%Y-%m-%d'); End = End.strftime('%Y-%m-%d')
    print(Start, End)
    BulkData=yf.download(ListOfStocks, start=Start, end = End, interval='30m')
    ND15m=BulkData['High'].tail(1); ND15m=ND15m.melt(); ND15m.columns=['Stock','ND30m']  
    Data = pd.merge(DaysData, ND15m, on=['Stock'], how='left')
    Data['ND30mHP']=round((Data['ND30m'] - Data['Close'])*100/Data['Close'],1)
    #print(Data['ND30mHP'])
    
    tu.DisplayData(Data, 'Day','Short')# need to add ND30mHP column in DisplayData
    return()

def FindFnOCircuits():
    FnOList=ou.GetFnOList()
    ListOfStocks=' '.join(FnOList['Stock'].tolist())
    Start=dt.datetime.now() - dt.timedelta(days=abs(185));  Start = Start.strftime('%Y-%m-%d')
    End=dt.datetime.now();  End = End.strftime('%Y-%m-%d')

    BulkData=yf.download(ListOfStocks, start=Start, end=End)
    PDClose=pd.DataFrame(); DayHighP=pd.DataFrame(); DayLowP=pd.DataFrame()
    for Col in BulkData['Close'].columns:
        PDClose[Col]=BulkData['Close'][Col].shift(1)
    for Col in BulkData['Close'].columns:
        DayHighP[Col]= round((BulkData['High'][Col] - PDClose[Col])*100 / BulkData['High'][Col],2)
        DayLowP[Col]= round((BulkData['Low'][Col] - PDClose[Col])*100 / BulkData['Low'][Col],2)
    
    Count=0
    for i, Row in DayHighP.iterrows():
        Stocks=''
        for Col in DayHighP.columns:
            if(Row[Col] >= 9) : 
                Stocks += (' ' + Col + ' ' + str(Row[Col]));Count += 1
        if(len(Stocks) > 0): print(i.date() , Stocks)
    print(Start, End, 'Total Count', Count)
    