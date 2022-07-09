import pandas as pd
import datetime as dt

StartTime = dt.datetime.now()  
#ToDate=pd.to_datetime((pd.datetime.now()).date(), format='%Y-%m-%d')
ToDate=dt.date.today()
#FromDate=DataFromDate=pd.to_datetime((ToDate+dt.timedelta(days=(-600))).date(), format='%Y-%m-%d') 
FromDate=ToDate - dt.timedelta(days=365*1.5)
#FromDate=pd.to_datetime('2016-01-01', format='%Y-%m-%d') 
#ToDate=pd.to_datetime('2020-04-01', format='%Y-%m-%d')
GraphStart='2019-10-01'
#ListType=['RSI',['HD','RD']]; ListFor=['Buy','Sell']; NoOfStocks=10
#ListType=[['HD','RD']]; ListFor=['Buy','Sell']; NoOfStocks=10
ListType=[['HD']]; ListFor=['Buy','Sell']; NoOfStocks=20
ListOfStocks = ""
#RunDayToDay=True
#AddLTP = False; #AddLTP = False; 
Action=['Find','Graph', 'History','Attrib','NoHistPat']
TradeVal={1:'Buy',-1:'Sell'}
HistPatDate='2020-08-04'; HistFailedDiv=True
#History = ['NoReadRaw', 'ReadProc','WriteProc', 'NoUpdate','NoCreateAll'] 
History = ['NoReadRaw', 'ReadProc','WriteProc', 'NoUpdate','NoCreateAll'] 
RootDir = '../'
RptDir = RootDir+'reports/'; DataDir = RootDir+'config/'
HistDir = RootDir+'history/'

FnOList = DataDir+'FnOList.csv'
ToTradeFile = True; UploadGDrive=False
TechIndToDisp = ['Stock','Date', 'RSI', 'Close', 'DivDays', 'PerGain', 
    'LastRSI', 'LastClose', 'LastHigh','LastLow']
TechIndToFile = ['Stock','Date', 'RSI', 'Close', 'DivDays', 'RSIDiv', 
    'PerGain', 'LastRSI','Action','LastClose', 'LastHigh', 'LastLow', 
    'Last2Close', 'Last2High', 'Last2Low','Last3Close']
TradingCols = ['Stock','Date', 'RSI', 'Close', 'LastRSI','PerGain',
                'PDay2P', 'PDayP','DayP', 'LTP', 'Lot']
DFile={'N50':'Nifty50','N100':'Nifty100','PSU':'PSURatan',
    'NMC100':'NiftyMC100', 'ET100':'ETInTop100',
    'USDiv':'USStocksDiv','USTop50':'USTop50','USHolding':'USHolding',
    'HRSI':'L6yHighRSI', 'Holding':'Holding','NPharma':'NiftyPharma',
    'NBank': 'NiftyBank', 'PRecom':'RRecom'}
for i in DFile: DFile[i]=DataDir+DFile[i]+'.csv'
InFile=['N50','N100','PSU','NMC100','ET100','HRSI','NPharma','NBank','Holding','PRecom']
#InFile=['Holding']
#InFile=['NMC100']
#ListOfStocks = 'HCLTECH.NS ONGC.NS' #INFRATEL.NS
DiscStock=['OBEROIRLTY.NS'] #['GICRE.NS', 'TATASTLBSL.NS', 'HUDCO.NS' ]
DiscMinStock=['INFRATEL.NS']
#ListOfStocks = 'SUNTV.NS SUNPHARMA.NS BANDHANBNK.NS BOSCHLTD.NS BPCL.NS ICICIGI.NS INDIANB.NS'
#ListOfStocks = 'ADANIENT.NS TCS.NS BPCL.NS UPL.NS UNIONBANK.NS CIPLA.NS MARUTI.NS IBVENTURES.NS BATAINDIA.NS'
#StockCols = ['Open','High', 'Low','Close','Adj Close','olume'] #Date is index
StockCols = ['Close','Open','Low','High','Volume'] #Date is index

UpdateHistory=True
if(UpdateHistory):
#    FromDate=pd.to_datetime('2016-01-01', format='%Y-%m-%d') 
    InFile=['N50','N100','PSU','NMC100','ET100','HRSI','NPharma','NBank','Holding','PRecom']
    #'USDiv','USHolding', 'USTop50',
    ListOfStocks = ""
    History = ['NoReadRaw', 'ReadProc','WriteProc', 'Update','CreateAll'] 
    Action=['Find','NoGraph', 'History','Attrib']    
ReadHistory=True
OB = 22; OS = 78; RSIPeriod=DaysForTech=14
RSIMAPeriods = [100]; MAPeriods = [50]; IsSMA=False
RSIMAPeriod = 50
SLocMinMaxPeriod=6; LLocMinMaxPeriod = 30
RSIDiverg=['HD','RD'];  RSIDivCols = ['Date', 'RSIDiv', 'PrevRSIDiv','DivDays', 'Action']
RSIHidDivIgnLRec=True  #This will ignore the last record if forming max/min
RangeBound=True; BOutLimit = 3; BestStocks=5; CalcURGain=True
Patterns = {'RSIMAMinMax':False,'RSICDBO':True, 'RSIDiverg':True,
            'SellAtLMP': False, 'PerLevelBS': True, 'MA': True, 'RSIMA':False}
InitStockInvest = 100000 ; LimitNoOfStock = 15

DispGraph=True; RSIGraphSize=(33,5); PriceGraphSize=(33,10)
LatestGraphData=False
if(LatestGraphData):
    RSIGraphSize=(20,4); PriceGraphSize=(20,10)    
Color = {1: 'g', -1: 'r', 0 : 'b'}    
Marker = {'SD': 'x', 'SC': '+', 'MP': '.', 'HP': '>', 'LP':'<'} 
PlotFabLevel=False ; DispDiv = True
RSILineColor='grey'; CloseLineColor='grey'

RepFiles={'UnSortData':'UnSortDataInd.csv', 'DataWInd':'StockDataInd.csv', 
    'PatData':'PatData.csv', 'BestStocks':'BestStocksData.csv','Orders':'OrderData.csv',
    'InvestData':'PortFolioData.csv', 'StockAttrib':'StockAttrib.csv',
    'ToTrade':'ToTrade.csv'}  
SaveGraph=True; FirstTime=True

#updatable vars
RSI=CV=None; CalcStockAttributes=False
StockAttribCols=['Stock','StartDate','EndDate','RSI','CV']

RSILStyle={80:'--',70:'-',60:':',40:':',30:'-',20:'--'}
RSILStyle={80:'g',70:'y',60:'c',40:'c',30:'y',20:'g'}
CVLogThreshold=.35; NoOfSupNRes=3
#FromSupNRes=pd.to_datetime((ToDate+dt.timedelta(days=(-700))).date(), format='%Y-%m-%d')
FromSupNRes=ToDate - dt.timedelta(days=700)

HoldTxnFile= '../../Dash/StockPortfolio.xlsx'
class Error(Exception): pass;
class DoNothing(Error): pass ;
