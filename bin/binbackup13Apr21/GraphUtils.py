import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
#from scipy.stats import variation
from matplotlib import ticker
#import datetime as dt

import StockUtils as su
import OtherUtils as ou
import GlobalVars as gv

def DrawGraphForStock(Stock):
    ou.CleanFiles()
    if(Stock != ""): 
        PatResult, Stock=su.FindStocks(Stock)
        StockData=su.ProcData(PatResult, Stock)
        DrawGraphs(Stock, StockData)  
    return()

def DrawGraphs(Stock, PatResult):
#    if(DateRange=='Small'):
#        PatResult=PatResult[PatResult['Date'] >= gv.SmallRange]
#    PatResult = PatResult.iloc[gv.DaysForTech:]

    if('RSIDiv' in PatResult.columns):
        StartIndex=Stock+'_'+gv.GraphStart
        PatResult=PatResult[PatResult.index.values >= StartIndex]
        PatResult['PrevRSIDiv']=np.where((PatResult['PrevRSIDiv'] >= StartIndex), 
                                PatResult['PrevRSIDiv'], np.NaN)
        PatResult['DivDays']=np.where((PatResult['PrevRSIDiv'] >= StartIndex), 
                                PatResult['DivDays'], np.NaN)
    
        PatResult['RSIDiv']=np.where((PatResult['PrevRSIDiv'] >= StartIndex), 
                                PatResult['RSIDiv'], np.NaN)
    plt=PlotPriceWInd(Stock+' All indicators', PatResult)# plt.show()
    plt=PlotRSI(Stock + ' RSI',  PatResult)# plt.show()
    return()
    
def PlotRSI(Title, Txn):

    plt.figure(figsize=gv.RSIGraphSize); 
#    plt.xlim([dt.date(2017, 1, 1), dt.date(2019, 5, 1)])
#    plt.margins(x=0)
#    plt.rcParams['axes.xmargin'] = 0

#    plt.figure.yaxis.set_label_position("right")
    plt.plot(Txn['Date'], Txn['RSI'], color=gv.RSILineColor)
    plt.grid(True, which="both")
    RSIPoints=Txn.dropna(subset=['Action'])  
    plt.scatter(RSIPoints['Date'], RSIPoints['RSI'], c='b')
    for Y in gv.RSILStyle.keys():
        plt.axhline(y=Y, color=gv.RSILStyle[Y])
    plt.title(Title)

    if(gv.DispDiv) : PlotDiverg(Txn, 'RSI', plt)
    if(gv.Patterns['RSIMA']):
        Cols = [col for col in Txn.columns if 'RSI_MA' in col]
        for Col in Cols:
            plt.plot(Txn['Date'], Txn[Col], color='b')    
#    plt.show()
#    Pdf.savefig(fig)
#    plt.xlim([dt.date(2018, 1, 1), dt.date(2020, 5, 1)])
    return(plt)

def PlotPriceWInd(Title, Txn):
    
    CV = su.CalcCV(Txn); 
    plt.figure(figsize=gv.PriceGraphSize); 
#    plt.xlim([dt.date(2017, 1, 1), dt.date(2019, 5, 1)])
#    plt.margins(x=0)
#    plt.rcParams['axes.xmargin'] = 0
    plt.grid(True, which="both")
    if(CV > gv.CVLogThreshold): 
        plt.semilogy(Txn['Date'], Txn['Close'], color=gv.CloseLineColor) 
        plt.gca().yaxis.set_minor_formatter(ticker.ScalarFormatter())
        plt.gca().yaxis.set_major_formatter(ticker.ScalarFormatter())
    else:
        plt.plot(Txn['Date'], Txn['Close'], color=gv.CloseLineColor)        

    for Col in ['OrderType', 'Action', 'RSI', 'RSIDiv']:
        Txn[Col]= Txn[Col].replace('nan', np.nan)
        
    if(gv.PlotFabLevel): PlotFabRet(Txn, plt)
    if(gv.Patterns['MA']): 
        SMACols = [col for col in Txn.columns if 'Close_MA' in col]
        for Cols in SMACols:
            plt.plot(Txn['Date'], Txn[Cols], 'g--') 
    if(gv.DispDiv) : PlotDiverg(Txn, 'Close', plt)  
    if (gv.NoOfSupNRes) > 0 : RSIDivSupNRes(Txn)    
