import pandas as pd
import yfinance as yf
from yahoo_fin import stock_info as si
import talib
import datetime as dt
from scipy.signal import argrelextrema
from scipy.stats import variation
import numpy as np

import OtherUtils as ou
import GlobalVars as gv

def FindStocks(Stocks):
    if(Stocks == ""): return(pd.DataFrame(), '')
    BulkData = GetBulkData(Stocks, gv.FromDate)  
    for i, Stock in enumerate(Stocks.split()):
        print('\rFinding Stock Pattern for ', i+1, Stock, 
              '->           ', end='')
        StockData = GetStockData(Stock, BulkData)
        if(not StockData.empty):                     
            PatResult = GetStockPatterns(Stock, StockData, False)
            ou.SaveResult(PatResult, 'PatData')
    PatResult=ou.GetDataFromKey('PatData')
    Stocks=StocksToTrade('PatData')
    return(PatResult, Stocks)

def ProcData(PatResult, Stock):
    if('History' in gv.Action):
        StockData=PatResult[PatResult['Stock'] == Stock].copy()
        StockData = GetStockPatterns(Stock, StockData, True)
    else:
        StockData=ou.ReadHistData(Stock)
    if(not StockData.empty): 
        if('Attrib' in gv.Action):
            CalcStockAttrib(StockData)
    return(StockData)

def GetStockData(Stock, BulkData):  
    Txn=pd.DataFrame(columns=gv.StockCols)
    if(isinstance(BulkData['Close'], pd.DataFrame)): 
         for Column in gv.StockCols: Txn[Column]=BulkData[Column][Stock]
    else:
        Txn=BulkData[gv.StockCols].copy()    
    Txn = Txn.dropna(subset=['Close'])
#    if(gv.AddLTP):
#       Today=dt.date.today()
#       Today=pd.to_datetime((pd.datetime.now()).date(), format='%Y-%m-%d')
#       if(ou.IsMarketOpen(Today)):
#           Txn.loc[Today] = round(si.get_live_price(Stock),2)
    Txn = Txn.reset_index();Txn['Index']=Stock + "_" +Txn['Date'].dt.date.astype(str)
    Txn.set_index('Index', inplace=True)
    Txn = Txn.dropna(axis=0, subset=['Close'])     
    Txn['Stock']=Stock    
    if('ReadRaw' in gv.History):
        HistData=ou.ReadHistData(Stock)
        if(not HistData.empty): 
            StartDate=HistData.Date.iloc[-1]; 
            Txn=HistData[['Date','Close','Stock']].append(Txn[Txn['Date'] > StartDate])
    if(len(Txn) < gv.DaysForTech):
        print('!!! Not enough Data for !!! :', end='\n')
        return(pd.DataFrame())
    
    Txn['TradeDate']=Txn['Date'].shift(-1); Txn['TradePrice']=Txn['Close'].shift(-2)
    Txn.at[Txn.index[-1], 'TradeDate']=Txn.at[Txn.index[-2], 'TradeDate']=Txn['Date'].iloc[-1]
    Txn.at[Txn.index[-1], 'TradePrice']=Txn.at[Txn.index[-2], 'TradePrice']=Txn['Close'].iloc[-1]  
    return(Txn)

