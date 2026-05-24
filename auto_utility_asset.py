import urllib.request
import urllib.parse
import sys
import os
import datetime

# --- Configuration ---
# Determine the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True) # Ensure the logs directory exists
LOG_FILE = os.path.join(LOG_DIR, "url_shortener_errors.log")
SHORTEN_API_ENDPOINT = "http://tinyurl.com/api-create.php" # Free, unauthenticated public API

# --- Logging Utility ---
def _log_error(message):
    """Logs an error message to a local file with a timestamp."""
    try:
        timestamp = datetime.datetime.now().isoformat()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ERROR: {message}\n")
        print(f"ERROR: {message} (details logged to {LOG_FILE})", file=sys.stderr)
    except Exception as e:
        print(f"FATAL ERROR: Could not write to log file {LOG_FILE}: {e}", file=sys.stderr)
        print(f"Original error: {message}", file=sys.stderr)

# --- Main Utility Function ---
def shorten_url(long_url):
    """
    Shortens a given long URL using tinyurl.com's unauthenticated API.

    Args:
        long_url (str): The URL to shorten.

    Returns:
        str: The shortened URL, or None if an error occurred.
    """
    if not isinstance(long_url, str) or not long_url.strip():
        _log_error(f"Invalid input: URL must be a non-empty string. Received: '{long_url}'")
        return None

    # Basic validation for URL format: must start with http:// or https://
    # This avoids sending malformed or unintended protocols to the external API.
    if not (long_url.startswith("http://") or long_url.startswith("https://")):
        _log_error(f"URL does not start with 'http://' or 'https://'. Please provide a valid web URL: '{long_url}'")
        return None

    try:
        # Encode the long URL to be safely passed as a query parameter
        params = urllib.parse.urlencode({'url': long_url})
        full_api_request_url = f"{SHORTEN_API_ENDPOINT}?{params}"

        # Make the request to the tinyurl API
        # tinyurl.com's API is simple and returns the shortened URL directly in the response body.
        with urllib.request.urlopen(full_api_request_url, timeout=10) as response:
            if response.status == 200:
                short_url = response.read().decode('utf-8').strip()
                # tinyurl sometimes returns an error message as plain text if it fails internally
                if short_url.startswith("Error"):
                    _log_error(f"tinyurl API returned an error for original URL '{long_url}': {short_url}")
                    return None
                return short_url
            else:
                _log_error(f"tinyurl API request failed for '{long_url}' with status {response.status}: {response.reason}")
                return None
    except urllib.error.URLError as e:
        _log_error(f"Network error or invalid URL '{long_url}' (could not reach tinyurl.com): {e.reason}")
        return None
    except Exception as e:
        _log_error(f"An unexpected error occurred while shortening '{long_url}': {e}")
        return None

# --- Self-Test Logic ---
def run_self_test():
    """
    Executes a self-test with mock data to verify the URL shortening logic.
    It checks for success, proper formatting, and error handling.
    """
    print("\n--- Running Self-Test (no arguments provided) ---")
    print(f"Logging directory: {LOG_DIR}")
    print(f"Error log file: {LOG_FILE}")
    
    sample_urls = [
        "https://www.google.com/search?q=python+url+shortener+api+free+unauthenticated&rlz=1C5CHFA_enUS893US893&oq=python+url+shortener+api+free+unauthenticated&aqs=chrome..69i57j0i22i30l2.12328j0j7&sourceid=chrome&ie=UTF-8",
        "http://example.com/a/very/long/path/to/a/specific/page/that/we/want/to/share/cleanly",
        "https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen",
        "https://invalid-domain-should-fail.com/path", # This should fail due to network (DNS/connection)
        "ftp://not-an-http-url.com/file.txt", # Expected to fail internal validation
        "", # Empty URL string
        None, # None as URL input
        123, # Not a string
    ]

    test_results = []
    success_count = 0
    failure_count = 0

    print("\nAttempting to shorten sample URLs...")
    for i, url in enumerate(sample_urls):
        print(f"\n[{i+1}/{len(sample_urls)}] Testing URL: '{url}'")
        short_url = shorten_url(url)
        
        result_entry = {"original": url, "shortened": short_url, "status": "FAIL", "reason": ""}

        if short_url:
            # Basic verification for a successful shortening
            is_valid_format = isinstance(short_url, str) and short_url.startswith("http://tinyurl.com/")
            is_shorter_than_original = False
            
            # Only compare length if the original URL was a valid http/s string
            if isinstance(url, str) and (url.startswith("http://") or url.startswith("https://")):
                is_shorter_than_original = len(short_url) < len(url)
            
            if is_valid_format and is_shorter_than_original:
                result_entry["status"] = "PASS"
                result_entry["reason"] = "Short URL returned, valid format, and shorter than original."
                success_count += 1
            else:
                result_entry["status"] = "FAIL"
                if not is_valid_format:
                    result_entry["reason"] += "Shortened URL has an invalid format. "
                if not is_shorter_than_original and isinstance(url, str) and (url.startswith("http://") or url.startswith("https://")):
                    result_entry["reason"] += "Shortened URL is not shorter than original. "
                elif not (isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))):
                    result_entry["reason"] += "Original URL was invalid, length comparison skipped. "
                failure_count += 1
        else:
            result_entry["status"] = "FAIL"
            result_entry["reason"] = "No short URL returned (function reported an error or internal validation failed)."
            failure_count += 1
        
        test_results.append(result_entry)
        print(f"  Result: {result_entry['status']} - {result_entry['reason']}")
        if short_url:
            print(f"  Shortened: {short_url}")

    print("\n--- Self-Test Summary ---")
    print(f"Total Test Cases: {len(sample_urls)}")
    print(f"Passed: {success_count}")
    print(f"Failed: {failure_count}")

    if failure_count == 0:
        print("\nAll self-test cases passed successfully!")
    else:
        print(f"\n{failure_count} self-test cases failed. Check console output and '{LOG_FILE}' for details.")

    # Optionally write self-test results to a dedicated log file
    test_log_file = os.path.join(LOG_DIR, "url_shortener_self_test_results.log")
    try:
        timestamp = datetime.datetime.now().isoformat()
        with open(test_log_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- Self-Test Run [{timestamp}] ---\n")
            for res in test_results:
                f.write(f"Original: {res['original']}\n")
                f.write(f"Shortened: {res['shortened']}\n")
                f.write(f"Status: {res['status']}\n")
                f.write(f"Reason: {res['reason']}\n")
                f.write("-" * 20 + "\n")
            f.write(f"Summary: Passed {success_count}/{len(sample_urls)}, Failed {failure_count}/{len(sample_urls)}\n")
            f.write("=" * 40 + "\n")
        print(f"Detailed self-test results also logged to: {test_log_file}")
    except Exception as e:
        _log_error(f"Could not write self-test results to {test_log_file}: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If command-line arguments are provided, treat them as URLs to shorten.
        input_urls = sys.argv[1:]
        print("--- URL Shortener Utility ---")
        print(f"Attempting to shorten {len(input_urls)} URL(s)...")
        results = {}
        for url in input_urls:
            print(f"\nOriginal URL: {url}")
            short_url = shorten_url(url)
            if short_url:
                results[url] = short_url
                print(f"Shortened URL: {short_url}")
            else:
                results[url] = "Failed to shorten. Check error logs."
                print("Failed to shorten this URL. Check error logs for details.")
        
        print("\n--- Summary ---")
        for original, shortened in results.items():
            print(f"{original} -> {shortened}")
        print(f"\nError logs can be found at: {LOG_FILE}")
    else:
        # If no command-line arguments are provided, execute the self-test.
        run_self_test()