Binance Futures Report

1. You need to add credentials.json (Service Account Key) file for access Google Sheets. 
How to? Google it.

2. You also need to set binance_api (API key) and binance_secret (Secret Key) as system variables [User Variables is okay]
Control Panel -> System and Security -> System -> Advanced Settings -> Environment Variables -> Add them

Also in main.py set up spreadsheet ID.

Only last 7 days orders are supported. 
After new trading day I suggest running script to get day statistics.

sheets and orders txt files:
If you want to set up new google sheet -> set sheets.txt to `no` and delete all lines from orders.txt

Output: 

![image](https://user-images.githubusercontent.com/63478397/128729721-07a4d298-d849-48be-9d42-fa50dc43ab0c.png)

For spot support: 
You have to add "Spot" list on Google Sheets.

Outpout:
![image](https://user-images.githubusercontent.com/63478397/129458598-e4532a39-70ab-4829-af5f-793fddec539c.png)

