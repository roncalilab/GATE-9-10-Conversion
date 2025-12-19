#!/usr/bin/env python3
"""
GATE 10 Offline Coincidence Sorter
Processes singles to create coincidences and delayed coincidences
Run this AFTER the main simulation completes
"""

import uproot
import numpy as np
from pathlib import Path
import opengate as gate

def sort_coincidences(singles_file, output_file, time_window_ns=120, offset_ns=0):
    """
    Sort singles into coincidences using a time window
    
    Parameters:
    - singles_file: path to singles ROOT file
    - output_file: path to output coincidences ROOT file
    - time_window_ns: coincidence time window in nanoseconds
    - offset_ns: time offset for delayed coincidences (0 for prompt)
    """
    
    print(f"Reading singles from: {singles_file}")
    
    # Read singles data
    with uproot.open(singles_file) as f:
        tree = f['Singles_main_window']  # Energy window filtered singles
        
        # Get all branches
        branches = tree.arrays(library="np")
        
        # Extract key information
        times = branches['GlobalTime']
        eventIDs = branches['EventID']
        energies = branches['TotalEnergyDeposit']
        
        # Position information
        posX = branches['PostPosition_X']
        posY = branches['PostPosition_Y']
        posZ = branches['PostPosition_Z']
        
        # Volume IDs for detector identification
        volumeIDs = branches['PostStepUniqueVolumeID']
        
        # Track information
        trackIDs = branches['TrackID']
        
        # Get run information if available
        if 'RunID' in branches.keys():
            runIDs = branches['RunID']
        else:
            runIDs = np.zeros(len(times), dtype=int)
    
    print(f"Total singles: {len(times)}")
    
    # Sort by time
    sort_idx = np.argsort(times)
    times = times[sort_idx]
    eventIDs = eventIDs[sort_idx]
    energies = energies[sort_idx]
    posX = posX[sort_idx]
    posY = posY[sort_idx]
    posZ = posZ[sort_idx]
    volumeIDs = volumeIDs[sort_idx]
    trackIDs = trackIDs[sort_idx]
    runIDs = runIDs[sort_idx]
    
    # Apply time offset for delayed coincidences
    times_shifted = times + offset_ns
    
    # Find coincidences
    coincidences = []
    i = 0
    n_singles = len(times)
    
    print("Sorting coincidences...")
    while i < n_singles - 1:
        t1 = times_shifted[i]
        
        # Look for coincident singles within time window
        for j in range(i + 1, n_singles):
            t2 = times_shifted[j]
            time_diff = abs(t2 - t1)
            
            # Check if within time window
            if time_diff <= time_window_ns:
                # Check if from different detectors
                if volumeIDs[i] != volumeIDs[j]:
                    # Store coincidence
                    coinc = {
                        'time1': times[i],
                        'time2': times[j],
                        'eventID1': eventIDs[i],
                        'eventID2': eventIDs[j],
                        'energy1': energies[i],
                        'energy2': energies[j],
                        'globalPosX1': posX[i],
                        'globalPosY1': posY[i],
                        'globalPosZ1': posZ[i],
                        'globalPosX2': posX[j],
                        'globalPosY2': posY[j],
                        'globalPosZ2': posZ[j],
                        'volumeID1': volumeIDs[i],
                        'volumeID2': volumeIDs[j],
                        'runID': runIDs[i],
                        'trackID1': trackIDs[i],
                        'trackID2': trackIDs[j],
                        # Add placeholders for scatter info (would need full tracking)
                        'comptonPhantom1': 0,
                        'comptonPhantom2': 0,
                        'RayleighPhantom1': 0,
                        'RayleighPhantom2': 0,
                        'sourceID1': 0,  # Would need source tracking
                        'sourceID2': 0,
                    }
                    coincidences.append(coinc)
                    break
            elif time_diff > time_window_ns:
                # No more coincidences for this single
                break
        
        i += 1
        
        if i % 1000 == 0:
            print(f"Processed {i}/{n_singles} singles, found {len(coincidences)} coincidences")
    
    print(f"Total coincidences found: {len(coincidences)}")
    
    # Convert to numpy arrays
    if len(coincidences) > 0:
        coinc_dict = {key: np.array([c[key] for c in coincidences]) 
                      for key in coincidences[0].keys()}
        
        # Write to ROOT file
        print(f"Writing coincidences to: {output_file}")
        with uproot.recreate(output_file) as f:
            f["Coincidences"] = coinc_dict
        
        print(f"Successfully wrote {len(coincidences)} coincidences")
    else:
        print("No coincidences found!")
    
    return len(coincidences)


def main():
    """
    Process singles to create prompt and delayed coincidences
    """
    
    # Configuration
    singles_file = "/home/joshua/gate10_scripts/Simulation-And-Reconstruction-Of-Nuclear-Medicine-Imaging-Systems-PET/output/singles_filtered.root"
    prompt_output = "/home/joshua/gate10_scripts/Simulation-And-Reconstruction-Of-Nuclear-Medicine-Imaging-Systems-PET/output/coincidences.root"
    delay_output = "/home/joshua/gate10_scripts/Simulation-And-Reconstruction-Of-Nuclear-Medicine-Imaging-Systems-PET/output/delay.root"
    
    time_window = 120  # ns
    delay_offset = 500  # ns
    
    # Check if singles file exists
    if not Path(singles_file).exists():
        print(f"Error: Singles file not found: {singles_file}")
        print("Run the main simulation first!")
        return
    
    # Sort prompt coincidences
    print("\n" + "="*80)
    print("SORTING PROMPT COINCIDENCES")
    print("="*80)
    n_prompt = sort_coincidences(singles_file, prompt_output, 
                                  time_window_ns=time_window, 
                                  offset_ns=0)
    
    # Sort delayed coincidences
    print("\n" + "="*80)
    print("SORTING DELAYED COINCIDENCES")
    print("="*80)
    n_delay = sort_coincidences(singles_file, delay_output, 
                                 time_window_ns=time_window, 
                                 offset_ns=delay_offset)
    
    print("\n" + "="*80)
    print("COINCIDENCE SORTING COMPLETE")
    print("="*80)
    print(f"Prompt coincidences: {n_prompt}")
    print(f"Delayed coincidences: {n_delay}")
    print(f"\nOutput files:")
    print(f"  - {prompt_output}")
    print(f"  - {delay_output}")


if __name__ == "__main__":
    main()