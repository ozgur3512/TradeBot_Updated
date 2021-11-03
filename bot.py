import os,pprint,talib,config,websocket,json,numpy,math
import pandas as pd
from binance.client import Client
from binance.enums import *
stream="wss://stream.binance.com:9443/ws/ethusdt@kline_30m"
api_key="ENTER YOUR API KEY"
secret_key="ENTER YOUR SECRET KEY"
client=Client(api_key,secret_key)

closesKline=[]
lowsKline=[]
highsKline=[]
#Getting Historical klines from 1 day ago
klines = client.get_historical_klines("ETHUSDT", Client.KLINE_INTERVAL_30MINUTE, "1 week ago GMT")
x=0
for i in klines:
    if(len(klines)-1!=x):
        closesKline.append(float(i[4]))
        lowsKline.append(float(i[3]))
        highsKline.append(float(i[2]))
    x+=1




RSI_PERIOD=14
LEVERAGE=20
TRADE_SYMBOL="ETHUSDT"
TRADE_QUAN=0.03
in_position=False
client.futures_change_leverage(symbol=TRADE_SYMBOL, leverage=LEVERAGE)

#External Functions Beginning

def GetOrderNum():
    x=0
    a=client.futures_get_all_orders(symbol="ETHUSDT")
    for i in a:
        if(i['status']=="NEW" or i['status']=="ACTIVE"):
            x+=1
    return x


def generateSupertrend(close_array, high_array, low_array, atr_period, atr_multiplier):
    close_array=numpy.array(close_array)
    high_array=numpy.array(high_array)
    low_array=numpy.array(low_array)
    
    atr = talib.ATR(high_array, low_array, close_array, atr_period)
    

    previous_final_upperband = 0
    previous_final_lowerband = 0
    final_upperband = 0
    final_lowerband = 0
    previous_close = 0
    previous_supertrend = 0
    supertrend = []
    supertrendc = 0

    for i in range(0, len(close_array)):
        if numpy.isnan(close_array[i]):
            pass
        else:
            highc = high_array[i]
            lowc = low_array[i]
            atrc = atr[i]
            closec = close_array[i]

            if math.isnan(atrc):
                atrc = 0

            basic_upperband = (highc + lowc) / 2 + atr_multiplier * atrc
            basic_lowerband = (highc + lowc) / 2 - atr_multiplier * atrc

            if basic_upperband < previous_final_upperband or previous_close > previous_final_upperband:
                final_upperband = basic_upperband
            else:
                final_upperband = previous_final_upperband

            if basic_lowerband > previous_final_lowerband or previous_close < previous_final_lowerband:
                final_lowerband = basic_lowerband
            else:
                final_lowerband = previous_final_lowerband

            if previous_supertrend == previous_final_upperband and closec <= final_upperband:
                supertrendc = final_upperband
            else:
                if previous_supertrend == previous_final_upperband and closec >= final_upperband:
                    supertrendc = final_lowerband
                else:
                    if previous_supertrend == previous_final_lowerband and closec >= final_lowerband:
                        supertrendc = final_lowerband
                    elif previous_supertrend == previous_final_lowerband and closec <= final_lowerband:
                        supertrendc = final_upperband

            supertrend.append(supertrendc)

            previous_close = closec

            previous_final_upperband = final_upperband

            previous_final_lowerband = final_lowerband

            previous_supertrend = supertrendc

    return supertrend


#External Functions Ending



def order(side,quantity,symbole,price):
    try:
        print("sending order")
        client.futures_create_order(
            symbol=symbole,
            type='LIMIT',
            timeInForce='GTC',  # Can be changed - see link to API doc below
            price=price+2,  # The price at which you wish to buy/sell, float
            side=side,  # Direction ('BUY' / 'SELL'), string
            quantity=quantity  # Number of coins you wish to buy / sell, float
        )
        client.futures_create_order(
            symbol=symbole,
            type='STOP_MARKET',
            side='SELL',
            stopPrice=price-29,
            closePosition=True
            )
        client.futures_create_order(
            symbol='ETHUSDT',
            type='TAKE_PROFIT_MARKET',
            side='SELL',
            stopPrice=price+40,
            closePosition=True
            )
    except:
        print("Order Failed")
        return False
    return True
