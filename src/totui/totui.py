#!/usr/bin/env python
# encoding: utf-8
import time
import npyscreen
import re
import decimal

from datetime import datetime
import configparser
from time import time
import pkg_resources
import os
import shutil
from curses import KEY_F5


from totui_selenium.totui_selenium import SeleniumTradeOgre
from tradeogre_api.tradeogre_api import TradeOgreAPI

BASEDIR = os.path.join(os.path.expanduser('~'), '.totui')
CONFFILE = os.path.join(BASEDIR, 'config.ini')
COINSFILE = os.path.join(BASEDIR, 'coins.list')
LOGOFILE = os.path.join(BASEDIR, 'logo.uni')
CONFIG = configparser.ConfigParser()
TOTUIVERSION = "TOTUI v1.7.7"

def read_configuration(confpath):
    """Read the configuration file at given path."""
    # copy our default config file
    
    if os.path.isdir(BASEDIR):
        if not os.path.isfile(confpath):
            defaultconf = pkg_resources.resource_filename(__name__, 'config.ini')
            defaultcoins = pkg_resources.resource_filename(__name__, 'coins.list')
            defaultlogo = pkg_resources.resource_filename(__name__, 'logo.uni')
            shutil.copyfile(defaultconf, CONFFILE)
            shutil.copyfile(defaultcoins, COINSFILE)
            shutil.copyfile(defaultlogo, LOGOFILE)

    else:
        os.mkdir(BASEDIR)
        defaultconf = pkg_resources.resource_filename(__name__, 'config.ini')
        defaultcoins = pkg_resources.resource_filename(__name__, 'coins.list')
        defaultlogo = pkg_resources.resource_filename(__name__, 'logo.uni')
        shutil.copyfile(defaultconf, CONFFILE)
        shutil.copyfile(defaultcoins, COINSFILE)
        shutil.copyfile(defaultlogo, LOGOFILE)
        
    CONFIG.read(confpath)
    return CONFIG

class BoxTitle(npyscreen.BoxTitle):
    _contained_widget = npyscreen.SelectOne


class ToTUIApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        global CONFIG
        
        self.coin_pair = CONFIG['pair'].get('order_book','').split(',')
        self.hcoin_pair = CONFIG['pair'].get('trade_history', '').split(',')
        self.tcoin_pair = CONFIG['pair'].get('ticker', '').split(',')
        self.addForm('MAIN', MainApp, name=TOTUIVERSION, color="STANDOUT")
        self.addForm("PAIR", EditPair, name="Trading Pair Books", color="IMPORTANT")
        self.addForm("HISTORY", EditHistoryPair, name="Trading Pair History", color="IMPORTANT")
        self.addForm("TICKER", EditTickerPair, name="Ticker Pair", color="IMPORTANT")
        self.addForm("BUY",  BuyPair, name="Buy Pair", color="IMPORTANT")
        self.addForm("SELL", SellPair, name="Sell Pair", color="IMPORTANT")
        self.addForm("CANCEL", CancelOrder, name="Cancel Order", color="IMPORTANT")
        self.addForm("DEPOSIT", GetCoinDepositAddress, name="Add Deposit Address", color="IMPORTANT")
        self.addForm("WITHDRAW", WithdrawCoin, name="Withdraw", color="IMPORTANT")
        self.addForm("DHISTORY", GetDepositHistory, name="Deposit History", color="IMPORTANT")
        self.addForm("WHISTORY", GetWithdrawHistory, name="Withdraw History", color="IMPORTANT")
        self.addForm("THISTORY", GetTradeHistory, name="Trades History", color="IMPORTANT")

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

