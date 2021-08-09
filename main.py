import requests
import os
import hmac
import hashlib
import time
from urllib.parse import urljoin, urlencode
import json
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'credentials.json'
#spreadsheet_id = '1XeMxUrlBCFaENJBJVivaNEPDK-wHrDlzeWem37bWAJE'
spreadsheet_id = '1ImX2APTLpHKbWs01QjXBJTFES8p0umkbEI2Ffn_VD-0' # test
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

BASE_URL = 'https://fapi.binance.com'

headers = {
    'X-MBX-APIKEY': os.environ.get('binance_api')
}

orders = []

def hashing(query_string):
    return hmac.new(os.environ.get('binance_secret').encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def get_timestamp():
    return int(time.time() * 1000)

def request(url, method, headers, params=None):
    response = getattr(requests, method)(url, headers=headers, params=params)
    if response.status_code == 200:
        return {'status': response.status_code, 'info': json.loads(response.text)}
    else:
        return {'status': response, 'info': response.text}

def get_opposite_side(side):
    if side == 'SELL':
        return 'BUY'
    if side == "BUY":
        return 'SELL'

def get_position_information(json, id, side, symbol, qty):
    if side == 'SELL':
        position = 'LONG'
    else:
        position = "SHORT"
    place = next((i for i, item in enumerate(json['info']) if item["orderId"] == id))
    opposite_side = get_opposite_side(side)
    current_qty = 0
    commission = 0
    commission_type = next((item for item in json['info'] if item["orderId"] == id))['commissionAsset']
    for order in reversed(json['info'][:place]):
        # Query order adding for more accurate in position choose
        if (order['symbol'] == symbol) and (order['side'] == opposite_side) and (round(current_qty) < round(float(qty))):

            current_qty += float(order['quoteQty'])
            if order['commissionAsset'] != commission_type:
                print('Commission different types;')
                raise ValueError
            commission += float(order['commission'])
            #print(f"Added to position {order['quoteQty']}, Current Position QTY: {current_qty}\nCommission Asset: {order['commissionAsset']}\Commission: {order['commission']}")
    #print(f'Position: {position} | Pair: {symbol} | Commission Asset: {commission_type} | Total Commission getting positions: {"{0:.20f}".format(commission)}')
    return position, commission


def get_all_orders_info(fromId=False, toId=False):
    global BNB_PRICE
    PATH = '/fapi/v1/userTrades'
    if fromId:
        params = {
            'timestamp': get_timestamp(),
            'limit': 1000,
            'fromId': fromId
        }
    else:
        params = {
            'timestamp': get_timestamp(),
            'limit': 1000
        }
    params['signature'] = hashing(urlencode(params))
    response = request(urljoin(BASE_URL, PATH), 'get', headers, params)
    theLastOrder = False
    try:
        for order in response['info']:
            if float(order['realizedPnl']) != 0:
                if not(theLastOrder):
                    theLastOrder = order['orderId']
                position_type, getting_position_commission = get_position_information(response, order['orderId'], order['side'], order['symbol'], order['quoteQty'])
                total_position_commission = getting_position_commission + float(order['commission'])
                print(f'Pair: {order["symbol"]} | Position: {order["side"]} | Position Type: {position_type} '
                      f'| PNL: {order["realizedPnl"]} '
                      f'| Date {time.strftime("%d %b %Y %H:%M:%S", time.gmtime(float(order["time"]) / 1000))} |'
                      f' QTY: {order["quoteQty"]} | Total Commission: {"{0:.20f}".format(total_position_commission)}')
                if order['commissionAsset'] == 'BNB':
                    dump_to_excel(time.strftime("%d %b %Y %H:%M:%S", time.gmtime(float(order["time"]) / 1000)), order["symbol"], position_type,
                                  float(order["realizedPnl"]), total_position_commission * BNB_PRICE,
                                  f"{order['commissionAsset']} | {'{0:.10f}'.format(total_position_commission)}", order['orderId'])
                else:
                    dump_to_excel(time.strftime("%d %b %Y %H:%M:%S", time.gmtime(float(order["time"]) / 1000)),
                                  order["symbol"], position_type,
                                  float(order["realizedPnl"]), total_position_commission,
                                  order['commissionAsset'], order['orderId'])
                #query_order(order['orderId'], order['symbol'])
    except Exception as e:
        print(e)
        print(response)
    return theLastOrder
    # for order in response['in']:
    #     #print(f'Pair: {order["symbol"]} | Position: {order["side"]}')
    #     try:
    #         # if order['status'] == ('FILLED' or 'OPEN'):
    #         #     print(order)
    #         #     print(f'Pair: {order["symbol"]} | Position: {order["positionSide"]} | Type: {order["origType"]} | Closing Position: {order["closePosition"]}')
    #         if int(order['realizedPnl']) != 0:
    #             print(f'Pair: {order["symbol"]} | Position: {order["side"]}')
    #         else:
    #             print('Not fulfilled order')
    #     except:
    #         print(f"Request Status: {order}")

def query_order(order_id, symbol):
    PATH = '/fapi/v1/order'
    params = {
        'timestamp': get_timestamp(),
        'orderId': order_id,
        'symbol': symbol
    }
    params['signature'] = hashing(urlencode(params))
    response = request(urljoin(BASE_URL, PATH), 'get', headers, params)
    try:
        print(response['info'].text)
    except:
        print(response)

def dump_to_excel(date, pair, position_type, pnl, commission, commission_type, order_id):
    global orders
    if str(order_id) in orders:
        return
    request = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        valueInputOption="USER_ENTERED",
        range='A1',
        body={
                 "values":  [[date, pair, position_type,commission_type, commission, pnl]]}
    ).execute()
    save_order(order_id)