def GetStockPatterns(Stock, StockData, RunDayToDay):
    if(RunDayToDay):
        DayToDayPat=pd.DataFrame(columns=gv.RSIDivCols); StartFrom=0
        if('ReadProc' in gv.History):
            HistData=ou.ReadHistData(Stock)
            StartFrom=gv.DaysForTech; 
            TotalRecs=len(StockData)
            if(not HistData.empty): 
                LastTxnDate=HistData['Date'].iloc[-1]
                StockData=HistData.append(StockData[StockData['Date'] > LastTxnDate])
                StartFrom=len(HistData); 
                DayToDayPat=HistData[HistData['RSIDiv'].isin(['RD','HD','RF','HF'])][gv.RSIDivCols]
        TotalRecs=len(StockData)
        for RecNo in range(StartFrom, TotalRecs+1):
            IncBulkData = StockData[:RecNo]
            StockDataInd = AddIndicators(IncBulkData, True)
            PatResult = SearchPattern(StockDataInd)
            IncPattern = PatResult[gv.RSIDivCols].copy()
            IncPattern = IncPattern[IncPattern['RSIDiv'].isin(gv.RSIDiverg)]
            DayToDayPat = pd.concat([DayToDayPat, IncPattern]).drop_duplicates()

        OverAllPat= PatResult[PatResult['RSIDiv'].isin(gv.RSIDiverg)]
        FailedDiv=DayToDayPat[~DayToDayPat.Date.isin(OverAllPat.Date)] 
        FailedDiv=FailedDiv.sort_values(['Date', 'RSIDiv'], ascending=[True, True])
        FailedDiv = FailedDiv[~FailedDiv.index.duplicated()] #Can have RD,HD both
        PatResult['FailedDiv']=np.NaN
        PatResult.loc[PatResult.index.isin(FailedDiv.index), ['RSIDiv']] = FailedDiv['RSIDiv']
        PatResult.loc[PatResult.index.isin(FailedDiv.index), ['FailedDiv']] = 'FD'
        PatResult['RSIDiv'] = np.where(PatResult['FailedDiv'] == 'FD', 
                                 PatResult['RSIDiv'].str[:1]+'F', PatResult['RSIDiv'])
        PatResult.loc[PatResult.index.isin(FailedDiv.index), 
            ['PrevRSIDiv', 'DivDays', 'Action']] = FailedDiv[['PrevRSIDiv', 'DivDays', 'Action']]
        for Col in gv.RSIDivCols: PatResult[Col]=PatResult[Col].replace('', np.nan)
        PatResult=AddIndicators(PatResult, False)       
        if('WriteProc' in gv.History): ou.CreateHistData(Stock, PatResult)  
    else:
        StockDataInd = AddIndicators(StockData, False)
        PatResult = SearchPattern(StockDataInd)
    return(PatResult)
 
def CreateStockOrders(PatResult, Stock):
    PatResult = PatResult[PatResult['Stock'] == Stock ]  
    Orders = GenOrders(PatResult) 
    return(Orders)

def GetBulkData(ListOfStocks, FromDate):
#    LastDate = ou.GetLastDay(ToDate) # To fix the bug in yfinance
    print(gv.StartTime.strftime('%H:%M:%S'),'Getting Data :',FromDate,':')
    print(ListOfStocks)
    BulkData=yf.download(ListOfStocks, FromDate)
    return(BulkData)

def AddIndicators(Txn, DayToDayCalc=False): 
    np.warnings.filterwarnings('ignore')  # Below code is throwing warnings 
    Txn['RSI'] =  round(talib.RSI(Txn['Close'],timeperiod=gv.RSIPeriod),1) 
    if(gv.Patterns['RSIDiverg']): Txn=CalcLMinMax(Txn, ['RSI', 'Close'], False)
    if(not DayToDayCalc):
        if(gv.Patterns['RSICDBO']): Txn=CalcLMinMax(Txn, ['RSI', 'Close'], True)
    #    Txn['PDayRSI']=Txn['RSI'].shift(1)
    #    Txn['RSIMA'] =  round(talib.SMA(Txn['RSI'],timeperiod=gv.RSIMAPeriod)) 
        if(gv.Patterns['MA']): Txn=CalcMA(Txn, 'Close', gv.MAPeriods, gv.IsSMA) 
        if(gv.Patterns['RSIMAMinMax']): Txn=CalcMA(Txn, 'RSI', gv.RSIMAPeriods)
        if(gv.Patterns['RSIMA']): Txn=CalcMA(Txn, 'RSI', gv.RSIMAPeriods, gv.IsSMA )
           
    return(Txn)  
    
def SearchPattern(StockDataInd):
    Txn=StockDataInd.copy()
    for CurrPat in gv.Patterns:
        if(gv.Patterns[CurrPat]): 
            Txn=globals()['Find'+CurrPat](Txn)
#                AllPat=AllPat.append(Txn, sort=False)
    return(Txn)

def SearchBestStocks(PatInFile):
    for CurrPat in gv.Patterns:
        if(gv.Patterns[CurrPat]): BestStocks=globals()['Best'+CurrPat](PatInFile)
    return(BestStocks)