class WithdrawCoin(npyscreen.ActionForm):
    coin = ''
    amount = ''
    address = ''
    two_factor_authentication = ''
    Togre = None
    prevCoin = ''
    balances = []
    
    def getBalances(self):
        
        balances = self.Togre.get_balances()

        clist = []
        if balances:
            for coin in balances['balances'].keys():
                if balances['balances'][coin] == "0.00000000":
                    continue
                clist.append("{1:<10}{0:>.8f}".format(float(balances['balances'][coin]), coin))
            return clist
        return None 

    def create(self):
        global TS
        global CONFIG

        self.y,self.x = self.curses_pad.getmaxyx()

        self.keypress_timeout = 15  

        
        self.Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))

        self.balances = self.getBalances()
        
        self.CoinBalances = self.add(BoxTitle, name="Available Coin Balances", values = self.balances,
                            max_height=self.y - 40, width = 38, rely = 5, relx = 36,
                            scroll_exit = True,
                            contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,}
                            )
        self.add(npyscreen.FixedText, name="Please fill in values shown below. Be sure to check the status of the wallet below and ensure it is Online",
                                      value="Please fill in values shown below. Be sure to check the status of the wallet below and ensure it is Online", rely = self.y - 35  )

        self.coin     = self.add(npyscreen.TitleText, name = "Coin: ", value=None, use_two_lines = False, begin_entry_at = 18, rely = self.y - 34)
        self.amount   = self.add(npyscreen.TitleText, name = "Amount: ", value=None, use_two_lines = False, begin_entry_at = 18, rely = self.y - 33)
        self.address  = self.add(npyscreen.TitleText, name = "Withdraw Address: ", value=None, use_two_lines = False, begin_entry_at = 18, rely = self.y - 32)
        self.two_factor_authentication = self.add(npyscreen.TitleText, name = "2FA: ", value=None, use_two_lines = False, begin_entry_at = 18, rely = self.y - 31)
        self.wallet_status = self.add(npyscreen.FixedText, name="Wallet:", value="Wallet: ", use_two_lines=False, begin_entry_at = 10, rely = self.y - 28 )

        
    def on_ok(self):
        global TS
        global CONFIG
        
        retvalue = TS.tradeogre_withdraw(self.coin.value, self.amount.value, self.address.value)
        
        totp_return = TS.tradeogre_totp(self.two_factor_authentication.value)
        
        if retvalue['success'] and totp_return['success']:
            npyscreen.notify_wait("Success!\n %s %s\n has been deposited to:\n %s" % (self.amount.value, self.coin.value, self.address.value))
        else:
            npyscreen.notify_wait("ERROR.\n" + retvalue['message'] + '\n' + totp_return['message'])
    

        self.change_forms()
        
    def while_waiting(self):
        global TS
        
        self.CoinBalances.values = self.getBalances()
        self.CoinBalances.display()
        
        if self.coin.value:
            if self.prevCoin != self.coin.value:
                self.wallet_status.value = "Wallet (%s): Checking..." % self.coin.value
                self.wallet_status.display()
                wStatus = TS.tradeogre_getWallet_status(self.coin.value)
                self.wallet_status.value = "Wallet (%s): %s " % (self.coin.value,  wStatus)
                self.wallet_status.display()
                self.prevCoin = self.coin.value  
        try:
            if self.CoinBalances.value[0] >= 0:
                self.coin.value, self.amount.value = re.split(' +',self.balances[self.CoinBalances.value[0]])
                self.coin.display()
                self.amount.display()
        except IndexError:
            pass
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
        

class GetCoinDepositAddress(npyscreen.ActionForm):
    coin = ''
    
    def create(self):
        global TS
        self.y,self.x = self.curses_pad.getmaxyx()
        self.keypress_timeout = 15  

        self.CoinList = self.add(BoxTitle, name="Available Coin List", values = TS.coins,
                            max_height=self.y - 28, width = 25, rely = 18, relx = 36,
                            scroll_exit = True,
                            contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,}
                            )
        
        

        
        self.coin   = self.add(npyscreen.TitleText, name = "Coin: ", value="", use_two_lines = False, begin_entry_at = 7)
    
    def while_waiting(self):
        try:
            if self.CoinList.value[0] >= 0:
                self.coin.value = TS.coins[self.CoinList.value[0]]
                self.coin.display()
            
        except IndexError:
            pass
    def on_ok(self):
        global TS
        global CONFIG
        
        address = TS.tradeogre_getDeposit_address(self.coin.value)
        
        CONFIG.set('address',self.coin.value.lower(),address)
        
        FILE = open(CONFFILE,'w')
        CONFIG.write(FILE)
        
        self.change_forms()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
        
