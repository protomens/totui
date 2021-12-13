#!/usr/bin/env python
# encoding: utf-8
import time
import npyscreen
import requests

from requests.auth import HTTPBasicAuth
from datetime import datetime
import configparser
from time import time
import pkg_resources
import os
import shutil


BASEDIR = os.path.join(os.path.expanduser('~'), '.totui')
CONFFILE = os.path.join(BASEDIR, 'config.ini')
CONFIG = configparser.ConfigParser()

def read_configuration(confpath):
    """Read the configuration file at given path."""
    # copy our default config file
    if not os.path.isfile(confpath):
        defaultconf = pkg_resources.resource_filename(__name__, 'config.ini')
        shutil.copyfile(defaultconf, CONFFILE)

    CONFIG.read(confpath)
    return CONFIG


class TradeOgreAPI():
    apiURL = "https://tradeogre.com/api/v1"
    auth=""
    
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.auth = HTTPBasicAuth(self.key,self.secret)
        
    def get_balances(self):
        endpoint = '/account/balances'
        r = requests.get(self.apiURL + endpoint, auth=self.auth)
        return r.json()
    
    def get_ticker(self,coinl):
        coinpair = '-'.join([coinl[0], coinl[1]])
        endpoint = '/ticker/%s' % coinpair
        r = requests.get(self.apiURL + endpoint, auth=self.auth)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    
    def get_open_orders(self):
        endpoint = '/account/orders'
        r = requests.post(self.apiURL + endpoint, auth=self.auth)
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def get_order_book(self,coinl):
        coinpair = '-'.join([coinl[0], coinl[1]])
        endpoint = '/orders/%s' % coinpair
        r = requests.get(self.apiURL + endpoint, auth=self.auth)
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def get_trade_history(self, coinl):
        coinpair = '-'.join([coinl[0], coinl[1]])
        endpoint = '/history/%s' % coinpair
        r = requests.get(self.apiURL + endpoint, auth=self.auth)
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def place_buy_order(self,coinl,qty,price):
        market = '-'.join([coinl[0], coinl[1]])
        endpoint = '/order/buy'
        
        r = requests.post(self.apiURL + endpoint, data={'market': market, 'quantity': qty, 'price': price}, auth=self.auth)
        
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def place_sell_order(self,coinl,qty,price):
        market = '-'.join([coinl[0], coinl[1]])
        endpoint = '/order/sell'
        
        r = requests.post(self.apiURL + endpoint, data={'market': market, 'quantity': qty, 'price': price}, auth=self.auth)
        
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def cancel_order(self, uuid):
        endpoint = '/order/cancel'
        r = requests.post(self.apiURL + endpoint, data={'uuid' : uuid}, auth=self.auth)
        
        if r.status_code == 200:
            return r.json()
        else:
            return None

class ToTUIApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        CONFIG = read_configuration(CONFFILE)
        
        self.coin_pair = CONFIG['pair'].get('order_book','').split(',')
        self.hcoin_pair = CONFIG['pair'].get('trade_history', '').split(',')
        self.tcoin_pair = CONFIG['pair'].get('ticker', '').split(',')
        self.addForm('MAIN', MainApp, name="Tradeogre Main", color="STANDOUT")
        self.addForm("PAIR", EditPair, name="Trading Pair Books", color="IMPORTANT")
        self.addForm("HISTORY", EditHistoryPair, name="Trading Pair History", color="IMPORTANT")
        self.addForm("TICKER", EditTickerPair, name="Ticker Pair", color="IMPORTANT")
        self.addForm("BUY",  BuyPair, name="Buy Pair", color="IMPORTANT")
        self.addForm("SELL", SellPair, name="Sell Pair", color="IMPORTANT")
        self.addForm("CANCEL", CancelOrder, name="Cancel Order", color="IMPORTANT")
        self.addForm("DEPOSIT", DepositAddress, name="Add Deposit Addressr", color="IMPORTANT")

        #self.change_form("MAIN")
    def onCleanExit(self):
        npyscreen.notify_wait("Goodbye!")

    def change_form(self, name):
        # Switch forms.  NB. Do *not* call the .edit() method directly (which 
        # would lead to a memory leak and ultimately a recursion error).
        # Instead, use the method .switchForm to change forms.
        self.switchForm(name)
        
        # By default the application keeps track of every form visited.
        # There's no harm in this, but we don't need it so:        
        self.resetHistory()

