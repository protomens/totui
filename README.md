# totui (Trade Ogre TUI)
A textual user interface (TUI) for the popular TradeOgre exchange

Has the ability to:

* Place Buy Orders
* Place Sell Orders
* List Order Books, Tickers, and Action History
* Withdraw to address for most coins
* Locate Deposit address
* & more!

## Dependencies
* Latest Chrome Browser (stable)


## Install (pip)
```shell
pip3 install totui
```

Configure `~/.totui/config.ini` (see below), then run
 
```shell
totui
```


## Install (Source)
From git source

```shell
git clone https://github.com/protomens/totui
cd totui
```


Install the following dependencies if you don't already have them installed:

```shell
pip3 install npyscreen
pip3 install requests
pip3 install selenium
pip3 install undected_chromedriver
pip3 install bs4
pip install urllib3
```

Build & Install
```shell
cd totui && python3 -m build
python3 setup.py install
```


## Configure

Edit **~/.totui/config.ini** to include your public and secret TradeOgre keys. These keys can be found by logging into your account and going to **settings**. Generate your keys if you haven't already. Paste the first into the first line under **[api]**,  **pub_key**. Paste after **=**. Paste the second key into the next line, **secret_key**, after the **=**.

All your changes within **totui** will be saved to this config file. It will startup how you left it.

Run:

`totui`


**Note:** *Your terminal size must be at least 178x62 otherwise you will get an error when trying to run this.* 

## Usage

Follow the menus and read the details. Read the on-screen instructions.

## Screenshot
![img/totui.png](img/totui.png)

## Disclaimer

I am in no way responsible for your actions with this app. I am not liable for any erroneous buy/sell orders you may place using totui. Instead, be cautious and double check your orders before submitting them. This is good practice in general.

## License

GPL v3.0 

# Tipjar

If you feel so inclined as to leave a tip this app will cotinue in development and issues raised will be handled in a timely manner. Programming costs time and money and donating helps the cause of open source and app development. 

`XMR: 82iYCRic1nQHb8RkU1T8ZYgebv7mzuxRJXiZ8fQ1crNoMtPqZRy4Rr1aJ9ND7RMd5uHTR9z8GbugGMSokmEq5JYsEuKtwHP`

`DERO: dero1qyxctkgzee00jh3md4etc8kxkr8x4hh7cckezrhn7de39kj4xaf9xqqa6xeta`

`BTC: bc1q70qdes2xrxyc03fgwekmmt8j2rds0fmg3dehth`



