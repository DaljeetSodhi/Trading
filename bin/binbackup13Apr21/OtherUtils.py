import pandas as pd
import numpy as np
import datetime as dt
import os
import ipywidgets as ipw

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from nsetools import Nse

#import matplotlib.backends.backend_pdf as pf
import GlobalVars as gv

def CreatUI():
    CleanFiles()
    ListOfStocks=GetProcStocks()
    Stock=ipw.Combobox(options=ListOfStocks, 
        description='Stocks:', ensure_option=True)
    StockGroup=ipw.SelectMultiple(options=gv.DFile.keys() ,  #rows=10,
        description='Stock Groups')
        
    UI=ipw.HBox([Stock, StockGroup])
    return(UI, [Stock, StockGroup])

def on_execute_clicked(Stock):
    print('Something happens!', Stock)
    return()
def GetProcStocks():
#    onlyfiles = [f for f in os.listdir(mypath) if isfile(join(mypath, f))]
    return([File[:-4] for File in os.listdir(gv.HistDir)])
def CleanFiles():
    for file in gv.RepFiles.values():
        FileName=gv.RptDir+file
        if(os.path.isfile(FileName)): os.remove(FileName)

#    pdf = pf.PdfPages(gv.RptDir+gv.RepFiles['GraphData'])
    return()

def SaveResult(Data, FileKey, OverWrite=False, FileCols=None, Recycle='D'):    
    FP=""
    if(Recycle == 'W'):
        FP=dt.datetime.now().weekday()
        if (dt.datetime.now().time().hour >= 16): FP += 1
        if(FP > 4): FP=0
    
    FileName = gv.RptDir+str(FP)+gv.RepFiles[FileKey]
    
    if(FileCols): Data = Data[FileCols]
    if(os.path.isfile(FileName) and (not OverWrite)):
        Data.to_csv(FileName, mode='a', header=False)
    else: Data.to_csv(FileName)       
    return()

def CreateHistData(Stock, Data, OverWrite=False):
    FileName = gv.HistDir+Stock+'.csv'

    if(('Update' in gv.History) or (not os.path.isfile(FileName))):
#        print('Creating History :', end=' ')
#        Today=pd.to_datetime((pd.datetime.now()).date(), format='%Y-%m-%d')
        Today=dt.date.today()
        LastRecDate=Data.Date.iloc[-1]; 
        if(Today == LastRecDate): # Today's data may not be the close price
            Data = Data.iloc[:-1]
        Data.to_csv(FileName)         
    return()
    
def ReadHistData(Stock):
#    print('Reading data from history', Stock)
    FileName = gv.HistDir+Stock+'.csv'

    if(not os.path.isfile(FileName)):
        print('No History :', end='\n')
        return(pd.DataFrame())
    else:                
        Data = GetDataFromFile(FileName)
        return(Data)

def IsHistExist(Stock):
    RetValue = False
    FileName = gv.HistDir+Stock+'.csv'
    if(os.path.isfile(FileName)):
        RetValue = True   
    return(RetValue)   
    
def PdfToFile(fig):
    global FirstTime
    if(gv.SaveGraph):
#        print("First time", FirstTime)
        if(FirstTime):
#            pdf = pf.PdfPages(gv.RptDir+gv.RepFiles['GraphData'])
            FirstTime=False
#        pdf.savefig(fig)
    return()

def GetDataFromKey(FileKey):
    FileName = gv.RptDir+gv.RepFiles[FileKey]
    return(GetDataFromFile(FileName))
    
def GetDataFromFile(FileName):
    Data = pd.read_csv(FileName, index_col=0, skipinitialspace=True)
    Data['OrderType'] = Data['OrderType'].astype(str)
    Data['RSIDiv'] = Data['RSIDiv'].astype(str)
    Data['Date'] =  pd.to_datetime(Data['Date'])
    Data['TradeDate'] = pd.to_datetime(Data['TradeDate'])
    return(Data)

def GetLastDay(ToDate):
#    PDate = Date + dt.timedelta(days=-1)
    RetDate = ToDate
    StartTime = dt.datetime.now()  
    CurrentHour=StartTime.hour
#    Today = pd.to_datetime((pd.datetime.now()).date(), format='%Y-%m-%d')
    Today=dt.date.today()
    if(ToDate >= Today):
        if(IsMarketOpen(ToDate)):
            if(CurrentHour  < 9):
                RetDate = Today
            else:
                RetDate=Today - dt.timedelta(days=1)
#                RetDate=pd.to_datetime((Today+dt.timedelta(days=-1)).date(), format='%Y-%m-%d')
        else:
            RetDate = Today
    return(RetDate)
     
def IsMarketOpen(Date):
    ListOfHol=('2020-02-21', '2020-03-10', '2020-04-02', '2020-04-06', 
        '2020-04-10', '2020-04-14', '2020-05-01', '2020-25-05', '2020-10-02', 
        '2020-11-16', '2019-11-30', '2020-12-25')
    RetValue = True
    
    if(Date.strftime('%a') in ('Sat','Sun')): RetValue = False        
    if(Date.strftime('%Y-%m-%d') in ListOfHol): RetValue = False
    return(RetValue)  