def Shortorder(side,quantity,symbole,price):
    try:
        print("sending order")
        client.futures_create_order(
            symbol=symbole,
            type='LIMIT',
            timeInForce='GTC',  # Can be changed - see link to API doc below
            price=price,  # The price at which you wish to buy/sell, float
            side=side,  # Direction ('BUY' / 'SELL'), string
            quantity=quantity  # Number of coins you wish to buy / sell, float
        )
        client.futures_create_order(
            symbol=symbole,
            type='STOP_MARKET',
            side='BUY',
            stopPrice=price+61,
            closePosition=True
            )
        client.futures_create_order(
            symbol='ETHUSDT',
            type='TAKE_PROFIT_MARKET',
            side='BUY',
            stopPrice=price-73,
            closePosition=True
            )
    except:
        print("Order Failed")
        return False
    return True
def on_opened(ws):
    print("connected")


def on_closed(ws):
    print("connection closed")


def on_messaged(ws,message):
    global in_position
    global closesKline
    print("recieved message")
    new_mess=json.loads(message)
    
    candle=new_mess['k']
    
    candle_close=candle['x']
    close=candle['c']
    high=candle['h']
    low=candle['l']
    
    if candle_close:
        print("Candle Close at {}".format(float(close)))
        closesKline.append(float(close))
        lowsKline.append(float(low))
        highsKline.append(float(high))
       
        
        if(len(closesKline)>31):
            numpy_closes=numpy.array(closesKline)
           

            #STOCHRSI CALCULATION
            rsi = talib.RSI(numpy_closes,RSI_PERIOD)

            rsi_nan = rsi[numpy.logical_not(numpy.isnan(rsi))]

            stochrsif, stochrsis = talib.STOCH(rsi_nan, rsi_nan, rsi_nan, fastk_period=14, slowk_period=3, slowd_period=3)
            
            #EMA CALCULATION

            ema=talib.EMA(numpy_closes,timeperiod=200)
            print(ema[-1])

            #supertrend calculation
            son_kapanis = closesKline[-1]
            
            supertrend=generateSupertrend(closesKline,highsKline,lowsKline,atr_period=10, atr_multiplier=3)
            son_supertrend_deger = supertrend[-1]
            
            print(in_position)
            if(closesKline[-1]>ema[-1]):
                print("EMA Geçildi")
            # renk yeşile dönüyor, trend yükselişe geçti
            if son_kapanis > son_supertrend_deger :
                print('al sinyali')

            # renk kırmızıya dönüyor, trend düşüşe geçti
            if son_kapanis < son_supertrend_deger :
                    print('sat sinyali')

            if(48<=float(stochrsif[-1])+float(stochrsis[-1])<=68):
                print("StochRSI Long Sağlandı.")
                
            else:
                print("StochRSI Sağlanamadı.{}".format(float(stochrsif[-1])+float(stochrsis[-1])))    
           
            
        
            if(closesKline[-1]>ema[-1] and (son_kapanis > son_supertrend_deger) and (40<=float(stochrsif[-1])+float(stochrsis[-1])<=72) and (float(stochrsis[-1]>float(stochrsis[-2]) and float(stochrsis[-2]) > float(stochrsis[-3])))  ):
                if(not in_position):
                    order_succed=order(SIDE_BUY,TRADE_QUAN,TRADE_SYMBOL,closesKline[-1])
                    if(order_succed):
                        print("We entered a long position")
                        in_position=True
                else:
                    print("We are already in long position")

            if(closesKline[-1]<ema[-1] and (son_kapanis < son_supertrend_deger) and (120<=float(stochrsif[-1])+float(stochrsis[-1])<=145) and (float(stochrsis[-1]<float(stochrsis[-2]) and float(stochrsis[-2]) < float(stochrsis[-3])))  ):
                if(not in_position):
                    order_succed=Shortorder(SIDE_SELL,TRADE_QUAN,TRADE_SYMBOL,closesKline[-1])
                    if(order_succed):
                        print("We entered a short position")
                        in_position=True
                else:
                    print("We are already in short position") 

            if(in_position):
                if(GetOrderNum()==0 or GetOrderNum()==1):
                    in_position=False
                    if(GetOrderNum()==1):
                        client.futures_cancel_all_open_orders(symbol="ETHUSDT",timeInForce='GTC')
            


    
ws=websocket.WebSocketApp(stream,on_close=on_closed,on_open=on_opened,on_message=on_messaged)
ws.run_forever()