def BestRSIMAMinMax(FileKey):
#    Txn = pd.read_csv(PatInFile, index_col=0, error_bad_lines = False)
    Txn=ou.GetDataFromKey(FileKey)

    StocksMin=Txn.sort_values(['RSIMAMin', 'Date'], ascending=[True, False])
    StocksMax=Txn.sort_values(['RSIMAMax', 'Date'], ascending=[False, False]);    
    Stocks = pd.concat([StocksMin.head(gv.BestStocks), StocksMax.head(gv.BestStocks)])
    return(Stocks)
    
def BestRSICDBO(FileKey):
#    Txn = pd.read_csv(PatInFile, index_col=0, error_bad_lines = False)
    Txn=ou.GetDataFromKey(FileKey)

    StocksBuy=Txn.sort_values(['Action', 'Date'], ascending=[False, False])
    StocksSell=Txn.sort_values(['Action', 'Date'], ascending=[True, False]);    
    Stocks = pd.concat([StocksBuy.head(gv.BestStocks), StocksSell.head(gv.BestStocks)])
    return(Stocks)
def FindRSIMA(Txn):
    return(Txn)
    
def FindRSIMAMinMax(Txn): # CalcRSIMA 
    Pat=Txn.copy()
    IndCols = [col for col in Pat.columns if '_MA' in col]; IndCols.append('RSI')  
    Pat=Pat.tail(len(IndCols)); 
    Pat['RSIMAMin'] = Pat[IndCols].min(axis=1)
    Pat['RSIMAMax'] = Pat[IndCols].max(axis=1)    
    PatMin=Pat.sort_values(['RSIMAMin', 'Date'], ascending=[True, True])
    PatMax=Pat.sort_values(['RSIMAMax', 'Date'], ascending=[False, True]);
    
    Pat = pd.concat([PatMin.head(1), PatMax.head(1)])
    return(Pat)   
    
def FindPerLevelBS(Txn): 
    Txn=CalcOBOSMinMax(Txn)
    Txn['OrderType'] = np.where(Txn['OSMax'] > 0, 'HP', Txn['OrderType'])
    Txn['OrderType'] = np.where(Txn['OBMin'] > 0, 'LP', Txn['OrderType'])
    Txn['OSMax'].fillna(method='ffill', inplace=True)
    Txn['OBMin'].fillna(method='ffill', inplace=True)
    Txn['PerFMinMax']=np.NaN
    Txn['PerFMinMax']=np.where((Txn['Action'] == 1)|(Txn['OrderType'] == 'LP'), 
        (Txn['OSMax'] - Txn['Close']) * 100 / Txn['OSMax'], Txn['PerFMinMax'])
    Txn['PerFMinMax']=np.where((Txn['Action'] == -1)|(Txn['OrderType'] == 'HP'), 
        (Txn['Close'] - Txn['OBMin']) * 100 / Txn['OBMin'], Txn['PerFMinMax'])   
    Txn['PerFMinMax']=round(Txn['PerFMinMax'], 1)
    return(Txn)
def CalcOBOSMinMax(Txn): 
    LastSOSDate=LastSOBDate=Txn['Date'].iloc[0]
    Txn['OSMax']=Txn['OBMin']=np.NaN
    for i, Row in Txn.iterrows():
        CurrTrend = FindTrend(Row['RSI'])
        if(CurrTrend == 'OS'): 
            if(pd.isnull(LastSOSDate)): LastSOSDate=Row['Date'] 
            if(not pd.isnull(LastSOBDate)):
                df=Txn[(Txn['Date'] >= LastSOBDate) & (Txn['Date'] <= Row['Date'])]
                PriceIdx = df['Close'].idxmin(); LastSOBDate=np.NaN
                if(PriceIdx) : Txn.at[PriceIdx, 'OBMin']=Txn.loc[PriceIdx,'Close']               
        if(CurrTrend == 'OB'): 
            if(pd.isnull(LastSOBDate)): LastSOBDate=Row['Date']
            if(not pd.isnull(LastSOSDate)):
                df=Txn[(Txn['Date'] >= LastSOSDate) & (Txn['Date'] <= Row['Date'])]
                PriceIdx = df['Close'].idxmax(); LastSOSDate=np.NaN
                if(PriceIdx) : Txn.at[PriceIdx, 'OSMax']=Txn.loc[PriceIdx,'Close']
    return(Txn)   
    