def GetStockList(Stocks='', FileName=[], AddFnO = True):
    if(Stocks == ''):
        if(len(FileName) == 0): return('')
        StockFileList=[gv.DFile[i] for i in FileName]
        df = pd.concat(map(pd.read_csv, StockFileList), sort=False)
        if('Symbol' in df.columns):
            if('Stock' not in df.columns): df['Stock']=np.NaN
            df['Stock'] = df['Stock'].fillna(df['Symbol']+'.NS')
        if(AddFnO):
            FnOList=GetFnOList()
            print(df.shape)
            df = pd.concat([df, FnOList])
            print(df.shape)
        df.sort_values('Stock', inplace=True) 
        print("Combining All stocks ====================", len(df), end =" ")
        df.drop_duplicates(subset ='Stock',inplace = True) 
        print("After Deduping ==========================", len(df))
        StockList = pd.Series(df['Stock']).str.cat(sep=' ')
    else:
        StockList = Stocks
    for Stock in gv.DiscStock: StockList=StockList.replace(Stock,'')       
    return(StockList)
    
def RoundQty(Qty):
    RetQty = Qty // 1
    if (RetQty > 1000):
        RetQty = (RetQty // 10 ) * 10
    elif(RetQty > 20):
        if(RetQty % 2 >= 1) : RetQty -= 1       
    return (RetQty)

def RoundPrice(Price, Up = False):
    LDigit = (( Price * 100 ) % 10 ) // 1
    SLDigit = (( Price * 10 ) % 10 ) // 1
    
    Delta = 0.05 if LDigit > 5 else 0   
    RetPrice = Price // 1 + SLDigit*0.1 + Delta
    if(Up): RetPrice += 0.05
    
    return(round(RetPrice,2)) 

def GetHistPat(Stocks):
    print("Get Stock Pattern from hist", Stocks)
    Result=pd.DataFrame()
    Cols = ['Stock', 'Date', 'RSI', 'Close', 'DivDays','RSIDiv', 'Action']
    for Stock in Stocks.split():
        FileName = gv.HistDir+Stock+'.csv'
        if(not os.path.isfile(FileName)):
            print('No History :', FileName, end='\n')
            continue
        df=pd.read_csv(FileName, index_col=0)

        df=df[Cols];df=df[(df['DivDays'] > 0)]
        df=df[(df['Date'] <= gv.HistPatDate)]
        Result=Result.append(df)

    for i in gv.TradeVal:
        Disp=Result[(Result['Action'] == i)]
        print("========= Stocks To ",gv.TradeVal[i])
        for Div in gv.ListType:
            if(gv.HistFailedDiv):
                RSIDivGroup= str(Div[0][0])  # both fake and regular F/D 
                Disp=Disp[(Disp['RSIDiv'].astype(str).str[0] == RSIDivGroup)]         
            else:
                RSIDivGroup= str(Div[0])  ; print("-------", RSIDivGroup)             
                Disp=Disp[(Disp['RSIDiv'] == RSIDivGroup)]                         
            Disp=Disp.sort_values(['Date'], ascending=[False])
            print(Disp.head(gv.NoOfStocks).to_string(index=False))
        
    return()
def ReadGoogleSheet():
#worked as of 19-Aug-20
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)   
    sheet = client.open("StockHoldNAnalysis").sheet1
    list_of_hashes = sheet.get_all_records()
    print(list_of_hashes)
    return()

def AddFileToGDrive(FileName):
#need to create OAuth2.0 which was deleted on 19-Aug-20
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("MyGDiveCreds.txt")    
    if gauth.credentials is None:
        gauth.GetFlow()
        gauth.flow.params.update({'access_type': 'offline'})
        gauth.flow.params.update({'approval_prompt': 'force'})  
        gauth.LocalWebserverAuth()    
    elif gauth.access_token_expired:
         gauth.Refresh()
    else:
         gauth.Authorize()
    gauth.SaveCredentialsFile("MyGDiveCreds.txt")        
    drive = GoogleDrive(gauth)  
    Path, FNOnly = os.path.split(FileName)
    print("FileNAme to upload", FNOnly)
    f = drive.CreateFile({'title': FNOnly}) 
    f.SetContentFile(FileName) 
    f.Upload() 
    f = None #bug to clear , otherwise cannot open file 
def GetFnOList():
    nse = Nse()
    FnO=pd.DataFrame(list(nse.get_fno_lot_sizes().items()), columns=['Stock', 'Lot'])
    FnO=FnO[~FnO.Stock.str.contains("NIFTY")]
    FnO['Stock']=FnO['Stock']+'.NS'
#    FnO=FnO.tail(2)
    return(FnO)