def get_orders():
    global orders
    global orders_txt
    lines = orders_txt.readlines()
    for line in lines:
        orders.append(line.replace('\n', ''))



def save_order(order):
    global orders
    orders_txt.write(str(order) + '\n')


def color_rows():
    values = service.spreadsheets().values().batchUpdateByDataFilter(
        spreadsheetId=spreadsheet_id,
        valueInputOption="USER_ENTERED",
        body={'data' : {

        }}
    ).execute()
    print(values['values'])

def get_currency_price(currency_pair):
    PATH = 'https://api.binance.com/api/v3/avgPrice'
    params = {
        'symbol': currency_pair,
    }
    response = request(PATH, 'get', headers, params)
    return float(response['info']['price'])

def prepare_sheets():
    sheets_txt = open('sheets.txt', 'r+')
    line = next(sheets_txt)
    print(line)
    if line == 'yes':
        return
    values = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
              "requests": [
                {
                  "addConditionalFormatRule": {
                    "rule": {
                      "ranges": [
                        {
                          "startColumnIndex": 0,
                          "endColumnIndex": 6,
                          "startRowIndex": 1,
                          "endRowIndex": 2000
                        }
                      ],
                      "booleanRule": {
                        "condition": {
                          "type": "CUSTOM_FORMULA",
                          "values": [
                            {
                              "userEnteredValue": "=$F2>0"
                            }
                          ]
                        },
                        "format": {
                          "backgroundColor": {
                            "green": 0.88,
                            "red": 0.72,
                            "blue": 0.8,
                          }
                        }
                      }
                    },
                    "index": 0
                  }
                }
              ]
            }
    ).execute()
    values = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [
                                {
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 6,
                                    "startRowIndex": 1,
                                    "endRowIndex": 2000
                                }
                            ],
                            "booleanRule": {
                                "condition": {
                                    "type": "CUSTOM_FORMULA",
                                    "values": [
                                        {
                                            "userEnteredValue": "=$F2<0"
                                        }
                                    ]
                                },
                                "format": {
                                    "backgroundColor": {
                                        "green": 0.8,
                                        "red": 0.96,
                                        "blue": 0.8,
                                    }
                                }
                            }
                        },
                        "index": 0
                    }
                }
            ]
        }
    ).execute()
    sheets_txt.seek(0)  # move file pointer to beginning of file
    sheets_txt.write('yes')
    sheets_txt.close()

def main():
    prepare_sheets()
    get_orders()
    last_order = get_all_orders_info()
    orders_txt.close()


if __name__ == '__main__':
    orders_txt = open('orders.txt', 'r+')
    BNB_PRICE = get_currency_price('BNBUSDT')
    main()


