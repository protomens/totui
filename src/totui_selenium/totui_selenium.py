#!/bin/env python3
import random
import undetected_chromedriver as uc
import os
from getpass import getpass

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from datetime import datetime

from bs4 import BeautifulSoup
from time import sleep


BASEURL = "https://www.tradeogre.com"
LOGINURL = "https://tradeogre.com/account/signin"
ORDERSURL = "https://tradeogre.com/account/orders"
DEPOSITSURL = "https://tradeogre.com/account/history/deposits"
WITHDRAWURL = "https://tradeogre.com/account/history/withdrawals"
TRADESURL = "https://tradeogre.com/account/history/trades"
BALANCEURL = "https://tradeogre.com/account/balances"

BASEDIR = os.path.join(os.path.expanduser('~'), '.totui')
COINSFILE = os.path.join(BASEDIR, 'coins.list')

class SeleniumTradeOgre():
    driver = None
    OpenOrders = []
    coins = []
    
    def __init__(self):
            
        #CHROME
        print("\nNOTE: \n")
        print("We will open a browser and log you into your account to handle certain operations\n")
        print("You will need to complete a CAPTCHA to login.\n")
        print("You will be prompted for your e-mail,password,and OTP within this console.\n")
        print("Please be assured this information is only sent to TradeOgre and not handled any other way externally.")
        print("This is secure and safe. Please leave the browser open while TOTUI is opened as well.")
        print("You may minimize the browser to clear up clutter.")
        print("If you need to use TradeOgre outside of TOTUI, open a new tab within the same browser. Do not use the original tab.")
        print("If you'd rather login yourself than through this command prompt, please login to the browser first,")
        print("then press ENTER at each prompt in this terminal. We will handle the rest from there. ")
        print("\nCHEERS!\n")
        input("Press ENTER to continue")
        
        self.populate_CoinList()
        
        self.driver = self.createDriverInstance()

    def createDriverInstance(self):
        options = Options()
        options.add_argument('--disable-infobars')
        mydriver = uc.Chrome(options=options)
        mydriver.get(BASEURL)
        sleep(random.randint(3,5))
        
        return mydriver
    
    def get_tradeogre_orders(self):
        self.driver.get(ORDERSURL)
        sleep(2)
        HTML = self.driver.page_source
        soup = BeautifulSoup(HTML, features="html.parser")
        trBlocks = soup.find("tbody")
        
        OODict = {}
        
        k = 0
        try:  
            for tr in trBlocks.find_all("td"):
                if k == 0:
                    OODict['pair'] = tr.getText()
                elif k == 1:
                    OODict['type'] = tr.getText()
                elif k == 2: 
                    OODict['date'] = tr.getText()
                elif k == 3:
                    OODict['uuid'] = tr['data-id']
                    OODict['amt'] = tr.getText()
                elif k == 4:
                    OODict['price'] = tr.getText()
                else:
                    self.OpenOrders.append(OODict)
                    OODict = {}
                    k = -1
                k += 1
        except:
            self.OpenOrders = None
                
    def format_open_orders(self):
        k=1
        OrderList = []
        if self.OpenOrders:
            for order in self.OpenOrders:
                orderDate = datetime.strptime(order['date'], '%m/%d/%y %I:%M %p').strftime("%a, %b %d %Y %I:%M:%S %p")
                
                OrderList.append("{0:<3}{1:<10}{2:^6}{3:<10}{4:<12}{5:<12}{6:>40}".format(str(k) + ".) ", orderDate,
                                                               order['type'].upper(),order['pair'],
                                                               order['price'],order['amt'], order['uuid']))
                k += 1
            return OrderList
        else:
            return None
        
    def tradeogre_login(self):
        self.driver.get(LOGINURL)
        sleep(4)
        
        username = input("Email: ")
        password = getpass() 
        if username and password:
            self.driver.find_element(By.NAME, 'email').send_keys(username, Keys.TAB, password, Keys.ENTER)
        
        sleep(3)
        
        self.tradeogre_totp(None)
        
        
        print("You are now logged in")
        
    def tradeogre_getWallet_status(self,coin):
        self.driver.get(BALANCEURL)
        self.driver.find_element(By.CSS_SELECTOR, "input[type='search']").send_keys(coin,Keys.ENTER)
        sleep(2)
        
        HTML = self.driver.page_source
        soup = BeautifulSoup(HTML, features="html.parser")
        badgeBlock = soup.find('span', {'class' : 'badge'})
        
        if badgeBlock:
            return badgeBlock.getText()
        else:
            return "NO SUCH COIN"
        
        
            
    def tradeogre_withdraw(self, coin, amt, address):
        
        def complete_withdraw(self, amt, address,resultant):
            try: 
                self.driver.find_element(By.NAME, 'amount').clear()
                self.driver.find_element(By.NAME, 'amount').send_keys(amt)
                sleep(1)
                self.driver.find_element(By.NAME, 'withdrawaddress').send_keys(address)
                
                sleep(1)
                self.driver.find_element(By.CSS_SELECTOR, "input[value='Withdraw']").click()
                sleep(2)
                resultant['success'] = True
                resultant['message'] = "Success"
                return resultant
            except:
                #print("Something went wrong. No funds were withdraw. Please try again.")
                sleep(2)
                resultant['success'] = False
                resultant['message'] = "Error 42" 
                return resultant
        
        resultant = { "success" : False, "message" : None}
        
        sleep(1)
        self.driver.get(BASEURL + "/account/withdraw/" + coin.upper())
        sleep(2)
        HTML = self.driver.page_source
        soup = BeautifulSoup(HTML, features="html.parser")

        block = soup.find('div', {'class' : 'alert'})
        
        if block:
            if "Warning" in block.getText():
                resultant['success'] = False
                resultant['message'] = block.getText()
                return resultant
            
        return complete_withdraw(self, amt,address,resultant)
                
            
    def tradeogre_getDeposit_address(self, coin):
        try:
            self.driver.get(BASEURL + "/account/deposit/" + coin.upper())
            sleep(random.randint(3,7))
        except:
            print("NOT A VALID URL OR COIN")
            sleep(4)
            return
        
        try:
            daddressElement = self.driver.find_element(By.ID, 'depositaddresst1')
        except:
            print("COULD NOT FIND A DEPOSIT ADDRESS")
            sleep(4)
            return
        
        return daddressElement.get_attribute('value')
        
        
    def tradeogre_getDeposit_history(self):
        self.driver.get(DEPOSITSURL)
        sleep(2)
        HTML = self.driver.page_source
        
        soup = BeautifulSoup(HTML, features="html.parser")

        tableBody = soup.find('tbody')
        
        DepositDict = {}
        DepositDictList = []
        k=0
        try:
            for row in tableBody.find_all("td"):
                if k == 0:
                    DepositDict['coin'] = row.getText()
                elif k == 1:
                    DepositDict['amt'] = row.getText()
                elif k == 2:
                    DepositDict['date'] = row.getText()
                elif k == 3:
                    DepositDict['status'] = row.getText()
                else:
                    DepositDict['confirmations'] = row.getText()
                    k = -1
                    DepositDictList.append(DepositDict)
                    DepositDict = {}
            
                k += 1
        except:
            return None
                
        
        DepositList = []
        DepositList.append("{0:<20}{1:^16}{2:^20}{3:<12}{4:>8}".format('Coin','Amount', 'Date', 'Status','Confirmations'))    
        DepositList.append("================================================================================")
        for deposits in DepositDictList:
            DepositList.append("{0:<20}{1:^16}{2:^20}{3:<12}{4:>9}".format(deposits['coin'],deposits['amt'],deposits['date'],deposits['status'],deposits['confirmations']))
            
    
        return DepositList
    
    def tradeogre_getWithdraw_history(self):
        self.driver.get(WITHDRAWURL)
        sleep(2)
        HTML = self.driver.page_source
        soup = BeautifulSoup(HTML, features="html.parser")


        tableBody = soup.find('tbody')
        
        WithdrawDict = {}
        WithdrawDictList = []
        k=0
        for row in tableBody.find_all("td"):
            if k == 0:
                WithdrawDict['coin'] = row.getText()
            elif k == 1:
                WithdrawDict['amt'] = row.getText()
            elif k == 2:
                WithdrawDict['date'] = row.getText()
            else:
                WithdrawDict['status'] = row.getText()
                k = -1
                WithdrawDictList.append(WithdrawDict)
                #print(WithdrawDict)
                WithdrawDict = {}
        
            k += 1
            
        
        WithdrawList = []
        WithdrawList.append("{0:<18}{1:^16}{2:^20}{3:>8}".format('Coin','Amount','Date','Status'))    
        WithdrawList.append("=================================================================")
        for deposits in WithdrawDictList:
            WithdrawList.append("{0:<18}{1:^16}{2:<20}{3:>9}".format(deposits['coin'],deposits['amt'],deposits['date'],deposits['status'],))
            
            
        return WithdrawList
    
    def tradeogre_getTrade_history(self):
        self.driver.get(TRADESURL)
        sleep(2)
        HTML = self.driver.page_source
        soup = BeautifulSoup(HTML, features="html.parser")


        tableBody = soup.find('tbody')
        
        TradeDict = {}
        TradeDictList = []
        k=0
        for row in tableBody.find_all("td"):
            if k == 0:
                TradeDict['pair'] = row.getText()
            elif k == 1:
                TradeDict['type'] = row.getText()
            elif k == 2:
                TradeDict['date'] = row.getText()
            elif k == 3:
                TradeDict['amt'] = row.getText()
            elif k == 4:
                TradeDict['price'] = row.getText()
            else:
                TradeDict['base_amt'] = row.getText()
                k = -1
                TradeDictList.append(TradeDict)
                #print(TradeDict)
                TradeDict = {}
        
            k += 1
            
        
        TradeList = []
        TradeList.append("{0:<10}{1:^6}{2:^20}{3:^15}{4:^15}{5:>13}".format('Pair','Type','Date','Amount','Price','Base Amount'))    
        TradeList.append("=================================================================================")
        for deposits in TradeDictList:
            TradeList.append("{0:<10}{1:^6}{2:^20}{3:^15}{4:^15}{5:>13}".format(deposits['pair'],deposits['type'],deposits['date'],deposits['amt'],
                                                                                  deposits['price'],deposits['base_amt']))
            
         
        return TradeList
    
    def tradeogre_totp(self, OTP):
        resultant = {'sucess' : False, 'message' : None}
        if OTP:
            try: 
                self.driver.find_element(By.CSS_SELECTOR, "input[id='totp']").send_keys(OTP)
                #self.driver.find_element(By.ID, 'totp').send_keys(OTP)
                #sleep(1)
                #self.driver.find_element(By.ID, 'authSubmit').click()
                try:
                    self.driver.find_element(By.CSS_SELECTOR, "button[id='authSubmit']").click()
                    resultant['success'] = True
                    resultant['message'] = None
                    return resultant
                except Exception as e:
                    resultant['success'] = False
                    resultant['message'] = "CLICKING SUBMIT: " + str(e)
                    return resultant
                
            except Exception as e:
                resultant['success'] = False
                resultant['message'] = "INPUTING VALUE: " + str(e)
                return resultant
        else:
            OTP = input("2FA OTP: ")
            if OTP:
                self.driver.find_element(By.NAME, 'totp').send_keys(OTP, Keys.ENTER)

            
    def clear_OpenOrders(self):
        self.OpenOrders = []
        
    def populate_CoinList(self): 

        with open(COINSFILE, "r") as f:
            TOcoinFILE = f.readlines()
            
        for coin in TOcoinFILE:
            self.coins.append(coin.rstrip())
                

    

