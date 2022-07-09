import datetime as dt
import sys
import os

import OtherUtils as ou
import StockUtils as su
import GraphUtils as gu
import GlobalVars as gv
try: 
    print('Process Start :', gv.StartTime.strftime('%H:%M:%S'))        
#    ou.AddFileToGDrive('Buy.csv'); raise(gv.DoNothing)
#    ou.ReadGoogleSheet(); raise(gv.DoNothing)
#    su.ProcHolding(); raise(gv.DoNothing)

    sys.path.append(os.path.abspath(gv.RootDir)); ou.CleanFiles()
    Stocks = ou.GetStockList(gv.ListOfStocks, gv.InFile) 
    if('HistPat' in gv.Action): ou.GetHistPat(Stocks); raise(gv.DoNothing)
    if('Find' in gv.Action): PatResult, Stocks=su.FindStocks(Stocks)
    if('CreateAll' in gv.History): Stocks = ou.GetStockList(gv.ListOfStocks, gv.InFile)
    if(('History' in gv.Action) | ('Graph' in gv.Action)):
        for i, Stock in enumerate(Stocks.split()):
           print('\rHistorical data ', i+1, Stock,'->               ', end='')
           StockData=su.ProcData(PatResult, Stock)
           if('Graph' in gv.Action): gu.DrawGraphs(Stock, StockData)     
#    Orders = su.CreateStockOrders(PatResult, Stock); ou.SaveResult(Orders, 'Orders')
#    su.CalcMktReturns(StockData, FromDate, ToDate)
#    PortFolioRet=su.CalcPortFolioRet('Orders', len(StockList.split()))
#    ou.SaveResult(PortFolioRet, 'InvestData');  su.GetIndextReturn(FromDate, ToDate)
except gv.DoNothing:
    print('Done ...')
except Exception as e:
    print("\nException : ",e)


print("\nProcess", dt.datetime.now().strftime('%Y-%m-%d'), ": Start [", gv.StartTime.strftime('%H:%M:%S'), "] End [",  
    dt.datetime.now().strftime('%H:%M:%S'),"] Taken [",dt.datetime.now() - gv.StartTime, "]")