import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GRAPH_API_KEY")

def send_telegram_message(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN_SILO")
    chat_id = os.getenv("TELEGRAM_CHAT_ID_SILO")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to send telegram message: {response.status_code} - {response.text}")

def check_positions():
    first = 100  # Number of items to fetch per request
    skip = 0     # Start with the first set of results

    # Silo ID's to monitor
    silo_ids = [
        "0xea9961280b48fe521ece83f6cd8a7e9b2c4ffc2e", # PENDLE, there is bad debt so here for test purposes
        "0x7bec832FF8060cD396645Ccd51E9E9B0E5d8c6e4", # weETH
        "0x4a2bd8dcc2539e19cb97DF98EF5afC4d069d9e4C", # ezETH
        "0x69eC552BE56E6505703f0C861c40039e5702037A", # WBTC
        "0xA8897b4552c075e884BDB8e7b704eB10DB29BF0D", # wstETH
        "0x601B76d37a2e06E971d3D63Cf16f41A44E306013", # uniETH
        # add here 
    ]
    silo_ids_string = ','.join([f'"{silo_id}"' for silo_id in silo_ids])

    while True:
        query = f"""
            query QueryPositions {{
              siloPositions(
                first: {first},
                skip: {skip},
                where: {{
                  silo_: {{id_in: [{silo_ids_string}]}},
                  riskFactor_gt: 0.9, # >1.0 means insolvent, very close to this value would mean "about to be liquidated"
                  riskScore_gt: 50000, # 50K is usually around 50k$ so a good value, imo
                  totalBorrowValue_gt: 0
                }},
                orderBy: riskFactor,
                orderDirection: desc,
              ) {{
                account {{
                  id
                }}
                silo {{
                  id
                  name
                  marketAssets: market {{
                    inputToken {{
                      symbol
                    }}
                  }}
                }}
                totalBorrowValue
                riskFactor
                riskScore
              }}
            }}
        """

        json_data = {
            "query": query,
            "operationName": "QueryPositions",
        }

        response = requests.post(
            f"https://gateway-arbitrum.network.thegraph.com/api/{api_key}/subgraphs/id/2ufoztRpybsgogPVW6j9NTn1JmBWFYPKbP7pAabizADU",
            json=json_data,
        )

        response_data = response.json()

        # Check if there are any positions returned
        positions = response_data["data"]["siloPositions"]
        if not positions:
            break

        # Process each position
        for position in positions:
            wallet_address = position["account"]["id"]
            input_token_symbol = position["silo"]["marketAssets"][0]["inputToken"]["symbol"]
            silo_name = position["silo"]["name"]
            silo_id = position["silo"]["id"]
            risk_factor = position["riskFactor"]
            risk_score = position["riskScore"]
            total_borrow_value = position["totalBorrowValue"]

            message = f"""
High Risk Position Detected!
Wallet Address: {wallet_address}
Input Token Symbol: {input_token_symbol}
Silo Name: {silo_name}
Silo ID: {silo_id}
Risk Factor: {risk_factor}
Risk Score: {risk_score}
Total Borrow Value: {total_borrow_value}
"""             
            print(message)
            send_telegram_message(message)

        # Increment the skip value to fetch the next set of results
        skip += first

def main():
    print("Checking positions in Arbitrum: ")
    check_positions()

if __name__ == "__main__":
    main()
