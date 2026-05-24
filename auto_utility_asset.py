import csv
import json
import sys
import os
import io
from datetime import datetime

# --- Configuration for logging ---
LOG_FILE_NAME = "csv_to_json_utility.log"

def _log_message(level, message, error_details=None):
    """
    Internal helper to log messages to stderr and a local log file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level.upper()}] {message}"
    if error_details:
        log_entry += f" - Details: {error_details}"

    print(log_entry, file=sys.stderr)

    try:
        with open(LOG_FILE_NAME, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except Exception as e:
        print(f"[{timestamp}] [ERROR] Failed to write to log file '{LOG_FILE_NAME}': {e}", file=sys.stderr)

def csv_to_json(csv_source, input_type='path', output_file_path=None, delimiter=','):
    """
    Converts CSV data to JSON.

    Args:
        csv_source (str): The source of the CSV data. Can be a file path or a CSV string.
        input_type (str): 'path' if csv_source is a file path, 'string' if csv_source is a CSV string.
                          Defaults to 'path'.
        output_file_path (str, optional): The path to the output JSON file. If None, the JSON
                                         string is returned and not saved to a file.
        delimiter (str): The delimiter used in the CSV data. Defaults to ','.

    Returns:
        str or None: The JSON string if output_file_path is None, otherwise None.
                     Returns None if an error occurs.
    """
    json_data = []
    
    try:
        if input_type == 'path':
            if not os.path.exists(csv_source):
                _log_message("error", f"Input CSV file not found: '{csv_source}'")
                return None
            try:
                with open(csv_source, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile, delimiter=delimiter)
                    for row in reader:
                        json_data.append(row)
            except Exception as e:
                _log_message("error", f"Failed to read or parse CSV file '{csv_source}'", str(e))
                return None
        elif input_type == 'string':
            csv_file_like = io.StringIO(csv_source)
            reader = csv.DictReader(csv_file_like, delimiter=delimiter)
            for row in reader:
                json_data.append(row)
        else:
            _log_message("error", f"Invalid input_type '{input_type}'. Must be 'path' or 'string'.")
            return None

    except csv.Error as e:
        _log_message("error", "CSV parsing error", str(e))
        return None
    except Exception as e:
        _log_message("error", "An unexpected error occurred during CSV reading", str(e))
        return None

    try:
        json_output_string = json.dumps(json_data, indent=4)
    except Exception as e:
        _log_message("error", "Failed to convert data to JSON string", str(e))
        return None

    if output_file_path:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as jsonfile:
                jsonfile.write(json_output_string)
            _log_message("info", f"Successfully converted and saved JSON to '{output_file_path}'")
            return None # Return None as data is saved to file
        except Exception as e:
            _log_message("error", f"Failed to write JSON to file '{output_file_path}'", str(e))
            return None
    else:
        _log_message("info", "Successfully converted CSV to JSON string (not saved to file).")
        return json_output_string

def run_self_test():
    """
    Executes a self-test with mock data to verify the utility's functionality.
    """
    _log_message("info", "--- Running self-test with mock data ---")

    mock_csv_data_basic = """name,age,city
Alice,30,New York
Bob,24,Los Angeles
Charlie,35,Chicago
"""
    mock_csv_data_semicolon = """product;price;category
