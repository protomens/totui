from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError
import requests


class TradeOgreAPI():
    apiURL = "https://tradeogre.com/api/v1"
    auth=""
    
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.auth = HTTPBasicAuth(self.key,self.secret)
        
    def get_balances(self):
        endpoint = '/account/balances'
        try:
            r = requests.get(self.apiURL + endpoint, auth=self.auth)
        except (ConnectionError,NewConnectionError) as e:
            #print(str(e))
            return None
        return r.json()
    
    def get_ticker(self,coinl):
        coinpair = '-'.join([coinl[0], coinl[1]])
        endpoint = '/ticker/%s' % coinpair
        try:
            r = requests.get(self.apiURL + endpoint, auth=self.auth)
        except (ConnectionError,NewConnectionError) as e:
            #print(str(e))
            return None
        if r.status_code == 200:
            return r.json()
        else:
            return None
    
    def get_open_orders(self):
        endpoint = '/account/orders'
        try:
            r = requests.get(self.apiURL + endpoint, auth=self.auth)
        except (ConnectionError,NewConnectionError) as e:
            #print(str(e))
            return None
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def get_order_book(self,coinl):
        coinpair = '-'.join([coinl[0], coinl[1]])
        endpoint = '/orders/%s' % coinpair
        try:
            r = requests.get(self.apiURL + endpoint, auth=self.auth)
        except (ConnectionError,NewConnectionError) as e:
            #print(str(e))
            return None
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def get_trade_history(self, coinl):
        coinpair = '-'.join([coinl[0], coinl[1]])
        endpoint = '/history/%s' % coinpair
        try:
            r = requests.get(self.apiURL + endpoint, auth=self.auth)
        except (ConnectionError,NewConnectionError) as e:
            #print(str(e))
            return None
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def place_buy_order(self,coinl,qty,price):
        market = '-'.join([coinl[0], coinl[1]])
        endpoint = '/order/buy'
        try:
            r = requests.post(self.apiURL + endpoint, data={'market': market, 'quantity': qty, 'price': str(price)}, auth=self.auth)
        except (ConnectionError, NewConnectionError) as e:
            return {'success' : False, "error" : "Connection Error"}
        
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 405:
            return {'success' : False, "error" : "HTTP 405: Method not allowed"}
        else:
            return {'success' : False, "error" : str(r.status_code)}
        
    def place_sell_order(self,coinl,qty,price):
        market = '-'.join([coinl[0], coinl[1]])
        endpoint = '/order/sell'
        try: 
            r = requests.post(self.apiURL + endpoint, data={'market': market, 'quantity': qty, 'price': price}, auth=self.auth)
        except (ConnectionError, NewConnectionError) as e:
            return {'success' : False, "error" : "Connection Error"}
        
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 405:
            return {'success' : False, "error" : "HTTP 405: Method not allowed"}
        else:
            return {'success' : False, "error" : str(r.status_code)}
        
    def cancel_order(self, uuid):
        endpoint = '/order/cancel'
        try:
            r = requests.post(self.apiURL + endpoint, data={'uuid' : uuid}, auth=self.auth)
        except (ConnectionError, NewConnectionError) as e:
            return {"success" : False}
        
        if r.status_code == 200:
            return r.json()
        else:
            return {"success" : False}
