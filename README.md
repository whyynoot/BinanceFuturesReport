Binance Futures Report

1. You need to add credentials.json (Service Account Key) file for access Google Sheets. 
How to? Google it.

2. You also need to set binance_api (API key) and binance_secret (Secret Key) as system variables [User Variables is okay]
Control Panel -> System and Security -> System -> Advanced Settings -> Environment Variables -> Add them

Also in main.py set up spreadsheet ID.

Only last 7 days orders are supported. 
After new trading day I suggest running script to get day statistics.

Output: 

![image](https://user-images.githubusercontent.com/63478397/128442834-36a5c036-c24b-4a70-98ce-68524dec5765.png)