#        plt.plot(Txn['Date'], Txn['RSIDiv'], color = 'blue')
    Trade=Txn.dropna(subset=['OrderType']).copy()
    Trade['Action'] = Trade['Action'].fillna(0)
    Trade['Color'] = [gv.Color[i] for i in Trade['Action']]
    Trade['Marker'] = [gv.Marker[i] for i in Trade['OrderType']]
    for i in gv.Marker:
        MarkerTxn=Trade[Trade['OrderType'] ==  i]
        plt.scatter(MarkerTxn['Date'], MarkerTxn['Close'],c=MarkerTxn['Color'],
                    marker=gv.Marker[i], label=i)

    if(gv.Patterns['PerLevelBS']):
        Trade['PerFMinMax'] = Trade['PerFMinMax'].fillna(0)
        for i, Row in Trade.iterrows():
#            if(Row['OrderType'] in ('HP', 'LP')):
            Price=Row['Close']
            Price = str(round(Price)) if (Price > 100) else str(round(Price,1))
            Label = str(round(Row['PerFMinMax'])) + ',' + Price
#            else:
#                Label = round(Row['PerFMinMax'])
            plt.annotate(Label, (Row['Date'], Row['Close']))
    plt.legend()
    plt.title(Title)
#    plt.xlim([dt.datetime(2018,1,1), dt.datetime(2020,1,1)])
#    plt.ylim([50,100])
    return(plt)    
def RSIDivSupNRes(Data):
    LTP=Data['Close'].iloc[-1]    
#   Commented out  when pd.datetime is connented for future deprication             
#    Data=Data[(Data['RSIDiv'].isin(['RD','HD']) & (Data['Date']> gv.FromSupNRes))]
    Data['NearDiv']=abs(Data[Data['RSIDiv'].isin(['RD','HD'])]['Close']-LTP)
    Data=Data.sort_values(['NearDiv'], ascending=[True])    
    for i, Row in Data.head(gv.NoOfSupNRes).iterrows():
        plt.axhline(y=Row['Close'], color='b', linestyle='--')
    return()   
def PlotDiverg(Data, Col, plt):
    Txn= Data.copy()    
    Txn['Action'] = Txn['Action'].fillna(0)
    RSIColor={'HD':'green', 'RD':'red', 'RF':'blue', 'HF':'yellow'}
    CloseColor={1:'green', -1:'red', 0:'grey'}
    Result= Txn.dropna(subset=['RSIDiv']); 
    for i, Row in Result.iterrows():
#        print(i,Row)
        SDate = Txn.loc[ Row['PrevRSIDiv'] , 'Date']
        SVal = Txn.loc[ Row['PrevRSIDiv'] , Col]
        if (Col == 'RSI'): 
            plt.annotate(' '+str(round(Row['DivDays'])), (Row['Date'], Row[Col]))
            Color=RSIColor[Row['RSIDiv']]
        else:
#            if(Row['Action'] == 'nan'):
#                Color = 'yellow'
#            else:
             Color=CloseColor[Row['Action']]; 
            
        plt.plot([SDate, Row['Date']], [SVal, Row[Col]], color=Color)
    if (Col == 'RSI'): 
        Legend=RSIColor
        Legend['Div Days']=gv.RSILineColor
        CustomLegend(plt, Legend)
 
    return()

def CustomLegend(plt, Legend):
    patchList = []
    for key in Legend:
            data_key = mpatches.Patch(color=Legend[key], label=key)
            patchList.append(data_key)   
    plt.legend(handles=patchList)
    return()       
 
def PlotFabRet(Txn, plt, RetType='Up'):
#Retracement levels 
    NoOfRecs=250 # approximately one year
    Color={'Up':'b', 'Down':'g'}
    RetLevel=[0, 0.236, 0.5, 0.618, 0.786, 1]
    
    Color=Color[RetType]
    
    if(RetType == 'Up'):
        FromValue = Txn['Close'].tail(NoOfRecs).min()
        LimitValue = Txn['Close'].max()
        Factor=1
    else:
        FromValue = Txn['Close'].tail(NoOfRecs).max()
        LimitValue = Txn['Close'].min()
        Factor=0

    TextXPos = Txn['Date'].iloc[len(Txn)//2]
    for i in RetLevel:
        Level=FromValue*(Factor+i)
        if((RetType == 'Up') and (Level >= (LimitValue)*1.2)): break
        if((RetType == 'Down') and (Level <= (LimitValue)*0.8)): break
        plt.axhline(y=Level, color=Color, linestyle='-')
        LineText=str(round(Level,1)) + '(' + str(round(i*100,1))+'%)'
        plt.text(TextXPos, Level, LineText, backgroundcolor='w')
    return()