class GetDepositHistory(npyscreen.ActionForm):
    
    def create(self):
        global TS

        self.y,self.x = self.curses_pad.getmaxyx()
        self.add_handlers({KEY_F5: self.keyrefresh})
        
        #TS.tradeogre_getDeposit_history()
        self.DepositList = self.add(npyscreen.BoxTitle, name="Deposit History", values = None,
                            max_height=self.y - 28, width = 150, rely = 5, relx = 10,
                            scroll_exit = True,
                            contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,}
                            )
        
        

        
        self.coin   = self.add(npyscreen.FixedText, name = "Press F5 to refresh", value="Press F5 to refresh", use_two_lines = False)
        
    def keyrefresh(self, *args, **keywords):
        global TS
        self.DepositList.values = TS.tradeogre_getDeposit_history()
        self.DepositList.display()
        
    def on_ok(self):
        
        self.change_forms()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
            
            
class GetWithdrawHistory(npyscreen.ActionForm):
    
    def create(self):
        global TS

        self.y,self.x = self.curses_pad.getmaxyx()
        self.add_handlers({KEY_F5: self.keyrefresh})
        
        #TS.tradeogre_getDeposit_history()
        self.WithdrawList = self.add(npyscreen.BoxTitle, name="Withdraw History", values = None,
                            max_height=self.y - 28, width = 150, rely = 5, relx = 10,
                            scroll_exit = True,
                            contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,}
                            )
        
        

        
        self.coin   = self.add(npyscreen.FixedText, name = "Press F5 to refresh", value="Press F5 to refresh", use_two_lines = False)
        
    def keyrefresh(self, *args, **keywords):
        global TS
        self.WithdrawList.values = TS.tradeogre_getWithdraw_history()
        self.WithdrawList.display()
        
    def on_ok(self):
        
        self.change_forms()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()

class GetTradeHistory(npyscreen.ActionForm):
    
    def create(self):

        self.y,self.x = self.curses_pad.getmaxyx()
        self.add_handlers({KEY_F5: self.keyrefresh})
        
        #TS.tradeogre_getDeposit_history()
        self.TradeList = self.add(npyscreen.BoxTitle, name="Trades History", values = None,
                            max_height=self.y - 28, width = 150, rely = 5, relx = 10,
                            scroll_exit = True,
                            contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,}
                            )
        
        

        
        self.coin   = self.add(npyscreen.FixedText, name = "Press F5 to refresh", value="Press F5 to refresh", use_two_lines = False)
        
    def keyrefresh(self, *args, **keywords):
        global TS
        self.TradeList.values = TS.tradeogre_getTrade_history()
        self.TradeList.display()
        
    def on_ok(self):
        
        self.change_forms()
        
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
        global CONFIG
        
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
        global CONFIG
        
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
           
        global CONFIG
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
        
        global CONFIG
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
    
    #global CONFIG
    coin_pair=''
    amount=''
    price=''
    response = 0
    Togre = None

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
        global CONFIG
        self.Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))

        self.keypress_timeout = 30  

        self.y,self.x = self.curses_pad.getmaxyx()

        self.add(npyscreen.TitleText, name="Press ^Q to quit and type in your order pair to display Order Book. i.e, BTC,XHV", value=None, rely = self.y - 9 )
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
        self.order_book()
        
        
    def on_ok(self):
        self.parentApp.coin_pair = coinl = self.coin_pair.value.split(',')
        decimal.getcontext().prec = 8
        if coinl and self.amount.value and self.price.value:
            response = self.Togre.place_buy_order(coinl, self.amount.value, str(decimal.Decimal(self.price.value)))
            
        if response['success']:
            npyscreen.notify_wait("Success! You will now return to the main screen. Your recent order should be in the bottom dialog box.")
            self.change_forms()
        else:
            npyscreen.notify_wait("Uh-oh! Something went wrong. Check your values and try again. REASON: " + response['error'] + "  VALUE: %s" % str(decimal.Decimal(self.price.value) ))
            self.coin_pair.value = "BTC,XMR"
            self.amount.value = None
            self.price.value = None
            self.display(clear=True)
        
        self.change_forms()
        
    def order_book(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')                
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0].upper(), "-",self.parentApp.coin_pair[1].upper()])
        self.OrderBook.display()
        
    def while_waiting(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')                
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0].upper(), "-",self.parentApp.coin_pair[1].upper()])
        self.OrderBook.display()
           
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
        
