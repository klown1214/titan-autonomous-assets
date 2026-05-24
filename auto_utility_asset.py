import json

def format_json_pretty(json_string, indent=4):
    """
    Formats a JSON string for readability and validates its syntax.

    Args:
        json_string (str): The JSON string to format.
        indent (int, optional): The indentation level for pretty-printing.
                                Defaults to 4.

    Returns:
        str: A pretty-printed JSON string if valid, otherwise an error message
             indicating the issue.
    """
    if not isinstance(json_string, str):
        return f"Error: Input must be a string, but received type {type(json_string).__name__}."
    try:
        data = json.loads(json_string)
        return json.dumps(data, indent=indent)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON string. Details: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    # --- Self-test with mock data ---

    print("--- JSON Formatter & Validator Self-Test ---")
    print("\nThis script pretty-prints and validates JSON strings.")
    print("When run without arguments, it executes these self-tests.")
    print("\n" + "="*60 + "\n")

    # Test Case 1: Valid JSON Object (compact)
    mock_valid_json_1 = '{"name": "Alice", "age": 30, "isStudent": false, "courses": [{"title": "Math", "credits": 3}, {"title": "History", "credits": 4}], "address": null}'
    print("Test Case 1: Valid JSON Object (compact form)")
    print("Input:\n", mock_valid_json_1)
    print("\nFormatted Output (indent=2):")
    print(format_json_pretty(mock_valid_json_1, indent=2))
    print("\n" + "="*60 + "\n")

    # Test Case 2: Valid JSON Array (compact)
    mock_valid_json_2 = '[{"id": 1, "item": "Apple"}, {"id": 2, "item": "Banana", "price": 1.25}]'
    print("Test Case 2: Valid JSON Array (compact form)")
    print("Input:\n", mock_valid_json_2)
    print("\nFormatted Output (default indent=4):")
    print(format_json_pretty(mock_valid_json_2))
    print("\n" + "="*60 + "\n")

    # Test Case 3: Invalid JSON (missing comma and quote)
    mock_invalid_json_1 = '{"user": "Bob", "email": "bob@example.com" "active": true}'
    print("Test Case 3: Invalid JSON (missing comma and quote)")
    print("Input:\n", mock_invalid_json_1)
    print("\nFormatted Output (should show error):")
    print(format_json_pretty(mock_invalid_json_1))
    print("\n" + "="*60 + "\n")

    # Test Case 4: Invalid JSON (malformed structure)
    mock_invalid_json_2 = '{"data": [1,2,3}, "status": "ok"}' # Mismatched bracket
    print("Test Case 4: Invalid JSON (malformed structure)")
    print("Input:\n", mock_invalid_json_2)
    print("\nFormatted Output (should show error):")
    print(format_json_pretty(mock_invalid_json_2))
    print("\n" + "="*60 + "\n")

    # Test Case 5: Non-string input
    mock_non_string_input = {"key": "value"} # This is a dict, not a JSON string
    print("Test Case 5: Non-string Input (a Python dict, not a JSON string)")
    print("Input:\n", mock_non_string_input)
    print("\nFormatted Output (should show error):")
    print(format_json_pretty(mock_non_string_input))
    print("\n" + "="*60 + "\n")

    print("--- Self-Test Complete ---")