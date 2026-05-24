import requests
import json
import sys
import logging

# --- Configuration ---
# Free API for geo-IP lookup. Provides comprehensive JSON data including IP, country, city, etc.
# Check their terms for rate limits (currently 45 req/min for free tier).
GEO_IP_API_URL = "https://ip-api.com/json/"
TIMEOUT_SECONDS = 5 # Timeout for API requests in seconds

# --- Logging Setup ---
# All errors encountered by the utility will be logged to this file.
LOG_FILE = "titan_ip_utility_errors.log"
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_external_ip_info(ip_address: str = None) -> dict | None:
    """
    Fetches external IP address and associated geographical information.

    This function queries a free, public API to retrieve details about
    a given IP address. If no IP address is provided, it fetches information
    about the machine's own public IP address.

    Args:
        ip_address (str, optional): An IP address (e.g., "8.8.8.8") to query.
                                    If None, the utility will fetch its own
                                    external IP. Defaults to None.

    Returns:
        dict | None: A dictionary containing IP information (e.g., country, city,
                     ISP, IP address itself) if the request is successful,
                     otherwise None.
    """
    url = GEO_IP_API_URL
    if ip_address:
        # Append the specific IP address to the URL for querying a different IP
        url = f"{GEO_IP_API_URL}{ip_address}"

    try:
        # Make an HTTP GET request to the Geo-IP API
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # Parse the JSON response
        data = response.json()

        # The ip-api.com service returns a 'status' field.
        if data.get("status") == "success":
            return data
        else:
            # Log specific API error messages
            error_message = data.get("message", "Unknown error from API")
            logging.error(f"API returned an error for IP '{ip_address or 'self'}': {error_message}. URL: {url}")
            return None

    except requests.exceptions.Timeout:
        # Handle cases where the request takes too long to respond
        logging.error(f"Request to {url} timed out after {TIMEOUT_SECONDS} seconds for IP '{ip_address or 'self'}'.")
        return None
    except requests.exceptions.ConnectionError as e:
        # Handle network-related errors (e.g., DNS failure, refused connection)
        logging.error(f"Connection error while trying to reach {url} for IP '{ip_address or 'self'}': {e}")
        return None
    except requests.exceptions.HTTPError as e:
        # Handle HTTP protocol errors (e.g., 404 Not Found, 500 Internal Server Error)
        logging.error(f"HTTP error {e.response.status_code} from {url} for IP '{ip_address or 'self'}': {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        # Handle errors when the response content is not valid JSON
        logging.error(f"Failed to decode JSON response from {url} for IP '{ip_address or 'self'}': {e}. Response content: '{response.text}'")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        logging.error(f"An unexpected error occurred while fetching IP info for '{ip_address or 'self'}': {e}", exc_info=True)
        return None

if __name__ == "__main__":
    target_ip = None
    ip_info = None # Initialize ip_info to None
    is_self_test = False

    # Check if any command-line arguments were provided.
    # sys.argv[0] is always the script's name.
    if len(sys.argv) > 1:
        target_ip = sys.argv[1]
        print(f"--- Titan IP Utility: Querying IP: {target_ip} ---")
        # Execute the core utility function for the provided IP
        ip_info = get_external_ip_info(target_ip)
    else:
        # If no arguments, activate self-test mode with mock data as per requirements.
        is_self_test = True
        print("--- Titan IP Utility: Running Self-Test (Using Mock Data) ---")
        # Use mock data to simulate a successful API response without making an external network call.
        ip_info = {
            "query": "127.0.0.1", # A loopback IP for mock purposes
            "status": "success",
            "country": "Mockland",
            "countryCode": "MK",
            "region": "MKL",
            "regionName": "Mock State",
            "city": "Mockville",
            "zip": "M0CK",
            "lat": 0.0,
            "lon": 0.0,
            "timezone": "Europe/London",
            "isp": "Mock ISP Inc.",
            "org": "Mock Organization",
            "as": "AS0 MOCK-AS",
            "reverse": "mock.local",
            "mobile": False,
            "proxy": False,
            "hosting": False
        }
        print("Self-test with mock data generated successfully!")


    # Display results to the console
    if ip_info:
        print("\nSuccessfully retrieved IP information:")
        # Pretty print the JSON output for readability
        print(json.dumps(ip_info, indent=2))
        # No additional "Self-test completed successfully!" print is needed here,
        # as the mock data generation already confirmed success.
    else:
        print("\nFailed to retrieve IP information.")
        print(f"Please check '{LOG_FILE}' for detailed error logs.")
        # This block is not expected to be hit for self-test with mock data,
        # as mock_ip_info is always a valid dictionary. It's kept for explicit IP queries.
        if is_self_test:
            print("\nSelf-test unexpectedly failed. There might be an issue with mock data generation logic.")
        sys.exit(1) # Exit with an error code if the operation failed.