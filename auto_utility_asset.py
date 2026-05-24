import csv
import json
import sys
import os
import tempfile
from datetime import datetime

# --- Configuration ---
ERROR_LOG_FILE = "csv_to_json_error.log"

def _log_error(message):
    """Logs an error message to stderr and a local file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - ERROR: {message}"
    print(log_entry, file=sys.stderr)
    try:
        with open(ERROR_LOG_FILE, "a") as f:
            f.write(log_entry + "\n")
    except IOError as e:
        print(f"Could not write to error log file {ERROR_LOG_FILE}: {e}", file=sys.stderr)

def convert_csv_to_json(input_filepath, output_filepath):
    """
    Converts a CSV file to a JSON file. Each row in the CSV becomes a JSON object,
    with column headers as keys.

    Args:
        input_filepath (str): The path to the input CSV file.
        output_filepath (str): The path to the output JSON file.

    Returns:
        bool: True if conversion was successful, False otherwise.
    """
    data = []
    try:
        with open(input_filepath, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            if not csv_reader.fieldnames:
                # This handles cases where the file is entirely empty or just has blank lines
                # DictReader with only header will still have fieldnames, but no rows.
                _log_error(f"CSV file '{input_filepath}' appears to be empty or missing headers.")
            for row in csv_reader:
                data.append(row)
    except FileNotFoundError:
        _log_error(f"Input CSV file not found: '{input_filepath}'")
        return False
    except csv.Error as e:
        _log_error(f"Error reading CSV file '{input_filepath}': {e}")
        return False
    except UnicodeDecodeError:
        _log_error(f"Encoding error when reading '{input_filepath}'. Ensure it's UTF-8 or specify correct encoding.")
        return False
    except Exception as e:
        _log_error(f"An unexpected error occurred while reading '{input_filepath}': {e}")
        return False

    try:
        with open(output_filepath, mode='w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Successfully converted '{input_filepath}' to '{output_filepath}'")
        return True
    except IOError as e:
        _log_error(f"Error writing JSON file '{output_filepath}': {e}")
        return False
    except TypeError as e:
        _log_error(f"Error serializing data to JSON for '{output_filepath}': {e}")
        return False
    except Exception as e:
        _log_error(f"An unexpected error occurred while writing '{output_filepath}': {e}")
        return False

def self_test():
    """
    Executes a self-test with mock data to verify the conversion logic.
    """
    print("\n--- Running Self-Test ---")

    # Sample CSV data for testing
    sample_csv_content = """id,name,value,notes
1,Item A,100,First item description with "quotes"
2,Item B,200,"Second item, has a comma"
3,Item C,,No value
4,Item D,450,"Another, entry"
"""
    # Expected JSON output structure (all values are strings as read from CSV)
    expected_json_data = [
        {"id": "1", "name": "Item A", "value": "100", "notes": 'First item description with "quotes"'},
        {"id": "2", "name": "Item B", "value": "200", "notes": 'Second item, has a comma'},
        {"id": "3", "name": "Item C", "value": "", "notes": "No value"},
        {"id": "4", "name": "Item D", "value": "450", "notes": "Another, entry"}
    ]

    temp_input_csv = None
    temp_output_json = None
    test_passed = False

    try:
        # Create a temporary input CSV file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix=".csv") as temp_csv_file:
            temp_csv_file.write(sample_csv_content)
            temp_input_csv = temp_csv_file.name
        print(f"Created temporary input CSV: {temp_input_csv}")

        # Define path for a temporary output JSON file
        temp_output_json = tempfile.mktemp(suffix=".json")
        print(f"Temporary output JSON will be: {temp_output_json}")

        # Run the CSV to JSON conversion
        conversion_success = convert_csv_to_json(temp_input_csv, temp_output_json)

        if conversion_success:
            print(f"Conversion reported success. Verifying output...")
            # Verify the content of the generated JSON file
            if os.path.exists(temp_output_json):
                with open(temp_output_json, 'r', encoding='utf-8') as json_file:
                    actual_json_data = json.load(json_file)
                
                if actual_json_data == expected_json_data:
                    print("Self-test PASSED: Generated JSON matches expected data.")
                    test_passed = True
                else:
                    _log_error("Self-test FAILED: Generated JSON does not match expected data.")
                    _log_error(f"Expected: {json.dumps(expected_json_data, indent=2)}")
                    _log_error(f"Actual: {json.dumps(actual_json_data, indent=2)}")
            else:
                _log_error("Self-test FAILED: Output JSON file was not created.")
        else:
            _log_error("Self-test FAILED: Conversion function returned False.")

    except Exception as e:
        _log_error(f"An unexpected error occurred during self-test: {e}")
        _log_error(f"Details: {sys.exc_info()[0].__name__} - {e}")
    finally:
        # Clean up temporary files regardless of test outcome
        if temp_input_csv and os.path.exists(temp_input_csv):
            os.remove(temp_input_csv)
            print(f"Cleaned up temporary input CSV: {temp_input_csv}")
        if temp_output_json and os.path.exists(temp_output_json):
            os.remove(temp_output_json)
            print(f"Cleaned up temporary output JSON: {temp_output_json}")
        
        if not test_passed:
            sys.exit(1) # Indicate test failure with a non-zero exit code


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No command-line arguments provided, run the self-test
        self_test()
    elif len(sys.argv) == 3:
        # Two arguments expected: input CSV path and output JSON path
        input_csv_path = sys.argv[1]
        output_json_path = sys.argv[2]
        convert_csv_to_json(input_csv_path, output_json_path)
    else:
        # Incorrect number of arguments provided
        print("Usage: python script_name.py [input.csv output.json]")
        print("       If no arguments are provided, a self-test will be executed.")
        sys.exit(1) # Exit with an error code for incorrect usage