def CalcMA(Txn, ColName, MovAvg, IsSMA=True):
    for ma in MovAvg:
        if(IsSMA): Txn[ColName+'_MAs'+str(ma)]=round(talib.SMA(Txn[ColName], ma))
        else: Txn[ColName+'_MAe'+str(ma)]=round(talib.EMA(Txn[ColName], ma))
    return(Txn)

def FindMA(Txn):
    return(Txn)
    
def FindSellAtLMP(Txn):
#    LastPrice=Txn.tail(1) 
    Txn.at[Txn.index[-1], 'Action'] = -1
    Txn.at[Txn.index[-1], 'OrderType'] = 'MP'                  
    return(Txn)  
    
def BestSellAtLMP(PatInFile):
    return(pd.DataFrame())
def FindRSICDBO(Alltxn):
#    Txn = pd.read_csv(DataFile, index_col=0, error_bad_lines = False)
    Txn=Alltxn.copy()
    Txn['OrderType'] = Txn['Action']=Txn['ActionRun']=np.NaN
    Txn['OrderType'] = Txn['OrderType'].astype(str)

#if how =any only those txn where RSI and Cloase matches
    LMax=Txn.dropna(subset=['RSILMax','CloseLMax'], how='all')  
    LMin=Txn.dropna(subset=['RSILMin', 'CloseLMin'], how='all')  
    PrevTrend=np.NaN
    for i, (idx, Row) in zip(np.arange(len(LMax.index)), LMax.iterrows()):
        CurrTrend=FindTrend(Row['RSI'])
        if(i>0): PrevTrend = FindTrend(LMax['RSI'].iloc[i-1])
        if(CurrTrend == 'OS' or PrevTrend == 'OS'):
            if(Row['Close'] > LMax['Close'].iloc[i-1]):
                Txn.at[idx, 'Action']=-1 
                if(Row['RSI'] < LMax['RSI'].iloc[i-1]):
                    Txn.at[idx, 'OrderType']='SD' 
                else:
                    Txn.at[idx, 'OrderType']='SC'

    for i, (idx, Row) in zip(np.arange(len(LMin.index)), LMin.iterrows()):
        CurrTrend=FindTrend(Row['RSI']); 
        if(i>0): PrevTrend = FindTrend(LMin['RSI'].iloc[i-1])
        if(CurrTrend == 'OB' or PrevTrend == 'OB'):
            if(Row['Close'] < LMin['Close'].iloc[i-1]):
                Txn.at[idx, 'Action']=1
                if(Row['RSI'] > LMin['RSI'].iloc[i-1]):
                    Txn.at[idx, 'OrderType']='SD' 
                else:
                    Txn.at[idx, 'OrderType']='SC'

#    Txn.dropna(subset=['Action'], inplace = True )  
    if((CalcCV(Txn) > 0.25) and (gv.RangeBound)) :
        Txn['ActionRun'] = (Txn.groupby(Txn['Action'].ne(Txn['Action'].shift()).cumsum()).cumcount().add(1))              
        Txn['Action'] = np.where((Txn['ActionRun'] >= gv.BOutLimit), Txn['Action']*(-1), Txn['Action'])
    return(Txn)  