class CancelOrder(npyscreen.ActionForm):
    CONFIG = read_configuration(CONFFILE)

    Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))

    def getOpenOrders(self):
        OpenOrders = self.Togre.get_open_orders()
        
        
        OrderList = []
        if OpenOrders:
            for order in OpenOrders:
                odate = datetime.fromtimestamp(order['date'])
                order_date = odate.strftime("%a, %b %d %Y")
                order_time = odate.strftime("%I:%M:%S %p")
                
                OrderList.append("{0:<10}{1:^6}{2:<10}{3:<12}{4:<12}{5:>40}".format(order_date + ' ' + order_time,
                                                               order['type'].upper(),order['market'],
                                                               order['price'],order['quantity'], order['uuid']))
            return OrderList
        else:
            return ['Bupski', 'Nada', 'None', 'Naught', 'Zilch', 'Zero', 'Nix', 'Nought', 'Nothing']
        
        
    
    def create(self):
        self.y,self.x = self.curses_pad.getmaxyx()
        self.keypress_timeout = 30  

        self.OpenOrders = self.getOpenOrders()
        self.OpenOrdersBox = self.add(npyscreen.BoxTitle, name="Open Orders", values=self.OpenOrders,
                                    max_height=14, width = self.x - 6, rely = self.y - 20,
                                    scroll_exit = True,
                                    contained_widget_arguments={
                                        'color': "CAUTION", 
                                        'widgets_inherit_color': True,}
                                    )
        self.order_num = self.add(npyscreen.TitleText, name = "Input Order Number to Cancel: ", value = None, begin_entry_at=33, use_two_lines = False)
        
    def on_ok(self):
        onum = int(self.order_num.value)
        if onum == 0 or onum > len(self.OpenOrders):
            npyscreen.notify_wait("Order numbers start from 1 and cannot be greater than the number of open orders. Please re-try.")
            self.order_num.value=None
            self.display(clear=True)
        else:
            uuid = self.OpenOrders[onum -1].split(' ')[-1].lstrip()
            JSON = self.Togre.cancel_order(uuid)
            
            if JSON:
                if JSON['success']:
                    npyscreen.notify_wait("Success! You will now return to the main screen. Your order should no longer be in the Open Orders box.")
                    self.change_forms()
                else: 
                    npyscreen.notify_wait("Uh-oh! Something went wrong: " + JSON)
                    self.order_num.value=None
                    self.display(clear=True)
            else:
                npyscreen.notify_wait("Uh-oh! Something went wrong and we don't know why. Please re-try." )
                self.order_num.value=None
                self.display(clear=True)
                
    def while_waiting(self):
        self.OpenOrdersBox.values = self.getOpenOrders()
        if not self.OpenOrdersBox.values:
            self.OpenOrdersBox.values = ['Bupkis']
        self.OpenOrdersBox.display()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
class DepositAddress(npyscreen.ActionForm):
    def create(self):
        
        self.deposit_address   = self.add(npyscreen.TitleText, name = "Coin,Address: ", value="ETH,0x", use_two_lines = False, begin_entry_at = 16)
        self.add_handlers({"^Q": self.change_forms})
        
        

    def on_ok(self):
        coin,address = self.deposit_address.value.split(',')
        CONFIG = read_configuration(CONFFILE)
        CONFIG.set('address',coin,address)
        
        FILE = open(CONFFILE,'w')
        CONFIG.write(FILE)
        
        self.change_forms()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()

