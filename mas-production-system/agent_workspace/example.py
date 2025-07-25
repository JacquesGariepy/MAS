#!/usr/bin/env python3
"""
Example usage of the sample library
"""

from sample_lib import SampleClass, helper_function, validate_input

def main():
    print("Sample Library Demo")
    print("-" * 30)
    
    # Create instance
    sample = SampleClass("Demo Collection")
    
    # Add some data
    items = ["Python", "JavaScript", "Go", "Rust"]
    for item in items:
        sample.add_data(item)
    
    # Process and display
    print("\n" + sample.process_data())
    
    # Use utility function
    message = "Hello from the swarm!"
    processed = helper_function(message)
    print(f"\nOriginal: {message}")
    print(f"Processed: {processed}")
    
    # Show object info
    print(f"\nObject info: {sample}")

if __name__ == "__main__":
    main()
