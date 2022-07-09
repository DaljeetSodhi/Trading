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
import StockUtils as su
#from yahoo_fin import stock_info as si
from nsetools import Nse
import talib
import yfinance as yf
from yahoofinancials import YahooFinancials

def GetListToTrade():
    FP=dt.datetime.now().weekday()

    ToTradeFN = gv.RptDir+str(FP)+gv.RepFiles['ToTrade']  
    print('Reading File :',ToTradeFN , ' (Created on) : ', 
          dt.datetime.fromtimestamp(os.path.getmtime(ToTradeFN)))
    ToTrade=pd.read_csv(ToTradeFN)
    FnOList=ou.GetFnOList()
    ToTrade = pd.merge(ToTrade, FnOList, on=['Stock'], how='left')
    ToTrade['Lot']=round(ToTrade['LastClose']*ToTrade['Lot']/100000,1)

    ColsToDisp=gv.TechIndToDisp+['Lot']
    print(ToTrade.to_string(columns=ColsToDisp, index=False))
    return(ToTrade)

def GetLTPFromNSE(ToTrade):
    nse = Nse()
    Stocks=ToTrade['Stock'].to_list()
    Stocks = [x[:-3] for x in Stocks]   
    Stocks = {stock:nse.get_quote(stock)['lastPrice'] for stock in Stocks}
    Stocks = {key+'.NS': val for key, val in Stocks.items()} 
    ToTrade['LTP'] = ToTrade['Stock'].map(Stocks)
    return(ToTrade)

def GetLTPFromYahoo(ToTrade):
    Stocks=ToTrade['Stock'].to_list()
    YF = YahooFinancials(Stocks);  StocksPrice = YF.get_current_price()
    ToTrade['LTP'] = ToTrade['Stock'].map(StocksPrice)
    return(ToTrade)

def GetLTP(ToTrade):
    print(LogTime() , 'Fetching Current Prices')
    return(GetLTPFromNSE(ToTrade))
#    return(GetLTPFromYahoo(ToTrade))

def AddDaysInfo(Data):
    print(LogTime(), 'Fetching Previous Days Data ')
    ListOfStocks=' '.join(Data['Stock'].tolist())
    BulkData=yf.download(ListOfStocks, period='6mo')
    if (dt.datetime.now().time().hour < 16): 
        Today=dt.datetime.now().strftime('%Y-%m-%d')
        BulkData=BulkData[BulkData.index < Today]
    
    LRows=[1,2,3]; Cols=['Close', 'Low', 'High']
    Data=ExtractData(Data, BulkData, LRows, Cols, 'D')

    Data['Close']=Data['DClose1']
    Data['Lot']=round(Data['Close']*Data['Lot']/100000,1)

    MinCandles=BulkData['Close']
    RSI=pd.DataFrame(); 
    for Cols in MinCandles.columns:
        RSI[Cols]= round(talib.RSI(MinCandles[Cols],timeperiod=gv.RSIPeriod),1)
    RSI=RSI.tail(1); RSI=RSI.melt(); RSI.columns = ['Stock','RSI']
    Data = pd.merge(Data, RSI, on=['Stock'], how='left')
    Data = Data.dropna(axis=0, subset=['RSI']) 
    Data.sort_values(['RSI'], inplace=True)
 
    Data=AddPerCols(Data, 'D')
    print(LogTime(), 'Day Processing Completed')    

    return(Data) 

def TopCurrGnL(Data):
     print(LogTime(), 'Current Gainers and Loosers')
     Txn = GetLTP(Data)
     Txn['CurrP']=round((Txn['LTP'] - Txn['Close'])*100/Txn['Close'],2)
     Txn.sort_values(['CurrP'], ascending=[False], inplace=True)
     return(Txn)
 
def AddIntraMin(Data, Interval='15m'):

    print(LogTime(),'Fetching IntraDay Data')    
    ListOfStocks=' '.join(Data['Stock'].tolist())
    MinCandles=yf.download(ListOfStocks, period='5d',interval=Interval)
   
#bug in yfinance returns nulls in live trading in lastrows
    delta=int(Interval[:-1]); Time = dt.datetime.now() - dt.timedelta(seconds=30)
    Time = Time - (Time - dt.datetime.min) % dt.timedelta(minutes=delta) # round to nearest interval
    MinCandles.index = MinCandles.index.tz_localize(None)
    MinCandles=MinCandles[MinCandles.index <= Time]
#    print('Shape of Data : ', MinCandles.shape)
    
    Cols=['Low', 'High'] ; LRows=[1,2,4,8] # last 15m, 30m, 1h, 2h
    Data=ExtractData(Data, MinCandles, LRows, Cols, 'M')

    MinCandles=MinCandles['Close']
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

def AddIntraDay(Data, Interval='15m'):
    Data = AddIntraMin(Data, Interval='15m')
    Data=GetLTP(Data)
    Data=AddPerCols(Data, 'I') 
    print(LogTime(),'Intra Day Processing Completed')    
    return(Data)