class SellPair(npyscreen.ActionForm):
    coin_pair=''
    amount=''
    price=''
    response = 0
    Togre = None
    
    def getBalances(self):
        
        balances = self.Togre.get_balances()

        clist = []
        if balances:
            for coin in balances['balances'].keys():
                if balances['balances'][coin] == "0.00000000":
                    continue
                clist.append("{1:<10}{0:>.8f}".format(float(balances['balances'][coin]), coin))
            return clist
        return None 
      
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
        clist = []
        global CONFIG
        
        self.Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))

        self.keypress_timeout = 15  

        self.y,self.x = self.curses_pad.getmaxyx()

        self.help = self.add(npyscreen.FixedText, value="Press ^Q to quit and type in order pair to display Order Book i.e. BTC,XHV", rely = self.y - 15 )
        self.help2 = self.add(npyscreen.FixedText, value="Select a coin from the list and press 'S', to sell the coin. Adjust coin pair, amount, and price appropriately.")
        self.help.editable = False
        self.help2.editable = False
        
        self.coin_pair   = self.add(npyscreen.TitleText, name = "Coin Pair: ", value="BTC,XMR", rely = self.y - 12)
        self.amount      = self.add(npyscreen.TitleText, name = "Amount:",value=None, rely = self.y - 11)
        self.price       = self.add(npyscreen.TitleText, name = "Price:",value=None, rely = self.y - 10)
        
        self.add_handlers({"^Q": self.change_forms})
        self.add_handlers({"^P": self.order_book})
        self.add_handlers({"S": self.load_order})
        
        
        self.OrderBook = self.add(npyscreen.BoxTitle, name="Order Book", values = None,
                            max_height=self.y - 34, width = 70, rely = 8, relx = 36,
                            scroll_exit = True,
                            contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,})

        self.holdingCell = self.add(BoxTitle, name="Holdings", values = clist, rely=self.y - 48, relx=116, 
                        max_width=30, max_height=15,scroll_exit = True,
                        contained_widget_arguments={
                                'color': "WARNING", 
                                'widgets_inherit_color': True,})
                            
        self.order_book()
        
    def on_ok(self):
        self.parentApp.coin_pair = coinl = self.coin_pair.value.split(',')
        decimal.getcontext().prec = 8

        if coinl and self.amount.value and self.price.value:
            response = self.Togre.place_sell_order(coinl, self.amount.value, str(decimal.Decimal(self.price.value)))
            
        if response['success']:
            npyscreen.notify_wait("Success! You will now return to the main screen. Your recent order should be in the bottom dialog box.")
            self.change_forms()
        else:
            npyscreen.notify_wait("Uh-oh! Something went wrong. Check your values and try again. REASON: " + response['error'] )
            self.coin_pair.value = "BTC,XMR"
            self.amount.value = None
            self.price.value = None
            self.display(clear=True)
        
        self.change_forms()
        
    def load_order(self, *args, **keywords):
        try:
            if self.holdingCell.value[0] >= 0: 
                sell_coin, self.amount.value = re.split(' +', self.holdingCell.values[self.holdingCell.value[0]])
                cpair = "BTC," + sell_coin
                self.coin_pair.value = cpair
                self.coin_pair.display()
                self.amount.display()
        except IndexError:
            pass
        
    def order_book(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')                
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0].upper(), "-",self.parentApp.coin_pair[1].upper()])
        self.OrderBook.display()
        
    def while_waiting(self):
        self.parentApp.coin_pair = self.coin_pair.value.split(',')                
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0].upper(), "-",self.parentApp.coin_pair[1].upper()])
        self.OrderBook.display()
        
        self.holdingCell.values = self.getBalances()
        self.holdingCell.display()
           
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
        
class CancelOrder(npyscreen.ActionForm):
    Togre = None
    OpenOrders = None
      
    def getOpenOrders(self):
        global TS
        TS.clear_OpenOrders()
        TS.get_tradeogre_orders()
        
        OrdersList = TS.format_open_orders()
        
        return OrdersList
        

    def create(self):
        global CONFIG
        self.Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))
        self.keypress_timeout = 30 

        self.y,self.x = self.curses_pad.getmaxyx()
        #self.keypress_timeout = 30  

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
        if onum == 0 or onum > len(self.OpenOrders) or not isinstance(onum,int):
            npyscreen.notify_wait("Order numbers start from 1 and cannot be greater than the number of open orders and must be an integer. Please re-try.")
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
                    npyscreen.notify_wait("Uh-oh! Something went wrong.")
                    self.order_num.value=None
                    self.display(clear=True)
            else:
                npyscreen.notify_wait("Uh-oh! Something went wrong and we don't know why. Please re-try." )
                self.order_num.value=None
                self.display(clear=True)
                
    def while_waiting(self):
        self.OpenOrders = self.getOpenOrders()
        self.OpenOrdersBox.values = self.OpenOrders
        self.OpenOrdersBox.display()
        
    def change_forms(self, *args, **keywords):    
        change_to = "MAIN"
            
        self.parentApp.change_form(change_to)
        
    def on_cancel(self):
        self.change_forms()
        
        