def FindRSIDiverg(Alltxn):
    Txn=Alltxn.copy()
    
    Txn['RSIDiv']=Txn['PrevRSIDiv']=''; Txn['DivDays']=np.NaN
    LMax=Txn.dropna(subset=['RSILMaxL','CloseLMaxL'], how='all')  
    LMin=Txn.dropna(subset=['RSILMinL', 'CloseLMinL'], how='all') 
 
    if(gv.RSIHidDivIgnLRec):
        if(LMax.index[-1] == Txn.index[-1]):
            LMax.drop(LMax.tail(1).index,inplace=True)
        if(LMin.index[-1] == Txn.index[-1]):
            LMin.drop(LMin.tail(1).index,inplace=True)

    for i, (idx, Row) in zip(np.arange(len(LMax.index)), LMax.iterrows()):
        if (i==0): continue
        if((Row['Close'] < LMax['Close'].iloc[i-1]) and ('HD' in gv.RSIDiverg)):
            if(Row['RSI'] > LMax['RSI'].iloc[i-1]):
                Txn.at[idx, 'Action']=-1; Txn.at[idx, 'RSIDiv']='HD'
                Txn.at[idx,'PrevRSIDiv']=LMax.index[i-1]
                Txn.at[idx,'DivDays']=(Row['Date']- Txn.loc[LMax.index[i-1] , 'Date']).days
        elif((Row['Close'] > LMax['Close'].iloc[i-1]) and ('RD' in gv.RSIDiverg)):
            if(Row['RSI'] < LMax['RSI'].iloc[i-1]):
                Txn.at[idx, 'Action']=-1; Txn.at[idx, 'RSIDiv']='RD'
                Txn.at[idx,'PrevRSIDiv']=LMax.index[i-1]
                Txn.at[idx,'DivDays']=(Row['Date']- Txn.loc[LMax.index[i-1] , 'Date']).days
            
    for i, (idx, Row) in zip(np.arange(len(LMin.index)), LMin.iterrows()):
        if(i==0): continue
        if((Row['Close'] > LMin['Close'].iloc[i-1]) and ('HD' in gv.RSIDiverg)) :
            if(Row['RSI'] < LMin['RSI'].iloc[i-1]):
                Txn.at[idx, 'Action']=1; Txn.at[idx, 'RSIDiv']='HD' 
                Txn.at[idx,'PrevRSIDiv']=LMin.index[i-1]
                Txn.at[idx,'DivDays']=(Row['Date']- Txn.loc[LMin.index[i-1] , 'Date']).days
        elif((Row['Close'] < LMin['Close'].iloc[i-1]) and ('RD' in gv.RSIDiverg)):
            if(Row['RSI'] > LMin['RSI'].iloc[i-1]):
                Txn.at[idx, 'Action']=1; Txn.at[idx, 'RSIDiv']='RD' 
                Txn.at[idx,'PrevRSIDiv']=LMin.index[i-1]
                Txn.at[idx,'DivDays']=(Row['Date']- Txn.loc[LMin.index[i-1] , 'Date']).days
    
    if((CalcCV(Txn) > 0.25) and (gv.RangeBound)) :
        Txn['ActionRun'] = (Txn.groupby(Txn['Action'].ne(Txn['Action'].shift()).cumsum()).cumcount().add(1))              
        Txn['Action'] = np.where((Txn['ActionRun'] >= gv.BOutLimit), Txn['Action']*(-1), Txn['Action'])
    return(Txn)      

def CalcLMinMax(Txn, Cols, SmallGapPeriod=True):  

    ColSuffix=''; Period = gv.SLocMinMaxPeriod
    if (not SmallGapPeriod): 
        ColSuffix='L'; Period = gv.LLocMinMaxPeriod        
    for Col in Cols:
        Txn[Col+'LMin'+ColSuffix]=Txn.iloc[argrelextrema(Txn[Col].to_numpy(), np.less_equal, order=Period)[0]][Col]
        Txn[Col+'LMax'+ColSuffix]=Txn.iloc[argrelextrema(Txn[Col].to_numpy(), np.greater_equal, order=Period)[0]][Col]
    return(Txn)   
    
def FindTrend(RSI) :
    RetValue='DZ'
    if(RSI > gv.OS): RetValue='OS'; 
    elif(RSI < gv.OB): RetValue='OB'; 
    return(RetValue)
    
def CalcStockAttrib(Txn):
    gv.RSI=round(Txn['RSI'].mean()) ; gv.CV=CalcCV(Txn)
    if('Attrib' in gv.Action):
        StockAttrib = {'Stock': Txn['Stock'].iloc[0], 'StartDate':Txn['Date'].iloc[0],
           'EndDate': Txn['Date'].iloc[-1], 'RSI': gv.RSI, 'CV':gv.CV }
        StockAttrib=pd.DataFrame([StockAttrib])
        ou.SaveResult(StockAttrib, 'StockAttrib')

    return() 
    
def CalcCV(Txn):
    return(round(variation(Txn['Close']),2))
  
