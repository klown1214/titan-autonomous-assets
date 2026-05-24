import re
import json
import sys
import os
import datetime

# --- Configuration (can be modified by user or external script) ---
# Default log file path for processing (if arguments are provided)
DEFAULT_INPUT_FILE = "input.log"
# Default output JSON file path (if arguments are provided)
DEFAULT_OUTPUT_FILE = "output.json"
# Default regex pattern for parsing log lines (can be customized)
# This pattern captures: [Timestamp] LEVEL: Message
DEFAULT_REGEX_PATTERN = r"^\[(.*?)\] (.*?): (.*)$"
# Default group names to assign to the captured regex groups
DEFAULT_GROUP_NAMES = ["timestamp", "level", "message"]

# --- Utility Functions ---

def _log_error(message, e=None):
    """Logs an error message to stderr and a local error log file."""
    error_time = datetime.datetime.now().isoformat()
    error_message = f"[{error_time}] ERROR: {message}"
    if e:
        error_message += f" - Exception: {type(e).__name__}: {e}"

    # Log to stderr for immediate feedback
    print(error_message, file=sys.stderr)

    # Optionally, log to a local error file
    try:
        with open("log_parser_errors.log", "a", encoding="utf-8") as f:
            f.write(error_message + "\n")
    except Exception as file_e:
        print(f"[{error_time}] CRITICAL ERROR: Could not write to error log file: {file_e}", file=sys.stderr)

def parse_text_with_regex(text_content, regex_pattern, group_names=None):
    """
    Parses a given text content using a regular expression pattern.

    Args:
        text_content (str): The multi-line string content to parse.
        regex_pattern (str): The regular expression pattern with capture groups.
        group_names (list, optional): A list of names for the captured groups.
                                      If None or mismatched, default names (group_1, group_2, ...) are used.

    Returns:
        list: A list of dictionaries, where each dictionary represents a parsed line
              and its keys correspond to group_names or default names.
              Returns an empty list on parsing failure or no matches.
    """
    parsed_data = []
    try:
        compiled_regex = re.compile(regex_pattern)
        for line_num, line in enumerate(text_content.splitlines()):
            if not line.strip(): # Skip empty lines
                continue
            match = compiled_regex.match(line.strip())
            if match:
                record = {}
                # Check if group_names are provided and match the number of captured groups
                if group_names and len(group_names) == len(match.groups()):
                    for i, name in enumerate(group_names):
                        record[name] = match.group(i + 1)
                else:
                    # Fallback to generic names if group_names not provided or mismatched
                    for i, group_val in enumerate(match.groups()):
                        record[f"group_{i + 1}"] = group_val
                parsed_data.append(record)
    except re.error as e:
        _log_error(f"Invalid regex pattern provided: '{regex_pattern}'", e)
        return []
    except Exception as e:
        _log_error(f"An unexpected error occurred during regex parsing of text content.", e)
        return []
    return parsed_data

def process_file_to_json(input_filepath, output_filepath, regex_pattern, group_names=None):
    """
    Reads a file, parses its content using a regex, and saves the structured data as JSON.

    Args:
        input_filepath (str): Path to the input text file.
        output_filepath (str): Path to save the output JSON file.
        regex_pattern (str): The regular expression pattern with capture groups.
        group_names (list, optional): Names for the captured groups.

    Returns:
        bool: True if processing and saving was successful, False otherwise.
    """
    if not os.path.exists(input_filepath):
        _log_error(f"Input file not found: {input_filepath}")
        return False

    file_content = ""
    try:
        with open(input_filepath, "r", encoding="utf-8") as f:
            file_content = f.read()
    except IOError as e:
        _log_error(f"Error reading input file: {input_filepath}", e)
        return False
    except Exception as e:
        _log_error(f"An unexpected error occurred while reading file: {input_filepath}", e)
        return False

    parsed_data = parse_text_with_regex(file_content, regex_pattern, group_names)

    if not parsed_data:
        _log_error(f"No data parsed from '{input_filepath}' using pattern '{regex_pattern}'. This might be expected if no matches are found.")
        # We still return True if no data found but no error occurred. The user gets an empty list.
        # However, for a file processing, it's often an error condition if no data is found at all.
        # Let's consider it an error for file processing as it implies the regex might be wrong or file empty.
        return False

    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=4)
        print(f"Successfully processed '{input_filepath}' and saved structured data to '{output_filepath}'")
        return True
    except IOError as e:
        _log_error(f"Error writing output JSON file: {output_filepath}", e)
        return False
    except TypeError as e:
        _log_error(f"Error during JSON serialization. Check data structure validity.", e)
        return False
    except Exception as e:
        _log_error(f"An unexpected error occurred while writing JSON file: {output_filepath}", e)
        return False