Laptop;1200.00;Electronics
Mouse;25.50;Electronics
Desk;150.00;Furniture
"""
    
    temp_csv_file_basic = "temp_test_input_basic.csv"
    temp_json_file_basic = "temp_test_output_basic.json"
    temp_csv_file_semicolon = "temp_test_input_semicolon.csv"
    temp_json_file_semicolon = "temp_test_output_semicolon.json"

    test_passed = True

    # Test 1: Basic CSV to JSON file output
    _log_message("info", f"Test 1: Basic CSV (comma delimited) to JSON file ('{temp_json_file_basic}')")
    try:
        with open(temp_csv_file_basic, 'w', encoding='utf-8') as f:
            f.write(mock_csv_data_basic)
        
        result = csv_to_json(temp_csv_file_basic, 'path', temp_json_file_basic)
        
        if result is None and os.path.exists(temp_json_file_basic):
            with open(temp_json_file_basic, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
            
            expected_json = [
                {"name": "Alice", "age": "30", "city": "New York"},
                {"name": "Bob", "age": "24", "city": "Los Angeles"},
                {"name": "Charlie", "age": "35", "city": "Chicago"}
            ]
            
            if json_content == expected_json:
                _log_message("info", "Test 1 Passed: JSON content matches expected.")
            else:
                _log_message("error", "Test 1 Failed: JSON content mismatch.")
                test_passed = False
        else:
            _log_message("error", "Test 1 Failed: JSON file not created or unexpected return value.")
            test_passed = False
    except Exception as e:
        _log_message("error", f"Test 1 encountered an exception: {e}")
        test_passed = False
    finally:
        if os.path.exists(temp_csv_file_basic): os.remove(temp_csv_file_basic)
        if os.path.exists(temp_json_file_basic): os.remove(temp_json_file_basic)

    # Test 2: Semicolon delimited CSV to JSON file output
    _log_message("info", f"Test 2: Semicolon delimited CSV to JSON file ('{temp_json_file_semicolon}')")
    try:
        with open(temp_csv_file_semicolon, 'w', encoding='utf-8') as f:
            f.write(mock_csv_data_semicolon)
        
        result = csv_to_json(temp_csv_file_semicolon, 'path', temp_json_file_semicolon, delimiter=';')
        
        if result is None and os.path.exists(temp_json_file_semicolon):
            with open(temp_json_file_semicolon, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
            
            expected_json = [
                {"product": "Laptop", "price": "1200.00", "category": "Electronics"},
                {"product": "Mouse", "price": "25.50", "category": "Electronics"},
                {"product": "Desk", "price": "150.00", "category": "Furniture"}
            ]
            
            if json_content == expected_json:
                _log_message("info", "Test 2 Passed: JSON content matches expected.")
            else:
                _log_message("error", "Test 2 Failed: JSON content mismatch.")
                test_passed = False
        else:
            _log_message("error", "Test 2 Failed: JSON file not created or unexpected return value.")
            test_passed = False
    except Exception as e:
        _log_message("error", f"Test 2 encountered an exception: {e}")
        test_passed = False
    finally:
        if os.path.exists(temp_csv_file_semicolon): os.remove(temp_csv_file_semicolon)
        if os.path.exists(temp_json_file_semicolon): os.remove(temp_json_file_semicolon)

    # Test 3: CSV string to JSON string output
    _log_message("info", "Test 3: CSV string to JSON string (no file output).")
    try:
        csv_string = "header1,header2\nvalue1,value2\nvalue3,value4"
        json_result_string = csv_to_json(csv_string, 'string')
        
        expected_json = [
            {"header1": "value1", "header2": "value2"},
            {"header1": "value3", "header2": "value4"}
        ]
        
        if json_result_string:
            parsed_json = json.loads(json_result_string)
            if parsed_json == expected_json:
                _log_message("info", "Test 3 Passed: JSON string content matches expected.")
            else:
                _log_message("error", "Test 3 Failed: JSON string content mismatch.")
                test_passed = False
        else:
            _log_message("error", "Test 3 Failed: No JSON string returned.")
            test_passed = False
    except Exception as e:
        _log_message("error", f"Test 3 encountered an exception: {e}")
        test_passed = False

    # Test 4: Error handling - Non-existent file
    _log_message("info", "Test 4: Error handling - Non-existent input CSV file.")
    try:
        non_existent_file = "non_existent.csv"
        result = csv_to_json(non_existent_file, 'path', "output_non_existent.json")
        if result is None:
            _log_message("info", "Test 4 Passed: Correctly handled non-existent file.")
            if os.path.exists("output_non_existent.json"): os.remove("output_non_existent.json")
        else:
            _log_message("error", "Test 4 Failed: Did not correctly handle non-existent file.")
            test_passed = False
    except Exception as e:
        _log_message("error", f"Test 4 encountered an unexpected exception: {e}")
        test_passed = False

    _log_message("info", "--- Self-test complete ---")
    if test_passed:
        _log_message("info", "All self-tests passed successfully!")
    else:
        _log_message("error", "One or more self-tests failed.")
        sys.exit(1) # Indicate failure

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run self-test
        run_self_test()
    else:
        # Command-line arguments provided
        _log_message("info", "--- Running utility with command-line arguments ---")
        
        input_csv_path = None
        output_json_path = None
        delimiter = ','

        # Basic argument parsing
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "-i" or arg == "--input":
                if i + 1 < len(sys.argv):
                    input_csv_path = sys.argv[i+1]
                    i += 1
                else:
                    _log_message("error", "Error: --input requires a file path.")
                    _log_message("info", "Usage: python csv_to_json_utility.py -i <input_csv_file> -o <output_json_file> [-d <delimiter>]")
                    sys.exit(1)
            elif arg == "-o" or arg == "--output":
                if i + 1 < len(sys.argv):
                    output_json_path = sys.argv[i+1]
                    i += 1
                else:
                    _log_message("error", "Error: --output requires a file path.")
                    _log_message("info", "Usage: python csv_to_json_utility.py -i <input_csv_file> -o <output_json_file> [-d <delimiter>]")
                    sys.exit(1)
            elif arg == "-d" or arg == "--delimiter":
                if i + 1 < len(sys.argv):
                    delimiter = sys.argv[i+1]
                    if len(delimiter) != 1:
                        _log_message("error", "Error: --delimiter must be a single character.")
                        _log_message("info", "Usage: python csv_to_json_utility.py -i <input_csv_file> -o <output_json_file> [-d <delimiter>]")
                        sys.exit(1)
                    i += 1
                else:
                    _log_message("error", "Error: --delimiter requires a character.")
                    _log_message("info", "Usage: python csv_to_json_utility.py -i <input_csv_file> -o <output_json_file> [-d <delimiter>]")
                    sys.exit(1)
            else:
                _log_message("error", f"Unknown argument: {arg}")
                _log_message("info", "Usage: python csv_to_json_utility.py -i <input_csv_file> -o <output_json_file> [-d <delimiter>]")
                sys.exit(1)
            i += 1

        if not input_csv_path:
            _log_message("error", "Error: Input CSV file (--input) is required.")
            _log_message("info", "Usage: python csv_to_json_utility.py -i <input_csv_file> -o <output_json_file> [-d <delimiter>]")
            sys.exit(1)

        # Execute the conversion
        _log_message("info", f"Attempting to convert '{input_csv_path}' (delimiter: '{delimiter}') to JSON...")
        csv_to_json(input_csv_path, 'path', output_json_path, delimiter)
        _log_message("info", "--- Utility execution complete ---")