import main as futures

BASE_URL = 'https://api.binance.com'

def query_all_orders(symbol):
    PATH = '/api/v3/allOrders'
    params = {
        'timestamp': futures.get_timestamp(),
        'symbol': symbol
    }
    params['signature'] = futures.hashing(futures.urlencode(params))
    response = futures.request(futures.urljoin(BASE_URL, PATH), 'get', futures.headers, params)
    for order in response['info']:
        try:
            #print(order['symbol'], 'Price:', float(order['price']), 'QTY:', float(order['origQty']))
            #print(order['symbol'], float(order['price']), float(order['origQty']) * float(order['price']))
            dump_spot_to_excel(
                futures.time.strftime("%d %b %Y %H:%M:%S", futures.time.gmtime(float(order['time']) / 1000)),
                order['symbol'], order['side'], float(order['orderId']), float(order['price']), float(order['origQty']) * float(order['price']))

        except:
            print(f"Request Status: {order}")

def dump_spot_to_excel(date, symbol,type, id, price, qty):
    if str(id) in futures.orders:
        return
    request = futures.service.spreadsheets().values().append(
        spreadsheetId=futures.spreadsheet_id,
        valueInputOption="USER_ENTERED",
        range='Spot!A1',
        body={
            'values': [[date, symbol, type, price, '', qty]]
        }
        # body={
        #          "values":  [[futures.time.gmtime(float(date) / 1000), symbol, float(price), 'NONE', float(qty) * float(price)]]
        # }
    ).execute()
    #print(request)
    futures.save_order(id)

def main():
    futures.get_orders()
    query_all_orders(input('Symbol: '))

if __name__ == "__main__":
    main()