# --- Self-Test / Main Execution Logic ---

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # User provided arguments, assume they want to process files.
        # Expected arguments:
        # sys.argv[1] -> input file path
        # sys.argv[2] -> output JSON file path (optional, defaults to DEFAULT_OUTPUT_FILE)
        # sys.argv[3] -> regex pattern (optional, defaults to DEFAULT_REGEX_PATTERN)
        # sys.argv[4:] -> group names (optional, comma-separated string, e.g., "timestamp,level,message")

        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_FILE
        regex = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_REGEX_PATTERN
        
        group_names = DEFAULT_GROUP_NAMES
        if len(sys.argv) > 4:
            # If group names are provided as a single comma-separated string
            group_names = sys.argv[4].split(',')
            group_names = [name.strip() for name in group_names if name.strip()]
        
        print(f"--- Running in File Processing Mode ---")
        print(f"  Input File: {input_file}")
        print(f"  Output JSON: {output_file}")
        print(f"  Regex Pattern: '{regex}'")
        print(f"  Group Names: {group_names}")

        if not process_file_to_json(input_file, output_file, regex, group_names):
            print(f"File processing failed or produced no output. Check 'log_parser_errors.log' for details.")
        print(f"--- File Processing Complete ---")

    else:
        # No arguments provided, execute self-test mode.
        print("--- Running Self-Test: Unstructured Text to JSON Parser Utility ---")
        print("This test demonstrates parsing sample log-like data and outputting it as structured JSON.")

        # Sample log data simulating server logs or application events
        sample_log_data = """
[2023-10-27 10:01:05] INFO: Request received from user:12345 for /api/data
[2023-10-27 10:01:10] DEBUG: Processing item_id:ABC-001 in module 'core'
[2023-10-27 10:01:12] ERROR: Failed to connect to DB for user:12345. Retrying...
[2023-10-27 10:01:15] INFO: Response sent to user:12345 (200 OK)
[2023-10-27 10:02:01] WARNING: High CPU usage detected on host:server-01. Threshold: 85%
This line does not match the pattern and should be ignored.
[2023-10-27 10:02:05] INFO: Service restart initiated.
"""
        # Define a specific regex pattern for the sample log data
        # This pattern specifically captures: full Timestamp, Log Level, and the rest as Message.
        test_regex_pattern = r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+): (.*)$"
        test_group_names = ["timestamp", "level", "message"] # Names for the captured groups

        print(f"\n--- Sample Input Text Data ---\n{sample_log_data.strip()}")
        print(f"\n--- Using Regex Pattern ---\n'{test_regex_pattern}'")
        print(f"\n--- With Group Names ---\n{test_group_names}")

        # Perform the parsing
        parsed_results = parse_text_with_regex(sample_log_data, test_regex_pattern, test_group_names)

        print("\n--- Self-Test Results (JSON Output to stdout) ---")
        if parsed_results:
            # Print to stdout in a pretty JSON format
            print(json.dumps(parsed_results, indent=4))

            # Optionally, save self-test output to a temporary file
            temp_output_file = "self_test_output.json"
            try:
                with open(temp_output_file, "w", encoding="utf-8") as f:
                    json.dump(parsed_results, f, indent=4)
                print(f"\nSelf-test output also saved to '{temp_output_file}' for review.")
            except Exception as e:
                _log_error(f"Failed to save self-test output to '{temp_output_file}'", e)
        else:
            _log_error("Self-test failed to parse any data. Check the sample data and regex pattern.")

        print("\n--- Self-Test Complete ---")