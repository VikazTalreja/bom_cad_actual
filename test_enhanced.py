#!/usr/bin/env python3
"""
Enhanced STEP file testing script
Use this to test different STEP files and see what they contain
"""

from step_parser import parse_step_file, extract_step_components
import sys

def test_step_file(file_path):
    """Test a STEP file and show detailed information"""
    print(f"Testing STEP file: {file_path}")
    print("=" * 50)
    
    try:
        # Parse the file
        print("Parsing STEP file...")
        step_data = parse_step_file(file_path)
        print(f"Parsed {len(step_data)} entities")
        
        # Show entity types
        entity_types = {}
        for entity in step_data:
            entity_type = entity['type']
            if entity_type in entity_types:
                entity_types[entity_type] += 1
            else:
                entity_types[entity_type] = 1
        
        print(f"\nEntity types found:")
        for entity_type, count in sorted(entity_types.items()):
            print(f"  {entity_type}: {count}")
        
        # Extract components
        print(f"\nExtracting components...")
        components = extract_step_components(step_data)
        
        print(f"\nExtracted {len(components)} components:")
        for i, comp in enumerate(components, 1):
            print(f"  Component {i}:")
            print(f"    ID: {comp['id']}")
            print(f"    Type: {comp['type']}")
            print(f"    Part Number: {comp['part_number']}")
            print(f"    Description: {comp['description']}")
            print(f"    Footprint: {comp['footprint']}")
            print(f"    Context: {comp['context']}")
            print()
        
        # Show some sample entities for debugging
        print("Sample entities (first 5):")
        for i, entity in enumerate(step_data[:5]):
            print(f"  Entity {i+1}: #{entity['id']} = {entity['type']}")
            print(f"    Parameters: {entity['parameters'][:3]}...")  # Show first 3 params
            print()
            
    except Exception as e:
        print(f"Error testing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_step_file(sys.argv[1])
    else:
        # Test with default file
        test_step_file("test.step")
        print("\n" + "="*50)
        print("To test a different file, run:")
        print("python test_enhanced.py your_file.step")
