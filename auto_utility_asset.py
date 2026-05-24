import requests
import json
import logging

# Setup logging to log errors to a file
logging.basicConfig(filename='utility_errors.log', level=logging.ERROR)

def fetch_exchange_rate(base_currency='USD', target_currency='EUR'):
    try:
        url = f'https://api.exchangerate-api.com/v4/latest/{base_currency}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if target_currency in data['rates']:
            return data['rates'][target_currency]
        else:
            raise ValueError(f"Target currency '{target_currency}' not found in the response.")
    
    except requests.exceptions.RequestException as e:
        logging.error(f"RequestException: {str(e)}")
        return None
    except ValueError as e:
        logging.error(f"ValueError: {str(e)}")
        return None

def convert_currency(amount, exchange_rate):
    try:
        return amount * exchange_rate
    except Exception as e:
        logging.error(f"Error in currency conversion: {str(e)}")
        return None

def main(base_currency='USD', target_currency='EUR', amount=100):
    try:
        exchange_rate = fetch_exchange_rate(base_currency, target_currency)
        if exchange_rate is not None:
            converted_amount = convert_currency(amount, exchange_rate)
            if converted_amount is not None:
                print(f"{amount} {base_currency} is equal to {converted_amount:.2f} {target_currency}")
            else:
                print("Failed to convert currency.")
        else:
            print("Failed to fetch exchange rate.")
    
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        print("An unexpected error occurred.")

# Self-test logic
if __name__ == "__main__":
    main()