# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 10:11:53 2020

@author: dsodh
"""
import pandas as pd
import numpy as np
import os
pd.options.mode.chained_assignment = None  # default='warn'

import time
import datetime as dt
import GlobalVars as gv
import OtherUtils as ou
#from yahoo_fin import stock_info as si
from nsetools import Nse
import talib
import yfinance as yf

def GetListToTrade():
    FP=dt.datetime.now().weekday()

    ToTradeFN = gv.RptDir+str(FP)+gv.RepFiles['ToTrade']  
    print('Reading File :',ToTradeFN , ' (Created on) : ', 
          dt.datetime.fromtimestamp(os.path.getmtime(ToTradeFN)))
    ToTrade=pd.read_csv(ToTradeFN)
    FnOList=GetFnOList()
    ToTrade = pd.merge(ToTrade, FnOList, on=['Stock'], how='left')
    ToTrade['Lot']=round(ToTrade['LastClose']*ToTrade['Lot']/100000,1)

    ColsToDisp=gv.TechIndToDisp+['Lot']
    print(ToTrade.to_string(columns=ColsToDisp, index=False))
    return(ToTrade)

def GetLTP(ToTrade):
    nse = Nse()
    Stocks=ToTrade['Stock'].to_list()
    Stocks = [x[:-3] for x in Stocks]   
    Stocks = {stock:nse.get_quote(stock)['lastPrice'] for stock in Stocks}
    Stocks = {key+'.NS': val for key, val in Stocks.items()} 
    ToTrade['LTP'] = ToTrade['Stock'].map(Stocks)
#    ToTrade['Time'] = time.strftime("%H:%M:%S", time.localtime()) 
    return(ToTrade)

def GetFnOList():
    nse = Nse()
    FnO=pd.DataFrame(list(nse.get_fno_lot_sizes().items()), columns=['Stock', 'Lot'])
    FnO=FnO[~FnO.Stock.str.contains("NIFTY")]
    FnO['Stock']=FnO['Stock']+'.NS'
    return(FnO)

def AddDaysInfo(Data):
    print('Start Time : ', dt.datetime.now())
    ListOfStocks=' '.join(Data['Stock'].tolist())
    BulkData=yf.download(ListOfStocks, period='6mo')
    print(BulkData)
    PrevClose=BulkData['Close'].tail(1).melt()
    PrevClose.columns=['Stock','Close']
    Data = pd.merge(Data, PrevClose, on=['Stock'], how='left')
    Data['Close']=round(Data['Close'],2)
    Data['LotValue']=round(Data['Close']*Data['Lot']/100000,1)

    MinCandles=BulkData['Close']
    RSI=pd.DataFrame(); 
    for Cols in MinCandles.columns:
        RSI[Cols]= round(talib.RSI(MinCandles[Cols],timeperiod=gv.RSIPeriod),1)
    RSI=RSI.tail(1); RSI=RSI.melt(); RSI.columns = ['Stock','RSI']
    Data = pd.merge(Data, RSI, on=['Stock'], how='left')
    Data = Data.dropna(axis=0, subset=['RSI']) 
    Data.sort_values(['RSI'], inplace=True)
 
    return(Data) 

def TopCurrGnL(Data):
     print('Start Time : ', dt.datetime.now() , ' .. taking few mins .. ')
     Txn = GetLTP(Data)
     Txn['CurrPer']=round((Txn['LTP'] - Txn['Close'])*100/Txn['Close'],2)
     Txn.sort_values(['CurrPer'], ascending=[False], inplace=True)
     return(Txn)
 
def AddIntraDay(Data, Interval='15m'):

    print('Start Time : ', dt.datetime.now())    
    ListOfStocks=' '.join(Data['Stock'].tolist())
    MinCandles=yf.download(ListOfStocks, period='5d',interval=Interval)
    MinCandles=MinCandles['Close']
   
#bug in yfinance returns nulls in live trading in lastrows
    delta=int(Interval[:-1]); Time = dt.datetime.now() - dt.timedelta(seconds=30)
    Time = Time - (Time - dt.datetime.min) % dt.timedelta(minutes=delta) # round to nearest interval
    MinCandles.index = MinCandles.index.tz_localize(None)
    MinCandles=MinCandles[MinCandles.index <= Time]
    print('Shape of Data : ', MinCandles.shape)
    RSI=pd.DataFrame(); RSIMA=pd.DataFrame()
    for Cols in MinCandles.columns:
        RSI[Cols]= round(talib.RSI(MinCandles[Cols],timeperiod=gv.RSIPeriod),1)
        if(RSI[Cols].isnull().values.all()):
            RSIMA[Cols]=np.NaN
        else:
            RSIMA[Cols]=round(talib.SMA(RSI[Cols], gv.RSIMAPeriod))
    RSI=RSI.tail(1); RSI=RSI.melt(); RSI.columns=['Stock','RSI'+Interval]   
    Data = pd.merge(Data, RSI, on=['Stock'], how='left')
    
    RSIMA=RSIMA.tail(1); RSIMA=RSIMA.melt(); RSIMA.columns=['Stock','RSIMA'+Interval]   
    Data = pd.merge(Data, RSIMA, on=['Stock'], how='left')
   
    Data.sort_values(['RSI'+Interval], inplace=True)

    return(Data) 

def AddLatestToList(ToTrade, Action = 0, RSIInterval=None):

    Txn=GetLTP(ToTrade)
    Txn['DayPer']=round((Txn['LTP'] - Txn['LastClose']) * 100 / Txn['LastClose'],2)
    Txn['PDayPer']=round((Txn['LastClose'] - Txn['Last2Close']) * 100 / Txn['Last2Close'],2)
    Txn['PDay2Per']=round((Txn['LastClose'] - Txn['Last3Close']) * 100 / Txn['Last3Close'],2)

    Txn['Date'] = pd.to_datetime(Txn["Date"]).dt.strftime('%m-%d')
    
    TradingCols = gv.TradingCols
    if (RSIInterval is not None):
        Txn=GetLastRSI(Txn, FnO = True, Interval=RSIInterval)
        TradingCols = gv.TradingCols + ['RSI'+RSIInterval, 'RSIMA'+RSIInterval]
    
    if(Action in [0,1]):
        print("Buying Opportunities ...", time.strftime("%H:%M:%S", time.localtime()))
        Buy = Txn[Txn['Action'] == 1]
        Buy.sort_values(['DayPer'], ascending=[True], inplace=True)
        print(Buy.to_string(columns=TradingCols, index=False))

    if(Action in [0,-1]):
        print("Selling Opportunities ...", time.strftime("%H:%M:%S", time.localtime()))
        Sell = Txn[Txn['Action'] == -1]
        Sell.sort_values(['DayPer'], ascending=[False], inplace=True)
        print(Sell.to_string(columns=TradingCols, index=False))
    
def GetLastRSI(ToTrade, FnO = True, Interval='15m', Recs=0):

    if(not ToTrade.empty):
         ListOfStocks=' '.join(ToTrade['Stock'].tolist())
    else:
        ListOfStocks = ou.GetStockList(gv.ListOfStocks, gv.InFile) 
        if(FnO):
            FnOList=GetFnOList()
            Filtered=''
            for StockVal in FnOList['Stock']: 
                if (ListOfStocks.find(StockVal) != -1):
                    Filtered += (StockVal + ' ')
            ListOfStocks=Filtered
 
    Period = '6mo' if (Interval[-1] == 'd') else '5d'
    for Stock in gv.DiscMinStock: ListOfStocks=ListOfStocks.replace(Stock,'')

    BulkData=yf.download(ListOfStocks, period=Period,interval=Interval)

    MinCandles=BulkData['Close']
   
    if (Interval[-1] == 'm'): #bug in yfinance returns nulls in live trading in lastrows
        delta=int(Interval[:-1]); Time = dt.datetime.now() - dt.timedelta(seconds=30)
        Time = Time - (Time - dt.datetime.min) % dt.timedelta(minutes=delta) # round to nearest interval
        MinCandles.index = MinCandles.index.tz_localize(None)
        MinCandles=MinCandles[MinCandles.index <= Time]
#    MinCandles=MinCandles.tail(gv.RSIPeriod+10)
    RSI=pd.DataFrame(); RSIMA=pd.DataFrame()
    for Cols in MinCandles.columns:
        RSI[Cols]= round(talib.RSI(MinCandles[Cols],timeperiod=gv.RSIPeriod),1)
        if(RSI[Cols].isnull().values.all()):
            RSIMA[Cols]=np.NaN
        else:
            RSIMA[Cols]=round(talib.SMA(RSI[Cols], gv.RSIMAPeriod))

    RSI=RSI.tail(1); RSI=RSI.melt(); RSI.columns=['Stock','RSI'+Interval]
    RSIMA=RSIMA.tail(1); RSIMA=RSIMA.melt(); RSIMA.columns=['Stock','RSIMA'+Interval]   
    RSI = pd.merge(RSI, RSIMA, on=['Stock'], how='left')    
    RSI.sort_values(['RSI'+Interval], inplace=True)

    if(not ToTrade.empty):
        ToTrade = pd.merge(ToTrade, RSI, on=['Stock'], how='left')
        ToTrade.sort_values(['RSI'+Interval], inplace=True)
    else:
        ToTrade=RSI
        if(Recs > 0):
            ToTrade=ToTrade.head(Recs).append(ToTrade.tail(Recs))

    return(ToTrade) 
  