class MainApp(npyscreen.FormWithMenus):
    Togre = None
    
    def getBalances(self):
        
        balances = self.Togre.get_balances()

        clist = []
        if balances:
            for coin in balances['balances'].keys():
                if balances['balances'][coin] == "0.00000000":
                    continue
                clist.append("{1:<10}{0:>.8f}".format(float(balances['balances'][coin]), coin))
            return clist
        return None 
        
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
        global TS
        
        TS.clear_OpenOrders()
        TS.get_tradeogre_orders()
        
        OrdersList = TS.format_open_orders()

        return OrdersList
            
    def getOrderBook(self,coinl):
        
        
        OrderBook = self.Togre.get_order_book(coinl)
        
        if OrderBook:
            try: 
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
            except KeyError as e:
                return ['Error: url request (612)']
        else:
            return ['Error: url request (612)']
        
    def getTradePairHistory(self,coinl):
        
        TradePairHistory = self.Togre.get_trade_history(coinl)
        TradePairList = [] 
        if TradePairHistory:
            TradePairHistory.reverse()
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
        global CONFIG
        daddress = []
        coins = CONFIG.options("address")
        for c in coins:
            address = CONFIG['address'].get(c, '')
            if address:
                daddress.append(c.upper() + ": " + address)
        return daddress
    
    def getCoinPair(self):
        global CONFIG
        return CONFIG['pair'].get('order_book','').split(','), CONFIG['pair'].get('trade_history','').split(','),CONFIG['pair'].get('ticker','').split(',')
    
    def create(self):
        global CONFIG
        self.Togre = TradeOgreAPI(CONFIG['api'].get('pub_key',''), CONFIG['api'].get('secret_key',''))
    
        self.y,self.x = self.curses_pad.getmaxyx()
        self.keypress_timeout = 45 
        
        self.timeWidget = self.add(npyscreen.Textfield, name=" ",
                                    value=self.getTimeDate(),
                                    editable = None, 
                                    relx = int((self.x - len(self.getTimeDate().split('\n')[-1])-7) / 2))
        
        #self.getBalances()
            
        #self.add_handlers({"^O": self.cancel_order})

        with open(LOGOFILE, 'r') as logo:
            data = logo.readlines()
        
        linlen=len(data[2])
        self.logo = self.add(npyscreen.BoxTitle, values=data, rely=4, relx= int((self.x - linlen) / 2),
               max_width=linlen+7,max_height=len(data)+2)
        self.logo.editable = False 
        
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
        self.tradingBTC = self.add(npyscreen.TitleText, name="Trading BTC:", value=None, relyy = 30, relx=5, begin_entry_at = 16, use_two_lines = False)
        
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
     
        
        
        #self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE]  = self.exit_application    
        
        self.m1 = self.add_menu(name="Main Menu", shortcut="^M")
        self.m1.addItem(text="1.) Order Book Pair",onSelect=self.change_form_pair,shortcut="O")
        self.m1.addItem(text="2.) Trade History Pair",onSelect=self.change_form_history,shortcut="H")
        self.m1.addItem(text="3.) Ticker Pair",onSelect=self.change_form_ticker,shortcut="T")
        self.m1.addItem(text="4.) Place Buy Order",onSelect=self.change_form_buy,shortcut="B")
        self.m1.addItem(text="5.) Place Sell Order",onSelect=self.change_form_sell,shortcut="S")
        self.m1.addItem(text="6.) Cancel Order",onSelect=self.change_form_cancel,shortcut="C")
        self.m1.addItem(text="7.) Get Deposit Address",onSelect=self.change_form_deposit,shortcut="D")
        self.m1.addItem(text="8.) Withdraw",onSelect=self.change_form_withdraw,shortcut="W")
        
        
        self.m2 = self.add_menu("History Menu", shortcut="^H")
        self.m2.addItem(text="1.) Deposit History",onSelect=self.change_form_deposit_history,shortcut="D")
        self.m2.addItem(text="2.) Withdraw History",onSelect=self.change_form_withdraw_history,shortcut="W")
        self.m2.addItem(text="3.) Trade History",onSelect=self.change_form_trade_history,shortcut="T")
        
        #self.m1.addItem(text="7.) Add Deposit Address",onSelect=self.change_form_deposit,shortcut="D")
        
        self.display()
        
    def calculate_available_btc(self,clist, OpenOrders):
        order_type = []
        btc_price = []
        btc_pair_qty = []

        btc = 0.0
        for c in clist: 
            coin = c.split(' ')[0]
            if coin == "BTC":
                btc = c.split('       ')[-1]

        if OpenOrders:      
            for s in OpenOrders:
                order_type.append(re.split(' +',s)[7])
                btc_price.append(re.split(' +',s)[9])
                btc_pair_qty.append(re.split(' +',s)[10])
                
            
            running_btc = 0.0
            pending_btc = 0.0
            for otype,price,qty in zip(order_type,btc_price,btc_pair_qty):
                
                if otype == "BUY":
                    
                    running_btc += float(price)*float(qty)
            
                else:
                    pending_btc += float(price)*float(qty)
            available_btc = float(btc) - running_btc
            trading_btc = available_btc-(available_btc*0.002)
            return round(available_btc,10),round(pending_btc,10), round(trading_btc, 10)
        else:
            trading_btc = float(btc)-(float(btc)*0.002)
            return float(btc),0.0, float(trading_btc)
                
    def while_waiting(self):
        self.parentApp.coin_pair, self.parentApp.hcoin_pair, self.parentApp.tcoin_pair = self.getCoinPair()

        self.holdingCell.values = self.getBalances()
        self.holdingCell.display()
        
        self.tickerCell.values = self.getTicker(self.parentApp.tcoin_pair)
        self.tickerCell.name = "".join(["Ticker: ", self.parentApp.tcoin_pair[0].upper(), "-", self.parentApp.tcoin_pair[1].upper()])
        self.tickerCell.display()
        
        self.timeWidget.value = self.getTimeDate()
        self.timeWidget.display()
        
        self.OpenOrders.values = self.getOpenOrders()
        self.OpenOrders.display()
        
        
        abtc, pbtc, tbtc = self.calculate_available_btc(self.holdingCell.values, self.OpenOrders.values)
        self.availBTC.value = '{:.8f}'.format(abtc)
        self.pendingBTC.value = '{:.8f}'.format(pbtc)
        self.tradingBTC.value = '{:.8f}'.format(tbtc)
        
        self.OrderBook.values = self.getOrderBook(self.parentApp.coin_pair)
        self.OrderBook.name = "".join(["Order Book:  ", self.parentApp.coin_pair[0].upper(), "-",self.parentApp.coin_pair[1].upper()])
        self.OrderBook.display()
        
        self.TradeHistory.values = self.getTradePairHistory(self.parentApp.hcoin_pair)
        self.TradeHistory.name = "".join(['Trade History:  ',self.parentApp.hcoin_pair[0].upper(), "-",self.parentApp.hcoin_pair[1].upper()])
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
        
    def change_form_deposit_history(self, *args, **keywords):
        change_to = "DHISTORY"
        
        self.parentApp.change_form(change_to)
        
    def change_form_withdraw_history(self, *args, **keywords):
        change_to = "WHISTORY"
        
        self.parentApp.change_form(change_to)
        
    def change_form_trade_history(self, *args, **keywords):
        change_to = "THISTORY"
        
        self.parentApp.change_form(change_to)
          
    def change_form_withdraw(self, *args, **keywords):
        change_to = "WITHDRAW"
        
        self.parentApp.change_form(change_to)
            
    def change_form_ticker(self, *args, **keywords):
        change_to = "TICKER"
        
        self.parentApp.change_form(change_to)

def main():
    global CONFIG
    CONFIG = read_configuration(CONFFILE)
    
    global TS
    TS = SeleniumTradeOgre()    
    TS.tradeogre_login()
    
    App = ToTUIApplication()
    App.run() 
    
if __name__ == '__main__':
    main()
  