def CalcPortFolioRet(FileKey, NoOfStockToInvest):
    AllTxn = ou.GetDataFromKey(FileKey)
    AllTxn.sort_values(['Date'], inplace = True);  
    if(NoOfStockToInvest < gv.LimitNoOfStock) : StockLimit = NoOfStockToInvest
    else : StockLimit = gv.LimitNoOfStock
    CashInHand = StockLimit*gv.InitStockInvest; 
    AmtInv=0; StockInvested = 0
    for i, Row in AllTxn.iterrows():
        if(Row['Action'] == 1):
            if(StockInvested < StockLimit):  
                AmtInv = round(CashInHand / (StockLimit - StockInvested))
                StockInvested += 1 ; 
            else: AmtInv=0; 
        if(Row['Action'] == -1):
            AmtInv = round(AllTxn.loc[Row['PTxnIndex'],'AmtInv']*(1+(Row['LongPer']/100)))
            if(AmtInv != 0): StockInvested -= 1 ; 
        AmtInv = (AmtInv*Row['Action']); CashInHand -= AmtInv   
        AllTxn.at[i, 'AmtInv']=AmtInv;  AllTxn.at[i, 'CashInHand'] = CashInHand           
        AllTxn.at[i, 'NoOfStock']=StockInvested      
    
    StartDate = pd.to_datetime(AllTxn['Date'].iloc[0])
    EndDate = pd.to_datetime(AllTxn['Date'].iloc[-1])    
    HoldDays = (EndDate - StartDate)/pd.Timedelta(1, unit='d')  
    
    StartAmt = gv.StockLimit*gv.InitStockInvest; EndAmt = round(AllTxn['CashInHand'].iloc[-1])
    GainPer =  (EndAmt -  StartAmt ) * 100 / StartAmt 
    GainIRR = round(GainPer * 365/ HoldDays)
    print("Total  [Long] [Hold] [IRR] [", round(GainPer), "%] [", HoldDays, "] [",GainIRR, "%]") 
    print("  [Invested] [Final] [Gain] [", StartAmt, "] [", EndAmt, "] [", EndAmt - StartAmt, "]")
    return(AllTxn)    

def GenOrders(Orders):   
    Txn=Orders.copy() 
    Txn.dropna(subset=['Action'], inplace = True )
    Txn['PTxnAction']=Txn['Action'].shift(1)
    Txn.drop(Txn[Txn['Action'] ==  Txn['PTxnAction']].index, inplace = True)    
    if(len(Txn) > 0) :
        if(Txn['Action'].iloc[0] == -1):
            Txn.drop(Txn.head(1).index, inplace=True)            
    Txn['PTxnTradeDate']=Txn['TradeDate'].shift(1)
    Txn['PTxnTradePrice']=Txn['TradePrice'].shift(1)  
    Txn['PTxnIndex']=Txn.index; Txn['PTxnIndex']=Txn['PTxnIndex'].shift(1)    
    Txn['HoldDays'] = (Txn['Date']- Txn['PTxnTradeDate']) / pd.Timedelta(1, unit='d')  
    Txn['GainPer']=(Txn['TradePrice'] - Txn['PTxnTradePrice'])*100 / Txn['PTxnTradePrice'] 
    Txn['GainIRR']=Txn['GainPer'] * 365/ Txn['HoldDays']         
    Txn['LongPer'] = np.where(Txn['Action'] == -1, Txn['GainPer'], np.NaN)
    Txn['LongIRR']=Txn['LongPer'] * 365/ Txn['HoldDays']         
    Txn['ShortPer'] = np.where(Txn['Action'] == 1, Txn['GainPer'], np.NaN)
    Txn['ShortIRR']=Txn['ShortPer'] * 365/ Txn['HoldDays']         

#    StartAmt = InitStockInvest; EndAmt = round(Txn['CashInHand'].iloc[-1])
#    ((df.fillna(0)+1).cumprod()-1).iloc[-1]
    TotalLongPer = round(((1 + Txn['LongPer'].fillna(0)/100).prod() - 1)*100)
    TotalHoldDays =  round(Txn.loc[Txn['Action'] == -1, 'HoldDays'].sum())
#    Stock=Txn['Stock'].iloc[-1]
    print("[Long] [Hold] [IRR] [", TotalLongPer,"%] [", 
        TotalHoldDays,"] [", round(TotalLongPer * 365 / TotalHoldDays ),"%]")
    return(Txn) 
    
