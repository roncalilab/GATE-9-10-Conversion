#!/usr/bin/env python3
"""
Post-processing script to create coincidences from singles
Compatible with GATE 10 output for analysis with run_analysis.py
"""

import uproot
import numpy as np
from pathlib import Path
import awkward as ak

def find_coincidences(singles, time_window=120e3, offset=0):
    """
    Find coincidences from singles events
    
    Parameters:
    -----------
    singles : dict
        Dictionary containing singles data arrays
    time_window : float
        Coincidence time window in picoseconds (default 120 ns = 120000 ps)
    offset : float
        Time offset for delayed coincidences in picoseconds (default 0)
    
    Returns:
    --------
    dict : Dictionary containing coincidence data
    """
    
    # Extract relevant data
    times = singles['GlobalTime']  # In picoseconds
    event_ids = singles['EventID']
    run_ids = singles['RunID']
    
    print(f"  Time range: {times.min():.2e} to {times.max():.2e} ps")
    print(f"  Time window: {time_window:.2e} ps ({time_window/1e3:.1f} ns)")
    print(f"  Offset: {offset:.2e} ps ({offset/1e3:.1f} ns)")
    
    # Get position data
    pos_x = singles['PostPosition_X']
    pos_y = singles['PostPosition_Y']
    pos_z = singles['PostPosition_Z']
    
    # Energy
    energy = singles['TotalEnergyDeposit']
    
    # Try to get source ID from the data
    # Method 1: Check if there's a direct SourceID field
    if 'SourceID' in singles:
        source_ids = singles['SourceID']
    # Method 2: Try to infer from position (F18 at y=-20mm, O15 at y=+20mm)
    elif 'PrePosition_Y' in singles:
        pre_pos_y = singles['PrePosition_Y']
        source_ids = np.where(pre_pos_y < 0, 0, 1)  # Source 0 at negative Y, Source 1 at positive Y
    # Method 3: Fall back to event ID pattern
    else:
        source_ids = event_ids % 2
    
    # Process information for scatter detection
    process = singles.get('ProcessDefinedStep', np.zeros(len(times), dtype=object))
    
    # Apply time offset
    adjusted_times = times + offset
    
    # Sort by time
    sort_idx = np.argsort(adjusted_times)
    sorted_times = adjusted_times[sort_idx]
    sorted_event_ids = event_ids[sort_idx]
    sorted_run_ids = run_ids[sort_idx]
    sorted_pos_x = pos_x[sort_idx]
    sorted_pos_y = pos_y[sort_idx]
    sorted_pos_z = pos_z[sort_idx]
    sorted_energy = energy[sort_idx]
    sorted_source_ids = source_ids[sort_idx]
    sorted_process = process[sort_idx] if len(process) > 0 else process
    
    # Find coincidences using sliding window
    coincidences = {
        'eventID1': [],
        'eventID2': [],
        'sourceID1': [],
        'sourceID2': [],
        'runID': [],
        'time1': [],
        'time2': [],
        'globalPosX1': [],
        'globalPosY1': [],
        'globalPosZ1': [],
        'globalPosX2': [],
        'globalPosY2': [],
        'globalPosZ2': [],
        'energy1': [],
        'energy2': [],
        'comptonPhantom1': [],
        'comptonPhantom2': [],
        'RayleighPhantom1': [],
        'RayleighPhantom2': [],
    }
    
    i = 0
    n = len(sorted_times)
    
    while i < n - 1:
        t1 = sorted_times[i]
        j = i + 1
        
        # Check all events within time window
        while j < n and (sorted_times[j] - t1) <= time_window:
            # Valid coincidence found
            coincidences['eventID1'].append(sorted_event_ids[i])
            coincidences['eventID2'].append(sorted_event_ids[j])
            coincidences['sourceID1'].append(sorted_source_ids[i])
            coincidences['sourceID2'].append(sorted_source_ids[j])
            coincidences['runID'].append(sorted_run_ids[i])
            coincidences['time1'].append(sorted_times[i])
            coincidences['time2'].append(sorted_times[j])
            coincidences['globalPosX1'].append(sorted_pos_x[i])
            coincidences['globalPosY1'].append(sorted_pos_y[i])
            coincidences['globalPosZ1'].append(sorted_pos_z[i])
            coincidences['globalPosX2'].append(sorted_pos_x[j])
            coincidences['globalPosY2'].append(sorted_pos_y[j])
            coincidences['globalPosZ2'].append(sorted_pos_z[j])
            coincidences['energy1'].append(sorted_energy[i])
            coincidences['energy2'].append(sorted_energy[j])
            
            # Check for Compton/Rayleigh scatter
            if len(sorted_process) > 0:
                comp1 = 1 if 'compt' in str(sorted_process[i]).lower() else 0
                comp2 = 1 if 'compt' in str(sorted_process[j]).lower() else 0
                rayl1 = 1 if 'rayl' in str(sorted_process[i]).lower() else 0
                rayl2 = 1 if 'rayl' in str(sorted_process[j]).lower() else 0
            else:
                comp1 = comp2 = rayl1 = rayl2 = 0
                
            coincidences['comptonPhantom1'].append(comp1)
            coincidences['comptonPhantom2'].append(comp2)
            coincidences['RayleighPhantom1'].append(rayl1)
            coincidences['RayleighPhantom2'].append(rayl2)
            
            j += 1
        
        i += 1
    
    # Convert to numpy arrays and convert times from ps to seconds for output
    for key in coincidences:
        coincidences[key] = np.array(coincidences[key])
        if 'time' in key.lower():
            coincidences[key] = coincidences[key] / 1e12  # ps to seconds
    
    if len(coincidences['eventID1']) > 0:
        print(f"  First coincidence time: {coincidences['time1'][0]:.6f} s")
        print(f"  Last coincidence time: {coincidences['time1'][-1]:.6f} s")
    
    return coincidences


