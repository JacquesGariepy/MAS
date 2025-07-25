"""
Core module with main functionality
"""

class SampleClass:
    """A sample class to demonstrate library structure"""
    
    def __init__(self, name="Sample"):
        """Initialize the SampleClass
        
        Args:
            name (str): Name for this instance
        """
        self.name = name
        self.data = []
        self._config = {
            "verbose": False,
            "max_items": 1000
        }
        
    def add_data(self, item):
        """Add data to the collection
        
        Args:
            item: Item to add to the collection
            
        Returns:
            str: Confirmation message
        """
        if len(self.data) >= self._config["max_items"]:
            raise ValueError(f"Maximum items ({self._config['max_items']}) exceeded")
            
        self.data.append(item)
        message = f"Added {item} to {self.name}"
        
        if self._config["verbose"]:
            print(message)
            
        return message
        
    def process_data(self):
        """Process all collected data
        
        Returns:
            str: Processing result summary
        """
        if not self.data:
            return "No data to process"
            
        result = f"Processing {len(self.data)} items:\n"
        
        # Group by type
        type_counts = {}
        for item in self.data:
            item_type = type(item).__name__
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
        for item_type, count in type_counts.items():
            result += f"  - {item_type}: {count} items\n"
            
        # List items
        for i, item in enumerate(self.data, 1):
            result += f"  {i}. {item}\n"
            
        return result
        
    def clear_data(self):
        """Clear all data from the collection"""
        self.data.clear()
        return f"Cleared all data from {self.name}"
        
    def get_stats(self):
        """Get statistics about the data
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            "name": self.name,
            "count": len(self.data),
            "types": list(set(type(item).__name__ for item in self.data)),
            "config": self._config.copy()
        }
        
    def configure(self, **kwargs):
        """Update configuration settings
        
        Args:
            **kwargs: Configuration key-value pairs
        """
        self._config.update(kwargs)
        
    def __str__(self):
        return f"SampleClass(name={self.name}, items={len(self.data)})"
        
    def __repr__(self):
        return f"SampleClass('{self.name}')"
