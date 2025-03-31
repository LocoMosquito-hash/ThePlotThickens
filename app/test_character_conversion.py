import traceback
import os

def write_log(message):
    print(message)
    with open("conversion_test_log.txt", "a") as f:
        f.write(message + "\n")

try:
    write_log("Importing modules...")
    from app.utils.character_references import convert_mentions_to_char_refs, convert_char_refs_to_mentions
    write_log("Imports successful!")

    def test_conversion():
        write_log("=== Testing Character Reference Conversion Functions ===\n")
        
        # Convert simple dictionary to list of dictionaries as expected by the functions
        char_map = {"John Doe": 1}
        characters = [{"id": 1, "name": "John Doe"}]
        
        # Test data
        text = "@John Doe went to the store"
        
        # Test mention to reference conversion
        write_log("Testing convert_mentions_to_char_refs...")
        converted = convert_mentions_to_char_refs(text, characters)
        write_log(f"Original: {text}")
        write_log(f"Converted: {converted}")
        
        # Test reference to mention conversion
        write_log("\nTesting convert_char_refs_to_mentions...")
        back = convert_char_refs_to_mentions(converted, characters)
        write_log(f"Back to mentions: {back}")
        
        # Test with multiple characters
        multi_text = "Meeting between @John Doe and @Mary Smith"
        multi_characters = [
            {"id": 1, "name": "John Doe"},
            {"id": 2, "name": "Mary Smith"}
        ]
        
        write_log("\nTesting with multiple characters...")
        multi_converted = convert_mentions_to_char_refs(multi_text, multi_characters)
        write_log(f"Original: {multi_text}")
        write_log(f"Converted: {multi_converted}")
        
        multi_back = convert_char_refs_to_mentions(multi_converted, multi_characters)
        write_log(f"Back to mentions: {multi_back}")
        
        write_log("\nAll tests completed successfully!")

    if __name__ == "__main__":
        # Clean previous log
        if os.path.exists("conversion_test_log.txt"):
            os.remove("conversion_test_log.txt")
        test_conversion()
except Exception as e:
    error_msg = f"An error occurred: {e}"
    print(error_msg)
    with open("conversion_test_log.txt", "a") as f:
        f.write(error_msg + "\n")
        f.write(traceback.format_exc()) 