def process_pet_data(input_file, output_file=None):
    """
    Process singles data to create coincidences and delayed coincidences
    
    Parameters:
    -----------
    input_file : str or Path
        Input ROOT file containing Singles_LSO tree (typically singles.root)
    output_file : str or Path, optional
        Output ROOT file (default: pet.root in same directory)
    """
    
    input_path = Path(input_file)
    if output_file is None:
        output_file = input_path.parent / "pet.root"
    else:
        output_file = Path(output_file)
    
    print(f"Reading singles from: {input_path}")
    
    # Read singles data
    with uproot.open(input_path) as f:
        # List all available keys
        print(f"Available trees in file: {f.keys()}")
        
        tree_name = None
        # Try to find the singles tree with various possible names
        possible_names = ['main_window', 'Singles_LSO', 'Singles', 'singles_filtered', 'Singles_LSO_main_window']
        for key in f.keys():
            key_base = key.split(';')[0]
            if any(name in key_base for name in possible_names):
                tree_name = key_base
                break
        
        if tree_name is None:
            print(f"ERROR: No Singles tree found in {input_path}")
            print(f"Available trees: {f.keys()}")
            print("\nPlease check that the simulation completed successfully.")
            print("The tree should be named 'main_window', 'Singles_LSO' or similar.")
            raise ValueError(f"No Singles tree found in {input_path}. Available: {list(f.keys())}")
        
        print(f"Found tree: {tree_name}")
        singles_tree = f[tree_name]
        
        # Read all branches
        print(f"Available branches: {singles_tree.keys()}")
        singles = singles_tree.arrays(library="np")
    
    print(f"Number of singles: {len(singles['GlobalTime'])}")
    
    # Create prompt coincidences (120 ns window = 120000 ps)
    print("Creating prompt coincidences...")
    coincidences = find_coincidences(singles, time_window=120e3, offset=0)
    print(f"Number of prompt coincidences: {len(coincidences['eventID1'])}")
    
    # Create delayed coincidences (500 ns offset = 500000 ps, 120 ns window = 120000 ps)
    print("Creating delayed coincidences...")
    delayed = find_coincidences(singles, time_window=120e3, offset=500e3)
    print(f"Number of delayed coincidences: {len(delayed['eventID1'])}")
    
    print(f"\nWriting output to: {output_file}")
    with uproot.recreate(output_file) as f_out:
        # Write singles (with time in seconds)
        f_out["Singles"] = singles_for_output
        
        # Write prompt coincidences
        f_out["Coincidences"] = coincidences
        
        # Write delayed coincidences
        f_out["delay"] = delayed
    
    print("\n" + "="*80)
    print("Processing complete!")
    print(f"Singles: {len(singles_for_output['GlobalTime'])}")
    print(f"Coincidences: {len(coincidences['eventID1'])}")
    print(f"Delayed: {len(delayed['eventID1'])}")
    print("="*80)
    return output_file


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python process_coincidences.py <input_root_file> [output_root_file]")
        print("\nExample:")
        print("  python process_coincidences.py output/singles.root")
        print("  python process_coincidences.py output/singles.root output/pet.root")
        print("\nTo debug your ROOT file first, run:")
        print("  python debug_root.py output/singles.root")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    process_pet_data(input_file, output_file)