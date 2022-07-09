
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
from pandas_datareader import data

from nsetools import Nse
import talib
import yfinance as yf

def GetListToTrade():
#    FP=dt.datetime.now().weekday()

    ToTradeFN = gv.RptDir+gv.RepFiles['ToTrade']  
    print('Reading File :',ToTradeFN , ' (Created on) : ', 
          dt.datetime.fromtimestamp(os.path.getmtime(ToTradeFN)))
    ToTrade=pd.read_csv(ToTradeFN)
    FnOList=GetFnOList()
    ToTrade = pd.merge(ToTrade, FnOList, on=['Stock'], how='left')
    ToTrade['LSize']=round(ToTrade['LastClose']*ToTrade['Lot']/100000,1)

    ColsToDisp=gv.TechIndToDisp+['Lot']+['LSize']
    print(ToTrade.to_string(columns=ColsToDisp, index=False))
    return(ToTrade)

def GetLTPFromNSE(ToTrade):
    print(ou.LogTime(), 'Fetching Latest Price from NSE')
    nse = Nse()
    Stocks=ToTrade['Stock'].to_list()
    Stocks = [x[:-3] for x in Stocks] 
    Result={stock:nse.get_quote(stock) for stock in Stocks}
    Result = pd.DataFrame(Result).T
    Result=Result[['open','dayHigh','dayLow','lastPrice']].reset_index(); 
    Result.columns=['Stock','Open','High','Low','LTP']
    Result['Stock']=Result['Stock']+'.NS'
    ToTrade = pd.merge(ToTrade, Result, on=['Stock'], how='left')
    return(ToTrade)

def GetLTPFromYahoo(ToTrade):
    print(ou.LogTime(), 'Fetching Latest Price from Yahoo')
    LTP=data.get_quote_yahoo(ToTrade['Stock'].to_list())['price'].reset_index()
    LTP.columns=['Stock','LTP']
    ToTrade = pd.merge(ToTrade, LTP, on=['Stock'], how='left')
    return(ToTrade)

def GetLTP(ToTrade):
    ToTrade=GetLTPFromNSE(ToTrade)
#    ToTrade=GetLTPFromYahoo(ToTrade)
    return(ToTrade)

def GetAttrib(ToTrade):   
    Ck=40
    print('Fetching MCap/YHigh/YLow [* =', Ck,'] ',end='')
    Attrib=pd.DataFrame(columns=['Stock','YLow','YHigh','MCap'])
    try:
#2 bugs 1: symbol with & throws exception 2: Bulk read hangs       
#        Sl=[x for x in ToTrade['Stock'].to_list() if not '&' in x]
        Sl=[x for x in ToTrade['Stock'].to_list()]
        Sl=[Sl[i*Ck:(i+1)*Ck] for i in range(int((len(Sl)+Ck-1)/Ck))]
        for Stocks in Sl:
            print('*',end='')
            AttribChunk=data.get_quote_yahoo(Stocks)[['fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'marketCap']].reset_index()
            AttribChunk.columns=['Stock','YLow','YHigh', 'MCap']; 
            Attrib=Attrib.append(AttribChunk)
            time.sleep(1)
        print()
    except Exception as e:
        print('Error in Fetching Stock Attrib',e); 
    Attrib['MCap']=round(AttribChunk['MCap']/1000000000).astype(int, errors='ignore')
    ToTrade = pd.merge(ToTrade, Attrib, on=['Stock'], how='left')
    FnOBan=GetFnOBan(); FnOBan=FnOBan['Stock']
    ToTrade['FnOBan']=np.where(ToTrade.Stock.isin(FnOBan), 'Yes', 'No')  
    HighDiv=[i + '.NS' for i in gv.HighDiv]
    ToTrade['HDivY']=np.where(ToTrade.Stock.isin(HighDiv), 'Yes', 'No')     
    return(ToTrade)

def GetDailyData(Data, ToPrevDays=0):
    
    End=ou.ExchTime() - dt.timedelta(days=abs(ToPrevDays))
    if (ou.ExchTime().hour >= 16): End=End+dt.timedelta(days=1)
    End = End.strftime('%Y-%m-%d')
    #for matching tradingview RSI 6 months of data is good
    Start = ou.ExchTime() - dt.timedelta(days=abs(ToPrevDays)+90)
    Start = Start.strftime('%Y-%m-%d')    
    
    ListOfStocks=' '.join(Data['Stock'].tolist())
    print(ou.LogTime(),'Fetching Daily Candles [', Start, ' to ', End,')' )
    BulkData=yf.download(ListOfStocks, start=Start, end = End)
    BulkData=BulkData[BulkData.index < End] # to remove bug where last row is always added
    return(BulkData)

def ProcessDaysData(TableColumns=False):
    print(ou.LogTime(), '===== Day Processing ',end='')
    FileName = gv.RptDir+gv.RepFiles['DaysInfo']+ou.ExchTime().strftime('%y%m%d')+'.csv'

    if(os.path.isfile(FileName)):
        print('/Already processed, Loading from file/')
        DaysData = pd.read_csv(FileName, index_col=0, skipinitialspace=True)
    else:
        DaysData=PreDayProcess()          
        DaysData=AddDaysInfo(DaysData)
        DaysData.to_csv(FileName)  
 
    DayAnalysis(DaysData)
    DaysData[gv.ConvToInt] = DaysData[gv.ConvToInt].astype('Int64', errors='ignore')
    if(TableColumns):
        DaysData=DaysData[gv.DTab]; DaysData.columns = gv.DTabDisp
        DaysData.sort_values(['Close%'], ascending=[False], inplace=True)
        print(DaysData[(DaysData['Stock'] == '^NSEI')].to_string(index=False))
    return(DaysData)

def PreDayProcess():
    Data=GetFnOList()
#    Data=Data.head()
    Data=AddCustomStocks(Data)
    Data=GetAttrib(Data)
    return(Data)
def AddCustomStocks(Data):
    Data=Data.append(pd.DataFrame({'Stock' : ['^NSEI']}), ignore_index = True)
    return(Data)
def GetGainersMat():
    
    FileName = gv.RptDir+'PerMat.csv'
    Data=GetFnOList()
    Data=AddCustomStocks(Data); BulkData=GetDailyData(Data)
    Data=BulkData['Close'].copy()
    for Cols in Data.columns:
        Data['PrevDay']=Data[Cols].shift(1)
        Data[Cols+'_C%']=round((Data[Cols]-Data['PrevDay'])*100/Data['PrevDay'],1)
    Cols = [s for s in Data.columns if("_C%" in s)]
    Data=Data[Cols];Data.columns=[x[:-6] for x in Cols]
    Data.index = Data.index.date; Data=Data.iloc[::-1]; Data=Data.transpose()
    Data.to_csv(FileName)
    return(Data)
    
def DayAnalysis(Data):
    print(ou.LogTime(), '===== Analysis ')  
    List=Data.query("FnOBan=='Yes'")['Stock'].to_list()
    if(len(List) != 0 ) : print('FnO Ban List :', List)      
    List=Data.query("(DHigh1P >= 10 and (DClose1P <= 10))")['Stock'].to_list()
    if(len(List) != 0 ) : print('Day High Circuit Only :', List)      
    List=Data.query("(DLow1P <= -10 and (DClose1P > -10))")['Stock'].to_list()
    if(len(List) != 0 ) : print('Day Low Circuit Only :', List)    
    return()

def AddDaysInfo(Data, ToPrevDays = 0):
    
    BulkData=GetDailyData(Data,ToPrevDays)
    LRows=[1,2,3]; Cols=['Close', 'Low', 'High']
    Data=ExtractData(Data, BulkData, LRows, Cols, 'D')

    Data['Close']=Data['DClose1']
    Data['Lot']=round(Data['Lot'])
    Data['LSize']=round(Data['Close']*Data['Lot']/100000,1)
    Data['YLHP']=round((Data['Close']-Data['YLow'])*100/(Data['YHigh']-Data['YLow']))

    Data=AddRSI(Data, BulkData)
    Data=AddLinReg(Data, BulkData,Period=5); Data=AddLinReg(Data, BulkData,Period=10)
    Data=AddPerCols(Data, 'D')
    return(Data) 

def AddLTPToDays(Data):
    Data=GetLTP(Data)
    Data = CalcPer(Data, ['DayP'], ['LTP'], ['Close'])  
    if('Open' in Data.columns):
        Cols={'Open':'DayOP','High':'DayHP','Low':'DayLP'}
        for key in Cols:
            Data = CalcPer(Data, [Cols[key]], [key], ['Close'])  
    return(Data)
   
def AddRSI(Data, BulkData, Interval=''):
    DataCandles=BulkData['Close'].copy()
    print('Data retreived range : ', DataCandles.index[0], DataCandles.index[-1])
    RSI=pd.DataFrame(); RSIMA=pd.DataFrame()
    for Cols in DataCandles.columns:
        RSI[Cols]= round(talib.RSI(DataCandles[Cols],timeperiod=gv.RSIPeriod))
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

def AddLinReg(Data, BulkData, Period):
    DataCandles=BulkData.tail(Period).copy()
    DataHC=DataCandles['High'];DataLC=DataCandles['Low']
    LinReg=pd.DataFrame(); StdDev=pd.DataFrame()
    for Cols in DataHC.columns:
        LinReg[Cols]= abs(round(talib.LINEARREG_SLOPE(DataHC[Cols],timeperiod=Period),2))
        Points = DataHC[Cols].tolist()+DataLC[Cols].tolist()
        StdDev[Cols]=[round(np.std(Points)*100/np.mean(Points),2)]

    LinReg=LinReg.tail(1); LinReg=LinReg.melt(); LinReg.columns=['Stock','LRm'+str(Period)] 
    StdDev=StdDev.tail(1); StdDev=StdDev.melt(); StdDev.columns=['Stock','SDP'+str(Period)] 
    LinReg = pd.merge(LinReg, StdDev, on=['Stock'], how='left')    
    Data = pd.merge(Data, LinReg, on=['Stock'], how='left')
    return(Data)

def GetFnOList():
    nse = Nse()
    FnO=pd.DataFrame(list(nse.get_fno_lot_sizes().items()), columns=['Stock', 'Lot'])
    FnO=FnO[~FnO.Stock.str.contains("NIFTY")]
    FnO['Stock']=FnO['Stock']+'.NS'
    return(FnO)
    
def GetFnOBan():
    FnOBanFile = 'https://www1.nseindia.com/content/fo/fo_secban.csv'
    FnOBan = pd.read_csv(FnOBanFile,names=['RowNo','Stock'], skiprows=1)
    if(len(FnOBan.index)>0):
        FnOBan['Stock']=FnOBan['Stock']+'.NS'
    return(FnOBan)
    
def TopCurrGnL(Data):
     print(ou.LogTime(), 'Current Gainers and Loosers')
     Txn = GetLTP(Data)
     Txn['CurrP']=round((Txn['LTP'] - Txn['Close'])*100/Txn['Close'],2)
     Txn.sort_values(['CurrP'], ascending=[False], inplace=True)
     return(Txn)
 
def AddIntraMin(Data, Interval='15m'):

    print(ou.LogTime(),'Fetching IntraDay Data')    
    ListOfStocks=' '.join(Data['Stock'].tolist())
    MinCandles=yf.download(ListOfStocks, period='5d',interval=Interval)
   
#bug in yfinance returns nulls in live trading in lastrows
    delta=int(Interval[:-1]); Time = ou.ExchTime() - dt.timedelta(seconds=30)
    Time = Time - (Time - dt.datetime.min) % dt.timedelta(minutes=delta) # round to nearest interval
    MinCandles.index = MinCandles.index.tz_localize(None)
    MinCandles=MinCandles[MinCandles.index <= Time]
    
    Cols=['Low', 'High'] ; LRows=[1,2,4,8] # last 15m, 30m, 1h, 2h
    Data=ExtractData(Data, MinCandles, LRows, Cols, 'M')

    Data=AddRSI(Data, MinCandles, '15m')
    return(Data) 

def AddIntraDay(Data, Interval='15m'):
    Data = AddIntraMin(Data, Interval='15m')
    Data=GetLTP(Data)
    Data=AddPerCols(Data, 'I') 
    print(ou.LogTime(),'Intra Day Processing Completed')    
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
        delta=int(Interval[:-1]); Time = ou.ExchTime() - dt.timedelta(seconds=30)
        Time = Time - (Time - dt.datetime.min) % dt.timedelta(minutes=delta) # round to nearest interval
        MinCandles.index = MinCandles.index.tz_localize(None)
        MinCandles=MinCandles[MinCandles.index <= Time]
#    MinCandles=MinCandles.tail(gv.RSIPeriod+10)
    RSI=pd.DataFrame(); RSIMA=pd.DataFrame()
    for Cols in MinCandles.columns:
        RSI[Cols]= round(talib.RSI(MinCandles[Cols],timeperiod=gv.RSIPeriod))
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

def DisplayData(InData, For = 'Intra', Dir='Short', Recs=6):
    
    DispCol = ['Stock', 'MCap','Lot', 'LSize', 'Close', 'DClose2P', 'D1Close2P','RSI']
    Data = InData.copy()
    SOrd = False if Dir == 'Short' else True

    if(For == 'Day'):
        if(Dir == 'Short'):
#            RankCols=['DClose1P','DHigh1P','D1Close2P','DClose2P', 'DHigh2P']            
#            RankCols=['DClose1P','DHigh1P','D1Close2P','DClose2P']
            RankCols=['DClose1P','DHigh1P']
        else:
#            RankCols=['DClose1P','DLow1P','D1Close2P','DClose2P','DLow2P']
#            RankCols=['DClose1P','DLow1P','D1Close2P','DClose2P']
            RankCols=['DClose1P','DLow1P']
        Data=AddRanking(Data, RankCols, SOrd)    
    
    Data = ApplyFilter(Data, For , Dir)
    print(Dir ,' .. Opportunities')

    if(For == 'Intra'): 
        if(Dir == 'Short'):
            DispCol += ['RSIMA15m','RSI15m', 'DayP','MHigh1P','MHigh2P'] 
        else:
            DispCol += ['RSIMA15m','RSI15m', 'DayP','MLow1P','MLow2P']
        SortCol=DispCol[5:] 
          
    if(For == 'Day'):
        if('LTP' in Data.columns):
            ColsList = DispCol+RankCols+['DayP']
            DisplayResult(Data,'DayP', ColsList, SOrd, Recs)
            RankingCol = [x + 'R' for x in RankCols]
            ColsList = DispCol+RankingCol+['DayP']
            DisplayResult(Data,'DayP', ColsList, SOrd, Recs)            
        DispCol += RankCols
        SortCol=DispCol[7:]   
    
    for Col in SortCol: DisplayResult(Data, Col, DispCol, SOrd, Recs)

    return()

def ApplyFilter(Data, For, Dir):

    FnOBan=GetFnOBan()
    Cond = Data['Stock'].isin(FnOBan['Stock']); 
    Data.drop(Data[Cond].index, inplace = True)
    
    if('LTP' in Data.columns):
        print('Applying Day RSI Filter')
        Cond = "Data['RSI'] >= 40" if Dir == 'Short' else "Data['RSI'] <= 60"
        print('Filter: ',Cond , 'Rows ', Data.shape[0],'->', end=" ")
        Data=Data[eval(Cond)]; print(Data.shape[0])  
 
    if(For == 'Intra'): 
         Cond = "Data['RSIMA15m'] >= 60" if Dir == 'Short' else "Data['RSIMA15m'] <= 40"
         print('Filter: ',Cond , 'Rows ', Data.shape[0],'->', end=" ")
         Data=Data[eval(Cond)]; print(Data.shape[0])       
    return(Data)
    
def AddPerCols(Data, For):

    if(For == 'I'):
        # This needs to be revist
        Col1 = ['LTP']*4
        Col2 =['MHigh1', 'MHigh2','MLow1', 'MLow2']
        ColsName=[Col + 'P' for Col in Col2]
        Data = CalcPer(Data, ColsName, Col1, Col2)
        # ends
        
        Col1 = ['LTP']; Col2 = ['Close']; ColsName = ['DayP']
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

def DisplayResult(Data, Col, DisplayCols, SOrder, NoOfRecs):
    ColsToDisp=DisplayCols.copy()
    Data.sort_values([Col], ascending=SOrder, inplace=True)
    ColsToDisp.remove(Col); ColsToDisp += [Col]     
    print(Data.head(NoOfRecs).to_string(columns=ColsToDisp, index=False))
    return()

def AddRanking(Data, RankCols, SOrder):
    for Col in RankCols:
        Data.sort_values([Col], ascending=SOrder, inplace=True)
        Data = Data.reset_index(drop=True)
        Data[Col+'R']=(Data.index+1)
    return(Data)
    
def CalcPer(Data, ColsName, Col1, Col2 ):
    for i in range(len(ColsName)):
        Data[ColsName[i]]=(Data[Col1[i]]-Data[Col2[i]])*100/Data[Col2[i]]
        Data[ColsName[i]]=Data[ColsName[i]].apply(pd.to_numeric)
        Data[ColsName[i]]=round(Data[ColsName[i]],1)
    return(Data)


