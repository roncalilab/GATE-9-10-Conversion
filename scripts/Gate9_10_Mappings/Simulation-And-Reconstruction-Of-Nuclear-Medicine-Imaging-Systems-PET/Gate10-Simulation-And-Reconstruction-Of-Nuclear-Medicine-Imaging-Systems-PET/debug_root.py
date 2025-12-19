#!/usr/bin/env python3
"""
Debug script to inspect ROOT file contents
"""

import uproot
import sys
from pathlib import Path

def inspect_root_file(filepath):
    """Inspect the contents of a ROOT file"""
    
    filepath = Path(filepath)
    
    if not filepath.exists():
        print(f"ERROR: File does not exist: {filepath}")
        return
    
    print(f"Inspecting: {filepath}")
    print("=" * 80)
    
    try:
        with uproot.open(filepath) as f:
            print(f"\n📁 Trees in file:")
            print("-" * 80)
            
            if len(f.keys()) == 0:
                print("❌ No trees found in file!")
                print("\nThis usually means:")
                print("  1. The simulation didn't complete successfully")
                print("  2. No events were generated")
                print("  3. The actor didn't write to disk (check write_to_disk=True)")
                return
            
            for key in f.keys():
                tree_name = key.split(';')[0]
                cycle = key.split(';')[1] if ';' in key else '1'
                print(f"  • {tree_name} (cycle {cycle})")
                
                # Get the tree
                tree = f[key]
                n_entries = tree.num_entries
                print(f"    Entries: {n_entries}")
                
                if n_entries > 0:
                    print(f"    Branches:")
                    for branch_name in tree.keys():
                        branch = tree[branch_name]
                        typename = branch.typename
                        print(f"      - {branch_name}: {typename}")
                    
                    # Show first few entries of key branches
                    print(f"\n    Sample data (first 5 entries):")
                    try:
                        arrays = tree.arrays(library="np", entry_stop=5)
                        for key_name in ['GlobalTime', 'TotalEnergyDeposit', 'EventID', 'RunID']:
                            if key_name in arrays:
                                print(f"      {key_name}: {arrays[key_name]}")
                    except Exception as e:
                        print(f"      Could not read sample data: {e}")
                else:
                    print(f"    ⚠️  Tree is empty!")
                
                print()
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_root.py <root_file>")
        print("\nExample:")
        print("  python debug_root.py output/pet.root")
        sys.exit(1)
    
    inspect_root_file(sys.argv[1])