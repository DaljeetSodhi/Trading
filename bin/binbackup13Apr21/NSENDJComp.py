# -*- coding: utf-8 -*-
"""
Comparing Dow Jones closing with Next Day Indian Market

@author: dsodh
"""
import StockUtils as su
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt

FromDates=['2020-01-01', '2007-01-01', '2000-01-01']
#FromDates=['2007-01-01', '2000-01-01']
#Prices=['High', 'Low', 'Close']
OneByOne=True
GraphSize=(25,8)
MaxPrice=12362
Data=pd.DataFrame()
from sklearn.preprocessing import MinMaxScaler
class Error(Exception): pass;
class DoNothing(Error): pass ;

def CreateGraph(FDate, Price, Title):
    FromDate=pd.to_datetime(FDate, format='%Y-%m-%d')  
    ToDate= pd.to_datetime((FromDate+dt.timedelta(days=365*(3))).date(), format='%Y-%m-%d')
#    print(i, FromDate, ToDate)
    Data=pd.DataFrame()
    if(FromDate < pd.to_datetime('2004-01-01', format='%Y-%m-%d')):
        Data = pd.concat(map(pd.read_csv, ['NSEData.csv', 'NSEData1.csv','NSEData2.csv']))
        Data.set_index('Date', inplace=True)
#        print('File Reading')       
#        print(Data)
    else:
        Data=su.GetBulkData('^NSEI', FromDate, ToDate)
#    print(Data)
    Data=Data[[Price]]
    DataMaxid=Data.idxmax().values[0]
#    print("=====================\n",DataMaxid)
    Data= Data.loc[DataMaxid:]
    DataMP=Data[Price].iloc[0]; Factor=MaxPrice/DataMP
    Data[Price]=Data[Price]*Factor
    Data.reset_index(inplace = True)
#    print(Data)
    plt.plot(Data.index.values, Data[Price], label=FDate[:4])
    if(OneByOne): 
        plt.legend()
        plt.title(Title)
    return()    

#try: 
def CompareNSEFalls(Prices) :
    try:
    #    plt.figure(figsize=(20,7))
        if(not OneByOne):
            plt.figure(figsize=GraphSize)
            plt.grid(True, which="both")
        for Price in Prices:
            if(OneByOne): 
                plt.figure(figsize=GraphSize)
                plt.grid(True, which="both")
            
    #        print('Comparing ', Price , '.........')
            for i, FDate in enumerate(FromDates): 
                CreateGraph(FDate, Price, Price)    
            if(OneByOne): plt.show()
     
        if(not OneByOne): plt.show()
        """
        raise DoNothing
        
        History = su.GetBulkData('^NSEI', FromDate, ToDate)
        History=History[['Close']]
        HistoryMaxid=History.idxmax().values[0]
        print("=====================\n",HistoryMaxid)
        History= History.loc[HistoryMaxid:]
        History.reset_index(inplace = True)
        print(History)
    
        History.to_csv('History.csv') 
        
        FromDate=pd.to_datetime('2020-01-01', format='%Y-%m-%d') 
        ToDate=pd.to_datetime('2020-03-11', format='%Y-%m-%d')
    
        Current = su.GetBulkData('^NSEI', FromDate, ToDate)
        Current=Current[['Close']]
        Current['Close']=Current['Close']/2
        CurrentMaxid=Current.idxmax().values[0]
        print("=====================\n",CurrentMaxid)
        Current=Current.loc[CurrentMaxid:]
        Current.reset_index(inplace = True)
        print(Current)
    
        Current.to_csv('Current.csv') 
    
    #    scaler = MinMaxScaler()
    #    scaler.fit(History)
    #    History = scaler.transform(History)
        
    #    scaler = MinMaxScaler()
    #    scaler.fit(Current)
    #    History = scaler.transform(Current)
    
        plt.figure(figsize=GraphSize)
        
        plt.plot(History.index.values, History['Close'], color='b')  
        plt.plot(Current.index.values, Current['Close'], color='r')  
            
        plt.show()
       
        raise DoNothing
    
        FromDate=pd.to_datetime('2014-01-01', format='%Y-%m-%d') 
        ToDate=pd.to_datetime('2020-01-23', format='%Y-%m-%d')
        ToDate=pd.to_datetime((pd.datetime.now()).date(), format='%Y-%m-%d')
        
        Stocks='^DJI ^NSEI'
        Data = su.GetBulkData(Stocks, FromDate, ToDate)
        Data=Data['Close']
        print(Data)
        Data=Data.rename(columns={"^DJI": "DJI", "^NSEI": "NSEI"})
        print(Data.columns)
        Data = Data.fillna(method = 'ffill') 
        Data['DJI_P'] = Data['DJI'].shift(1)
        Data['NSEI_P'] = Data['NSEI'].shift(1)
        
        Data['DJI_C'] = (Data['DJI'] - Data['DJI_P'])*100/Data['DJI_P']
        Data['NSEI_C'] = (Data['NSEI'] - Data['NSEI_P'])*100/Data['NSEI_P']
        Data['DJI_C']=round(Data['DJI_C'],4)
        Data['NSEI_C']=round(Data['NSEI_C'],4)
        
        Data['MovedWith']=np.where((Data['DJI_C'].shift(1) > 0 ) & (Data['NSEI_C'] > 0 ), 
            'UP', np.NaN)
        Data['MovedWith']=np.where((Data['DJI_C'].shift(1) < 0 ) & (Data['NSEI_C'] < 0 ), 
            'DN', Data['MovedWith'])
        
        print(Data)
        Data.to_csv('Result.csv') 
        """
    except DoNothing:
        print('Done ...')
    return()
CompareNSEFalls(['High','Close'])
    
"""
scaler = MinMaxScaler()
scaler.fit(Data)
Data = scaler.transform(Data)
print(Data)
"""