def GetIndextReturn(FromDate, ToDate):
    SIndex='^NSEI'
    print(SIndex, " Returns")
    IndexData = GetBulkData(SIndex, FromDate)
    CalcMktReturns(IndexData, FromDate, ToDate)
    return()
    
def CalcMktReturns(Txn, FromDate, ToDate):
    StartValue=Txn['Close'].iloc[0]
    EndValue=Txn['Close'].iloc[-1]
    GainPer = round((EndValue - StartValue)*100 / StartValue)
    HoldDays = (ToDate - FromDate).days 
    print("Mkt Returns  [Long] [Hold] [IRR] [",GainPer, "%] [", HoldDays, "] [",
       round(GainPer * 365/ HoldDays), "%]") 
    return() 
    
def PrepFinalList(FileKey, ListType, ListFor, NoOfStocks, OverWrite):
    Order={'Buy':True, 'Sell':False} 
    Txn=ou.GetDataFromKey(FileKey)
    if(ListType == 'RSI'): 
        Result=Txn.groupby(['Stock'], as_index=False).tail(1)
        Result=Result[(Result['RSI'] >= gv.OS) | (Result['RSI'] <= gv.OB)]
        Result.sort_values([ListType], ascending=Order[ListFor], inplace = True)
        Result=Result.head(NoOfStocks)
    elif(('HD' in ListType) | ('RD' in ListType)):
        Txn['RSIDiv'] = Txn['RSIDiv'].replace('nan', np.nan)
        Result=Txn[Txn['RSIDiv'].isin(ListType)]
        if(ListFor == 'Buy'): 
            Result=Result[Result['Action'] == 1]
        else:
            Result=Result[Result['Action'] == -1]
        
    Result=Result.groupby(['Stock'], as_index=False).tail(1)  
    Result.sort_values(['Date'], ascending=[False], inplace = True)             
    Result=Result.head(NoOfStocks)
    StockLast=GetLastRecs(Txn)
    Result = pd.merge(Result, StockLast, on=['Stock'], how='left')
    Result['PerGain']=round((Result['LastClose']-Result['Close'])*100/Result['Close'],2)
    print("\n========== List for ", ListType, ListFor,"==========") 
    if(Result.empty): 
        print('No Pattern for ', ListType, ListFor )
    else :
        for Col in ['Close','LastClose']: Result[Col]=round(Result[Col],2)
        print(Result.to_string(columns=gv.TechIndToDisp))
#        print(Result[gv.TechIndToWrite])
        if(gv.ToTradeFile): 
            ou.SaveResult(Result, 'ToTrade', OverWrite=OverWrite, FileCols=gv.TechIndToFile, Recycle='W')

    RetValue = Result['Stock'].values.tolist()
    return(RetValue)

def GetLastRecs(Txn):
    
    StockLast = Txn.groupby(['Stock'], as_index=False).tail(1)
    StockLast = StockLast[['Stock','Close','High','Low','RSI']]; 
#    print(StockLast)
    StockLast.rename(columns={"Close": "LastClose", "High":"LastHigh",
        "Low":"LastLow", "RSI":"LastRSI"}, inplace=True)
    StockLast2 = Txn.groupby(['Stock'], as_index=False).nth(-2)
    StockLast2 = StockLast2[['Stock','Close','High','Low']]; 
    StockLast2.rename(columns={"Close": "Last2Close", "High":"Last2High","Low":"Last2Low"}, inplace=True)
    Recs = pd.merge(StockLast, StockLast2, on=['Stock'], how='left')

    StockLast3 = Txn.groupby(['Stock'], as_index=False).nth(-3)
    StockLast3 = StockLast3[['Stock','Close']]; 
    StockLast3.rename(columns={"Close": "Last3Close"}, inplace=True)
    Recs = pd.merge(Recs, StockLast3, on=['Stock'], how='left')  
    
    for Col in Recs.columns:
        if(Col == 'Stock'): continue
        Recs[Col]=round(Recs[Col],2)
        
    return(Recs)

