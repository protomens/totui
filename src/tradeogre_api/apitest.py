from tradeogre_api import TradeOgreAPI


to = TradeOgreAPI("b51255004dc3070ab2b43857152da584", "399d4e09d3cb07eaacb659327a7d756c")

coinl = ["XMR", "BTC"]
json = to.get_order_book(coinl)
print(json['buy'])