class EditPair(npyscreen.ActionForm):
    def create(self):
        self.coin_pair   = self.add(npyscreen.TitleText, name = "Coin Pair:", value="BTC,XMR")
        self.add_handlers({"^Q": self.change_forms})
        
        self.parentApp.coin_pair = self.coin_pair.value.split(',')

    def on_ok(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')
        
        CONFIG = read_configuration(CONFFILE)
        CONFIG.set('pair',"order_book",self.coin_pair.value)
        
        FILE = open(CONFFILE,'w')
        CONFIG.write(FILE)
        
        self.change_forms()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
        
class EditTickerPair(npyscreen.ActionForm):
    def create(self):
        self.coin_pair   = self.add(npyscreen.TitleText, name = "Coin Pair:", value="BTC,XMR")
        self.add_handlers({"^Q": self.change_forms})
        
        self.parentApp.tcoin_pair = self.coin_pair.value.split(',')

    def on_ok(self):
        self.parentApp.tcoin_pair = self.coin_pair.value.split(',')
        
        CONFIG = read_configuration(CONFFILE)
        CONFIG.set('pair',"ticker",self.coin_pair.value)
        
        FILE = open(CONFFILE,'w')
        CONFIG.write(FILE)
        
        self.change_forms()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()

class EditHistoryPair(npyscreen.ActionForm):
    def create(self):
   
        self.hcoin_pair   = self.add(npyscreen.TitleText, name = "Coin Pair:", value="BTC,XMR")
        self.add_handlers({"^Q": self.change_forms})
        
        self.parentApp.hcoin_pair = self.hcoin_pair.value.split(',')

    def on_ok(self):
        self.parentApp.hcoin_pair = self.hcoin_pair.value.split(',')
        
        CONFIG = read_configuration(CONFFILE)
        CONFIG.set('pair',"trade_history",self.hcoin_pair.value)
        
        FILE = open(CONFFILE,'w')
        CONFIG.write(FILE)

        self.change_forms()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
  
        
class BuyPair(npyscreen.ActionForm):
    CONFIG = read_configuration(CONFFILE)

    Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))
    coin_pair=''
    amount=''
    price=''
    response = 0
    
    def getOrderBook(self,coinl):
        OrderBook = self.Togre.get_order_book(coinl)
        
        if OrderBook:
            i=0
            togre_buys = [ ]
            togre_buys_qty = [ ]
            togre_sells = [ ]
            togre_sells_qty = [ ]
            for key,key2 in zip(OrderBook['buy'].keys(), OrderBook['sell'].keys()):
                togre_buys.append(key)
                togre_buys_qty.append(OrderBook['buy'][key])
                togre_sells.append(key2)
                togre_sells_qty.append(OrderBook['sell'][key2])
                i += 1
            togre_buys.reverse()
            togre_buys_qty.reverse()
            
            OrderBookList = []
            score="_"
            OrderBookList.append("{0:^32}{1:^32}".format("Bid", "Ask"))
            OrderBookList.append("{0:^64}".format("Price"))
            OrderBookList.append(64*score)
            for bid,bamt,sell,samt in zip(togre_buys, togre_buys_qty, togre_sells, togre_sells_qty):
                OrderBookList.append("{0:<14}{1:>18}  |  {2:<14}{3:>18}".format(bamt,bid,sell,samt))
            
            return OrderBookList
        else:
            return ['Error: url request (612)']
        
        
    def create(self):
        self.keypress_timeout = 30  

        self.y,self.x = self.curses_pad.getmaxyx()

        self.add(npyscreen.TitleText, name="Press ^Q to quit and ^P to display orderbook of Pair", value=None, rely = self.y - 9 )
        self.coin_pair   = self.add(npyscreen.TitleText, name = "Coin Pair: ", value="BTC,XMR",)
        self.amount      = self.add(npyscreen.TitleText, name = "Amount:",value=None)
        self.price       = self.add(npyscreen.TitleText, name = "Price:",value=None)
        self.add_handlers({"^Q": self.change_forms})
        self.add_handlers({"^P": self.order_book})
        
        
        self.OrderBook = self.add(npyscreen.BoxTitle, name="Order Book", values = None,
                            max_height=self.y - 28, width = 70, rely = 18, relx = 36,
                            scroll_exit = True,
                            contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,}
                            )
        
        
    def on_ok(self):
        self.parentApp.coin_pair = coinl = self.coin_pair.value.split(',')
        
        if coinl and self.amount.value and self.price.value:
            response = self.Togre.place_buy_order(coinl, self.amount.value, round(float(self.price.value),8))
            
        if response['success']:
            npyscreen.notify_wait("Success! You will now return to the main screen. Your recent order should be in the bottom dialog box.")
            self.change_forms()
        else:
            npyscreen.notify_wait("Uh-oh! Something went wrong. Check your values and try again. REASON: " + response['error'] )
            self.coin_pair.value = "BTC,XMR"
            self.coin_pair.edit()
            self.amount.value = None
            self.amount.edit()
            self.price.value = None
            self.price.edit
            self.display(clear=True)
        
        self.change_forms()
        
    def order_book(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')                
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0], "-",self.parentApp.coin_pair[1]])
        self.OrderBook.display()
        
    def while_waiting(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')                
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0], "-",self.parentApp.coin_pair[1]])
        self.OrderBook.display()
           
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
        