def StocksToTrade(FileKey) :            
    Result=[]; OverWrite=True
    for i in  gv.ListFor: 
        for j in gv.ListType:
            List = PrepFinalList(FileKey, j, i, gv.NoOfStocks, OverWrite)
            OverWrite=False
            Result.extend(x for x in List if x not in Result)

    if(gv.UploadGDrive):
        ou.AddFileToGDrive(gv.RptDir+gv.RepFiles['ToTrade'])
    RetValue = ' '.join(Result)
    return(RetValue) 
    
def ProcHolding():
    xls = pd.ExcelFile(gv.HoldTxnFile)
    sheets = xls.sheet_names
    df = pd.DataFrame()
#    print(sheets)
    for sheet in sheets:
        sheetdf = pd.read_excel(gv.HoldTxnFile, sheet_name=sheet, encoding='utf8')    
        if (sheet == 'Satvinder'):
            sheetdf['Account'] = 'Satvinder'
        else:
            sheetdf['Account'] = 'Daljeet'
        df = pd.concat([df, sheetdf],sort=True)
    df.dropna(axis=0, subset=['FinYear', 'Stock'],inplace=True) 
    df['Stock']=df['Stock']+'.NS'  ;  
    df=df[df['FinYear'] >= 2020]
    df['BuyPrice']=round(df['BuyPrice'],2); df['SellPrice']=round(df['SellPrice'],2)
    df['BuyDate']=df['BuyDate'].dt.date
    df['SellDate']=df['SellDate'].dt.date

    print('\n===== Recent Buy Positions =====')
    RBuy=df.sort_values(['BuyDate'], ascending=[False]).head(15)   
    RBuy['LTP'] = RBuy['Stock'].apply(lambda x: round(si.get_live_price(x),2))
    RBuy['Per'] = round((RBuy['LTP'] - RBuy['BuyPrice']) * 100 / RBuy['BuyPrice'],2)
    print(RBuy[['Stock','BuyDate','BuyPrice','Qty','LTP', 'Per']])

    RBuy['GStock']=RBuy['Stock'].apply(lambda x : 'NSE:'+x[:-3])
    RBuy[['GStock','BuyDate','BuyPrice', 'Qty']].to_csv(gv.RptDir+'Buy.csv')  

    print('\n===== Recent Sell Positions =====')
    RSell=df.sort_values(['SellDate'], ascending=[False]).head(15)   
    RSell['LTP'] = RSell['Stock'].apply(lambda x: round(si.get_live_price(x),2))
    RSell['Per'] = round((RSell['LTP'] - RSell['SellPrice']) * 100 / RSell['SellPrice'],2)
    print(RSell[['Stock','SellDate','SellPrice','Qty','LTP', 'Per']])

    RSell['GStock']=RSell['Stock'].apply(lambda x : 'NSE:'+x[:-3])
    RSell[['GStock','SellDate','SellPrice','Qty']].to_csv(gv.RptDir+'Sell.csv') 

    print('\n===== Max Deviations from Buy Price =====')    
    RBuy=df.sort_values(['Stock','BuyDate'], ascending=[True, False])
    RBuy=RBuy.groupby(['Stock'], as_index=False).first()   
    RBuy['LTP'] = RBuy['Stock'].apply(lambda x: round(si.get_live_price(x),2))
    RBuy['Per'] = round((RBuy['LTP'] - RBuy['BuyPrice']) * 100 / RBuy['BuyPrice'],2)
    RBuy = RBuy.sort_values(['Per'], ascending=[False])
    print(RBuy[['Stock','BuyDate','BuyPrice','LTP','Per']])
    
    
    print('\n===== Max Deviations from Sell Price =====')  
    RSell=df.dropna(axis=0, subset=['SellPrice'])
    RSell=RSell.sort_values(['Stock','SellDate'], ascending=[True, False])
    RSell=RSell.groupby(['Stock'], as_index=False).first()   
    RSell['LTP'] = RSell['Stock'].apply(lambda x: round(si.get_live_price(x),2))
    RSell['Per'] = round((RSell['LTP'] - RSell['SellPrice']) * 100 / RSell['SellPrice'],2)
    RSell = RSell.sort_values(['Per'], ascending=[False])
    print(RSell[['Stock','SellDate','SellPrice','LTP','Per']])