def AddLatestToList(ToTrade, Action = 0, RSIInterval=None):

    Txn=GetLTP(ToTrade)
    Txn['DayP']=round((Txn['LTP'] - Txn['LastClose']) * 100 / Txn['LastClose'],2)
    Txn['PDayP']=round((Txn['LastClose'] - Txn['Last2Close']) * 100 / Txn['Last2Close'],2)
    Txn['PDay2P']=round((Txn['LastClose'] - Txn['Last3Close']) * 100 / Txn['Last3Close'],2)

    Txn['Date'] = pd.to_datetime(Txn["Date"]).dt.strftime('%m-%d')
    
    TradingCols = gv.TradingCols
    if (RSIInterval is not None):
        Txn=GetLastRSI(Txn, FnO = True, Interval=RSIInterval)
        TradingCols = gv.TradingCols + ['RSI'+RSIInterval, 'RSIMA'+RSIInterval]
    
    if(Action in [0,1]):
        print("Buying Opportunities ...", time.strftime("%H:%M:%S", time.localtime()))
        Buy = Txn[Txn['Action'] == 1]
        Buy.sort_values(['DayP'], ascending=[True], inplace=True)
        print(Buy.to_string(columns=TradingCols, index=False))

    if(Action in [0,-1]):
        print("Selling Opportunities ...", time.strftime("%H:%M:%S", time.localtime()))
        Sell = Txn[Txn['Action'] == -1]
        Sell.sort_values(['DayP'], ascending=[False], inplace=True)
        print(Sell.to_string(columns=TradingCols, index=False))
    
def GetLastRSI(ToTrade, FnO = True, Interval='15m', Recs=0):

    if(not ToTrade.empty):
         ListOfStocks=' '.join(ToTrade['Stock'].tolist())
    else:
        ListOfStocks = ou.GetStockList(gv.ListOfStocks, gv.InFile) 
        if(FnO):
            FnOList=ou.GetFnOList()
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

def DisplayData(InData, For = 'Intra', Dir='Short', Recs=5):
    
    Data = InData.copy()
    SOrd = False if Dir == 'Short' else True
    Cond = "Data['RSI'] >= 40" if Dir == 'Short' else "Data['RSI'] <= 60"
    print('Filter: ',Cond , 'Rows ', Data.shape[0],'->', end=" ")
    Data=Data[eval(Cond)]; print(Data.shape[0])       
    print(Dir ,' .. Opportunities')
    if(For == 'Intra'): 
        BasedCol = 'MLow' if Dir == 'Short' else 'MHigh'    
        DispCol=['Stock', 'Lot', 'RSI', 'DClose1P','RSI15m', 'RSIMA15m']
        DispCol += [BasedCol+'2P',BasedCol+'1P','TodayP']

        for Col in ['RSIMA15m', 'TodayP']: DisplayResult(Data, Col, DispCol, SOrd, Recs)
        for i in [1,2]: DisplayResult(Data, BasedCol+str(i)+'P', DispCol, SOrd, Recs)
                 
    if(For == 'Day'):
        BasedCol = 'DHigh' if Dir == 'Short' else 'DLow'    
        DispCol=['Stock', 'Lot', 'RSI', 'D1Close2P', 'DClose1P', 'DClose2P']
        DispCol += [BasedCol+'1P', BasedCol+'2P']    

        for Col in ['RSI','D1Close2P']: DisplayResult(Data, Col, DispCol, SOrd, Recs)
        print("")
        for Col in [BasedCol, 'DClose']: 
            for i in [1,2]: DisplayResult(Data, Col+str(i)+'P', DispCol, SOrd, Recs)
            
    return()
    
def AddPerCols(Data, For):

    if(For == 'I'):
        Col1 = ['LTP']*4
        Col2 =['MHigh1', 'MHigh2','MLow1', 'MLow2']
        ColsName=[Col + 'P' for Col in Col2]
        Data = CalcPer(Data, ColsName, Col1, Col2)
        
        Col1 = ['LTP']; Col2 = ['Close']; ColsName = ['TodayP']
        Data = CalcPer(Data, ColsName, Col1, Col2)   
    
    if(For == 'D'):
        Col1 =['DHigh1', 'DHigh2','DLow1', 'DLow2', 'DClose1', 'DClose2' ]
        Col2 = ['DClose2', 'DClose3']*3 
        ColsName=[Col + 'P' for Col in Col1]
        Data = CalcPer(Data, ColsName, Col1, Col2)
        Data = CalcPer(Data, ['D1Close2P'], ['DClose1'], ['DClose3'])
    
    return(Data)
    
def ExtractData(ToData, FromData, LRows, Cols, ColPrefix):
    
    for Col in Cols:
        DayCandles=FromData[Col]       
        for Row in LRows:
            ColName=ColPrefix+Col+str(Row)
            Prev=DayCandles.iloc[[-Row]].melt(); Prev.columns=['Stock',ColName]
            ToData = pd.merge(ToData, Prev, on=['Stock'], how='left')
            ToData[ColName]=round(ToData[ColName],2)
    return(ToData)

def DisplayResult(Data, Col, ColsToDisp, SortOrder, NoOfRecs):
#    Col=BasedCol+str(i)+'P'; #ColsToDisp = BaseCols + [Col]
    Data.sort_values([Col], ascending=SortOrder, inplace=True)
    ColsToDisp.remove(Col); ColsToDisp += [Col]       
    print(Data.head(NoOfRecs).to_string(columns=ColsToDisp, index=False))
    return()

def CalcPer(Data, ColsName, Col1, Col2 ):
    for i in range(len(ColsName)):
        Data[ColsName[i]]=round((Data[Col1[i]]-Data[Col2[i]])*100/Data[Col1[i]],1)
    return(Data)

def LogTime():
    return(dt.datetime.now().strftime('%d %H:%M:%S'))