class SellPair(npyscreen.ActionForm):
    CONFIG = read_configuration(CONFFILE)

    Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))
    coin_pair=''
    amount=''
    price=''
    response = 0
    
    def getOrderBook(self,coinl):
        OrderBook = self.Togre.get_order_book(coinl)
        
        if OrderBook:
            i=0
            togre_buys = [ ]
            togre_buys_qty = [ ]
            togre_sells = [ ]
            togre_sells_qty = [ ]
            for key,key2 in zip(OrderBook['buy'].keys(), OrderBook['sell'].keys()):
                togre_buys.append(key)
                togre_buys_qty.append(OrderBook['buy'][key])
                togre_sells.append(key2)
                togre_sells_qty.append(OrderBook['sell'][key2])
                i += 1
            togre_buys.reverse()
            togre_buys_qty.reverse()
            
            OrderBookList = []
            score="_"
            OrderBookList.append("{0:^32}{1:^32}".format("Bid", "Ask"))
            OrderBookList.append("{0:^64}".format("Price"))
            OrderBookList.append(64*score)
            for bid,bamt,sell,samt in zip(togre_buys, togre_buys_qty, togre_sells, togre_sells_qty):
                OrderBookList.append("{0:<14}{1:>18}  |  {2:<14}{3:>18}".format(bamt,bid,sell,samt))
            
            return OrderBookList
        else:
            return ['Error: url request (612)']
        
        
    def create(self):
        self.keypress_timeout = 30  

        self.y,self.x = self.curses_pad.getmaxyx()

        self.add(npyscreen.TitleText, name="Press ^Q to quit and ^P to display orderbook of Pair", value=None, rely = self.y - 9 )
        self.coin_pair   = self.add(npyscreen.TitleText, name = "Coin Pair: ", value="BTC,XMR",)
        self.amount      = self.add(npyscreen.TitleText, name = "Amount:",value=None)
        self.price       = self.add(npyscreen.TitleText, name = "Price:",value=None)
        self.add_handlers({"^Q": self.change_forms})
        self.add_handlers({"^P": self.order_book})
        
        
        self.OrderBook = self.add(npyscreen.BoxTitle, name="Order Book", values = None,
                            max_height=self.y - 28, width = 70, rely = 18, relx = 36,
                            scroll_exit = True,
                            contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,}
                            )
        
        
    def on_ok(self):
        self.parentApp.coin_pair = coinl = self.coin_pair.value.split(',')
        
        if coinl and self.amount.value and self.price.value:
            response = self.Togre.place_sell_order(coinl, self.amount.value, round(float(self.price.value),8))
            
        if response['success']:
            npyscreen.notify_wait("Success! You will now return to the main screen. Your recent order should be in the bottom dialog box.")
            self.change_forms()
        else:
            npyscreen.notify_wait("Uh-oh! Something went wrong. Check your values and try again. REASON: " + response['error'] )
            self.coin_pair.value = "BTC,XMR"
            self.coin_pair.edit()
            self.amount.value = None
            self.amount.edit()
            self.price.value = None
            self.price.edit
            self.display(clear=True)
        
        self.change_forms()
        
    def order_book(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')                
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0], "-",self.parentApp.coin_pair[1]])
        self.OrderBook.display()
        
    def while_waiting(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')                
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0], "-",self.parentApp.coin_pair[1]])
        self.OrderBook.display()
           
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
   
class MainApp(npyscreen.FormWithMenus):
    CONFIG = read_configuration(CONFFILE)

    Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))
    
    def getBalances(self):
        
        balances = self.Togre.get_balances()

        clist = []
        for coin in balances['balances'].keys():
            if balances['balances'][coin] == "0.00000000":
                continue
            clist.append("{1:<10}{0:>.8f}".format(float(balances['balances'][coin]), coin))
        return clist 
    
    def getTicker(self,coinl):
        ticker = self.Togre.get_ticker(coinl)
        
        tickerList = []
        if ticker:
            tickerList.append("Open: {:>14}".format(ticker['initialprice']))
            tickerList.append("Price: {:>13}".format(ticker['price']))
            tickerList.append("High: {:>14}".format(ticker['high']))
            tickerList.append("Low: {:>15}".format(ticker['low']))
            tickerList.append("Vol: {:>15}".format(ticker['volume']))
            tickerList.append("Bid: {:>15}".format(ticker['bid']))
            tickerList.append('Ask: {:>15}'.format(ticker['ask']))
            return tickerList
        else:
            return ["Error"]   
    
    def getOpenOrders(self):
        OpenOrders = self.Togre.get_open_orders()
        
        
        OrderList = []
        if OpenOrders:
            for order in OpenOrders:
                odate = datetime.fromtimestamp(order['date'])
                order_date = odate.strftime("%a, %b %d %Y")
                order_time = odate.strftime("%I:%M:%S %p")
                
                OrderList.append("{0:<10}{1:^6}{2:<10}{3:<12}{4:<12}{5:>40}".format(order_date + ' ' + order_time,
                                                               order['type'].upper(),order['market'],
                                                               order['price'],order['quantity'], order['uuid']))
            return OrderList
        else:
            return ['Bupski', 'Nada', 'None', 'Naught', 'Zilch', 'Zero', 'Nix', 'Nought', 'Nothing']
        
        
    def getOrderBook(self,coinl):
        
        
        OrderBook = self.Togre.get_order_book(coinl)
        
        if OrderBook:
            i=0
            togre_buys = [ ]
            togre_buys_qty = [ ]
            togre_sells = [ ]
            togre_sells_qty = [ ]
            for key,key2 in zip(OrderBook['buy'].keys(), OrderBook['sell'].keys()):
                togre_buys.append(key)
                togre_buys_qty.append(OrderBook['buy'][key])
                togre_sells.append(key2)
                togre_sells_qty.append(OrderBook['sell'][key2])
                i += 1
            togre_buys.reverse()
            togre_buys_qty.reverse()
            
            OrderBookList = []
            score="_"
            OrderBookList.append("{0:^32}{1:^32}".format("Bid", "Ask"))
            OrderBookList.append("{0:^64}".format("Price"))
            OrderBookList.append(64*score)
            for bid,bamt,sell,samt in zip(togre_buys, togre_buys_qty, togre_sells, togre_sells_qty):
                OrderBookList.append("{0:<14}{1:>18}  |  {2:<14}{3:>18}".format(bamt,bid,sell,samt))
            
            return OrderBookList
        else:
            return ['Error: url request (612)']
        
    def getTradePairHistory(self,coinl):
        
        TradePairHistory = self.Togre.get_trade_history(coinl)
        TradePairHistory.reverse()
        TradePairList = [] 
        if TradePairHistory:
            for trade in TradePairHistory:
                odate = datetime.fromtimestamp(trade['date'])
                otime = odate.strftime("%I:%M:%S %p")
                if trade['type'] == "buy":
                    otype = "B"
                else:
                    otype = "S"
                price = trade['price']
                qty = trade['quantity']
                TradePairList.append("{:<10}{:^5}{:^13}{:>14}".format(otime,otype,price,qty))
        return TradePairList
    
    def getDepositAddresses(self):
        daddress = []
        coins = CONFIG.options("address")
        for c in coins:
            address = CONFIG['address'].get(c, '')
            if address:
                daddress.append(c.upper() + ": " + address)
        return daddress
    
    def getCoinPair(self):
        return CONFIG['pair'].get('order_book','').split(','), CONFIG['pair'].get('trade_history','').split(','),CONFIG['pair'].get('ticker','').split(',')
    
    def create(self):
        self.y,self.x = self.curses_pad.getmaxyx()
        self.keypress_timeout = 70 
        #self.form = npyscreen.FormWithMenus(name = "Welcome to Npyscreen",)
        #t = F.add(npyscreen.BoxBasic, name = "Basic Box:", max_width=50, relx=2, max_height=3)
        #t.footer = "This is a footer"
        
        self.timeWidget = self.add(npyscreen.Textfield, name=" ",
                                    value=self.getTimeDate(),
                                    editable = None, 
                                    relx = int((self.x - len(self.getTimeDate().split('\n')[-1])-7) / 2))
        
        #self.getBalances()
            
        #myGrid = F.add(npyscreen.SimpleGrid,columns=2,column_width=10,values=coins)
        #self.add_handlers({"^O": self.cancel_order})

        with open('logo.uni', 'r') as logo:
            data = logo.readlines()
        
        linlen=len(data[2])
        self.logo = self.add(npyscreen.BoxTitle, values=data, rely=4, relx= int((self.x - linlen) / 2),
               max_width=linlen+7,max_height=len(data)+2)
        self.logo.editable = False 
        #t1.values = [("BTC", 0.0321), "KDA: 4.20918", "MWC: 9.8376", "USDT: 2384.340", "ARRR: 10.2"]
        #t1.add(npyscreen.SimpleGrid,columns=2,column_width=10,values=coins)
        
        self.OpenOrders = self.add(npyscreen.BoxTitle, name="Open Orders", values=None,
                                    max_height=6, width = self.x - 6, rely = self.y - 8,
                                    scroll_exit = True, editable = True,
                                    contained_widget_arguments={
                                        'color': "CAUTION", 
                                        'widgets_inherit_color': False,}
                                    )
        
        clist = []
        self.holdingCell = self.add(npyscreen.BoxTitle, name="Holdings", values = clist, rely=12, relx=5, 
                        max_width=30, max_height=15,scroll_exit = True,
                        contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,})
        
        
        self.availBTC = self.add(npyscreen.TitleText, name="Available BTC:", value=None, relyy = 29, relx=5, begin_entry_at = 16, use_two_lines = False)
        self.pendingBTC = self.add(npyscreen.TitleText, name="Pending BTC:", value=None, relyy = 30, relx=5, begin_entry_at = 16, use_two_lines = False)
        
        self.tickerCell = self.add(npyscreen.BoxTitle, name="Ticker", values = None, rely=31, relx=5, 
                        max_width=30, max_height=10,scroll_exit = True,
                        contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,})
        
        
        self.OrderBook = self.add(npyscreen.BoxTitle, name="Order Book", values = None,
                                    max_height=self.y - 28, width = 70, rely = 12, relx = 36,
                                    scroll_exit = True,
                                    contained_widget_arguments={
                                        'color': "WARNING", 
                                        'widgets_inherit_color': True,}
                                    )
        
        self.TradeHistory = self.add(npyscreen.BoxTitle, name="Trade History", values = None,
                                    max_height=self.y - 28, width = 50, rely = 12, relx = 108,
                                    scroll_exit = True,
                                    contained_widget_arguments={
                                        'color': "WARNING", 
                                        'widgets_inherit_color': True,}
                                    )
        
        daddress = self.getDepositAddresses()
        
        self.DepositAddress = self.add(npyscreen.BoxTitle, name="Deposit Addresses",
                                    max_height=6, width = self.x - 6, rely = self.y - 14, 
                                    scroll_exit = True,
                                    values = daddress,
                                    contained_widget_arguments={
                                        'color': "WARNING", 
                                        'widgets_inherit_color': True,}
                                    )
     
        '''
        t3 = F.add(npyscreen.BoxTitle, name="Box Title2:", max_height=6,
                        scroll_exit = True,
                        contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,}
                        )
        
        
        t2.entry_widget.scroll_exit = True
        t2.values = ["Hello", 
            "This is a Test", 
            "This is another test", 
            "And here is another line",
            "And here is another line, which is really very long.  abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz",
            "And one more."]
        t3.values = t2.values
        '''
        
        
        #self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE]  = self.exit_application    
        '''
        menu_options = [
           ("1.) Order Book Pair",self.change_forms,"P",(None,form="PAIR"), None),
           ("2.) Deposit", self.deposit, "D"),
           ("3.) Place Buy Order", self.placeBuyOrder, "B"),
           ("4.) Place Sell Order", self.placeSellOrder, "S"),
        ]
        '''
        self.m1 = self.add_menu(name="Main Menu", shortcut="^M")
        #self.m1.addItemsFromList(menu_options)
        self.m1.addItem(text="1.) Order Book Pair",onSelect=self.change_form_pair,shortcut="P")
        self.m1.addItem(text="2.) Place Buy Order",onSelect=self.change_form_buy,shortcut="B")
        self.m1.addItem(text="3.) Place Sell Order",onSelect=self.change_form_sell,shortcut="S")
        self.m1.addItem(text="4.) Cancel Order",onSelect=self.change_form_cancel,shortcut="C")
        self.m1.addItem(text="5.) Trade History Pair",onSelect=self.change_form_history,shortcut="H")
        self.m1.addItem(text="6.) Add Deposit Address",onSelect=self.change_form_deposit,shortcut="D")
        self.m1.addItem(text="7.) Ticker Pair",onSelect=self.change_form_ticker,shortcut="D")
        '''
        self.m2 = self.add_menu(name="Another Menu", shortcut="b",)
        self.m2.addItemsFromList([
            ("Just Beep",   self.whenJustBeep),
        ])
        
        self.m3 = self.m2.addNewSubmenu("A sub menu", "^F")
        self.m3.addItemsFromList([
            ("Just Beep",   self.whenJustBeep),
        ])
        '''
        self.display()
        
    def calculate_available_btc(self,clist, OpenOrders):
        order_type = []
        btc_price = []
        btc_pair_qty = []


        for c in clist: 
            coin = c.split(' ')[0]
            if coin == "BTC":
                btc = c.split('       ')[-1]

                
        for s in OpenOrders:
            order_type.append(s.split(' ')[6])
            btc_price.append(s.split(' ')[10])
            btc_pair_qty.append(s.split(' ')[12])
        
        running_btc = 0.0
        pending_btc = 0.0
        for otype,price,qty in zip(order_type,btc_price,btc_pair_qty):
            #print(otype)
            if otype == "BUY":
                #print("%s, %s, %s" % (otype, price,qty))
                running_btc += float(price)*float(qty)
        
            else:
                pending_btc += float(price)*float(qty)
        available_btc = float(btc) - running_btc
        return round(available_btc,8),round(pending_btc,8)
                
    def while_waiting(self):
        self.parentApp.coin_pair, self.parentApp.hcoin_pair, self.parentApp.tcoin_pair = self.getCoinPair()

        self.holdingCell.values = self.getBalances()
        self.holdingCell.display()
        
        self.tickerCell.values = self.getTicker(self.parentApp.tcoin_pair)
        self.tickerCell.name = "".join(["Ticker: ", self.parentApp.tcoin_pair[0], "-", self.parentApp.tcoin_pair[1]])
        self.tickerCell.display()
        
        self.timeWidget.value = self.getTimeDate()
        self.timeWidget.display()
        
        self.OpenOrders.values = self.getOpenOrders()
        if not self.OpenOrders:
            self.OpenOrders.values = ['Bupkis']
        self.OpenOrders.display()
        
        abtc, pbtc = self.calculate_available_btc(self.holdingCell.values, self.OpenOrders.values)
        self.availBTC.value = '{:f}'.format(abtc)
        self.pendingBTC.value = '{:f}'.format(pbtc)
        
        
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0], "-",self.parentApp.coin_pair[1]])
        self.OrderBook.display()
        
        self.TradeHistory.values = self.getTradePairHistory(self.parentApp.hcoin_pair)
        self.TradeHistory.name = "".join(['Trade History:  ',self.parentApp.hcoin_pair[0], "-",self.parentApp.hcoin_pair[1]])
        self.TradeHistory.display()
        
        self.DepositAddress.values = self.getDepositAddresses()
        
        self.display(clear=True)
        
            
    def getTimeDate(self):
        epoch_time = time()
        now = datetime.fromtimestamp(int(epoch_time))
        now_date = now.strftime("%a, %b %d %Y")
        now_time = now.strftime("%I:%M:%S %p")
        
        return now_date + '\n' +  now_time          
    
    def change_form_pair(self, *args, **keywords):
        change_to = "PAIR"
        
        self.parentApp.change_form(change_to)
    
    def change_form_history(self, *args, **keywords):
        change_to = "HISTORY"
        
        self.parentApp.change_form(change_to)
          
    def change_form_buy(self, *args, **keywords):
        change_to = "BUY"
        
        self.parentApp.change_form(change_to)
        
    def change_form_sell(self, *args, **keywords):
        change_to = "SELL"
        
        self.parentApp.change_form(change_to)
    
    
    def change_form_cancel(self, *args, **keywords):
        change_to = "CANCEL"
        
        self.parentApp.change_form(change_to)
        
    def change_form_deposit(self, *args, **keywords):
        change_to = "DEPOSIT"
        
        self.parentApp.change_form(change_to)
        
    def change_form_ticker(self, *args, **keywords):
        change_to = "TICKER"
        
        self.parentApp.change_form(change_to)

def main():
    global CONFIG
    CONFIG = read_configuration(CONFFILE)
    
    App = ToTUIApplication()
    App.run() 
    
if __name__ == '__main__':
    main()
  
