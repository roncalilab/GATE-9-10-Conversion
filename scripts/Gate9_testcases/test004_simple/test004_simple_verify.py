#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-processing script for GATE 9 simulation statistics
Reads the stat.txt output and compares with reference (OpenGATE 10 style)
"""

import os
import sys
from typing import Dict, Optional

class Stats:
    """Simple container for statistics data"""
    def __init__(self):
        self.runs = 0
        self.events = 0
        self.tracks = 0
        self.steps = 0
        self.pps = 0.0
        self.tps = 0.0
        self.sps = 0.0
        self.track_types = {}
        
def read_gate9_stat_file(filename: str) -> Optional[Stats]:
    """
    Read GATE 9 SimulationStatisticActor output file
    Returns a Stats object
    """
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found")
        return None
    
    stats = Stats()
    raw_data = {}
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith('#'):
                continue
            
            # Remove leading '# ' and parse
            line = line[2:].strip()
            
            if '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # Try to convert to appropriate type
                    try:
                        if '.' in value:
                            raw_data[key] = float(value)
                        else:
                            raw_data[key] = int(value)
                    except ValueError:
                        raw_data[key] = value
    
    # Map to Stats object
    stats.runs = raw_data.get('NumberOfRun', 0)
    stats.events = raw_data.get('NumberOfEvents', 0)
    stats.tracks = raw_data.get('NumberOfTracks', 0)
    stats.steps = raw_data.get('NumberOfSteps', 0)
    stats.pps = raw_data.get('PPS (Primary per sec)', 0.0)
    stats.tps = raw_data.get('TPS (Track per sec)', 0.0)
    stats.sps = raw_data.get('SPS (Step per sec)', 0.0)
    
    # Store all raw data for potential track types
    stats.raw_data = raw_data
    
    return stats

def print_test(is_ok: bool, message: str):
    """Print test result with color coding"""
    status = "✓" if is_ok else "✗"
    color = "\033[92m" if is_ok else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {message}")

def assert_stats(stats1: Stats, stats2: Stats, tolerance: float = 0.0, 
                 track_types_flag: bool = False) -> bool:
    """
    Compare two Stats objects (mimics OpenGATE 10 assert_stats function)
    
    Args:
        stats1: Current simulation statistics
        stats2: Reference statistics
        tolerance: Relative tolerance (0.01 = 1%)
        track_types_flag: Whether to compare track types
    
    Returns:
        bool: True if all tests pass within tolerance
    """
    is_ok = True
    
    print("\n" + "="*70)
    print("STATISTICS COMPARISON")
    print("="*70)
    
    # Calculate percentage differences
    if stats2.events != 0:
        event_d = stats1.events / stats2.events * 100 - 100
    else:
        event_d = 100
    
    if stats2.tracks != 0:
        track_d = stats1.tracks / stats2.tracks * 100 - 100
    else:
        track_d = 100
    
    if stats2.steps != 0:
        step_d = stats1.steps / stats2.steps * 100 - 100
    else:
        step_d = 100
    
    if stats2.pps != 0:
        pps_d = stats1.pps / stats2.pps * 100 - 100
    else:
        pps_d = 100
    
    if stats2.tps != 0:
        tps_d = stats1.tps / stats2.tps * 100 - 100
    else:
        tps_d = 100
    
    if stats2.sps != 0:
        sps_d = stats1.sps / stats2.sps * 100 - 100
    else:
        sps_d = 100
    
    # Test runs
    b = stats1.runs == stats2.runs
    is_ok = b and is_ok
    print_test(b, f"Runs:         {stats1.runs} {stats2.runs}")
    
    # Test events
    b = abs(event_d) <= tolerance * 100
    is_ok = b and is_ok
    st = f"(tol = {tolerance * 100:.2f} %)"
    print_test(
        b,
        f"Events:       {stats1.events} {stats2.events} : {event_d:+.2f} %  {st}"
    )
    
    # Test tracks
    b = abs(track_d) <= tolerance * 100
    is_ok = b and is_ok
    print_test(
        b,
        f"Tracks:       {stats1.tracks} {stats2.tracks} : {track_d:+.2f} %  {st}"
    )
    
    # Test steps
    b = abs(step_d) <= tolerance * 100
    is_ok = b and is_ok
    print_test(
        b,
        f"Steps:        {stats1.steps} {stats2.steps} : {step_d:+.2f} %  {st}"
    )
    
    # Performance metrics (informational only)
    print_test(
        True,
        f"PPS:          {stats1.pps:.1f} {stats2.pps:.1f} : "
        f"{pps_d:+.1f}%    speedup = x{(pps_d + 100) / 100:.1f}"
    )
    print_test(
        True,
        f"TPS:          {stats1.tps:.1f} {stats2.tps:.1f} : "
        f"{tps_d:+.1f}%    speedup = x{(tps_d + 100) / 100:.1f}"
    )
    print_test(
        True,
        f"SPS:          {stats1.sps:.1f} {stats2.sps:.1f} : "
        f"{sps_d:+.1f}%    speedup = x{(sps_d + 100) / 100:.1f}"
    )
    
    # Track types comparison (if available)
    if track_types_flag and stats1.track_types:
        print("\nTrack Types:")
        print("-"*70)
        
        # Compare track types from stats1
        for item in stats1.track_types:
            v1 = stats1.track_types[item]
            if item in stats2.track_types:
                v2 = stats2.track_types[item]
                v_d = float(v1) / float(v2) * 100 - 100 if v2 != 0 else 100
                print_test(True, f"Track {item:8}{v1} {v2} : {v_d:+.1f}%")
            else:
                print_test(True, f"Track {item:8}{v1} 0")
        
        # Check for track types only in stats2
        for item in stats2.track_types:
            if item not in stats1.track_types:
                v2 = stats2.track_types[item]
                print_test(True, f"Track {item:8}0 {v2}")
        
        # Consistency check
        n = sum(int(t) for t in stats1.track_types.values())
        b = n == stats1.tracks
        print_test(b, f"Tracks      : {stats1.track_types}")
        print_test(b, f"Tracks (ref): {stats2.track_types}")
        print_test(b, f"Tracks vs track_types : {stats1.tracks} {n}")
        is_ok = b and is_ok
    
    print("="*70)
    
    return is_ok

def display_stats(stats: Stats):
    """Display statistics summary"""
    print("\n" + "="*70)
    print("SIMULATION STATISTICS")
    print("="*70)
    print(f"  Runs:             {stats.runs:>15,}")
    print(f"  Events:           {stats.events:>15,}")
    print(f"  Tracks:           {stats.tracks:>15,}")
    print(f"  Steps:            {stats.steps:>15,}")
    print(f"  PPS:              {stats.pps:>15,.1f}")
    print(f"  TPS:              {stats.tps:>15,.1f}")
    print(f"  SPS:              {stats.sps:>15,.1f}")
    
    if stats.track_types:
        print("\n  Track Types:")
        for particle, count in stats.track_types.items():
            print(f"    {particle:12s}: {count:>10,}")
    
    print("="*70)

def test_ok(is_ok: bool):
    """Print final test result (mimics OpenGATE 10 test_ok function)"""
    if is_ok:
        print("\n" + "="*70)
        print("✓✓✓ TEST PASSED ✓✓✓")
        print("="*70 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("✗✗✗ TEST FAILED ✗✗✗")
        print("="*70 + "\n")
        sys.exit(1)

def main():
    """Main function"""
    # Parse command line arguments
    stat_file = "stat004_simple.txt"
    ref_file = None
    tolerance = 0.01
    track_types_flag = False
    
    # Simple argument parsing
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--stat" and i + 1 < len(args):
            stat_file = args[i + 1]
            i += 2
        elif args[i] == "--ref" and i + 1 < len(args):
            ref_file = args[i + 1]
            i += 2
        elif args[i] == "--tolerance" and i + 1 < len(args):
            tolerance = float(args[i + 1])
            i += 2
        elif args[i] == "--track-types":
            track_types_flag = True
            i += 1
        else:
            i += 1
    
    # Default reference file location
    if ref_file is None:
        ref_file = "stat004_simple_ref.txt"
    
    print(f"\nReading current statistics from: {stat_file}")
    
    # Read current statistics
    stats = read_gate9_stat_file(stat_file)
    
    if not stats:
        print("Failed to read statistics file")
        sys.exit(1)
    
    # Display current statistics
    display_stats(stats)
    
    # Compare with reference if available
    if os.path.exists(ref_file):
        print(f"\nReading reference statistics from: {ref_file}")
        ref_stats = read_gate9_stat_file(ref_file)
        
        if ref_stats:
            is_ok = assert_stats(stats, ref_stats, tolerance, track_types_flag)
            test_ok(is_ok)
        else:
            print("Failed to read reference file")
            sys.exit(1)
    else:
        print(f"\nNo reference file found at: {ref_file}")
        print("Skipping comparison. To compare with reference:")
        print(f"  python3 {sys.argv[0]} --ref <reference_file.txt>")
        print("\nCurrent statistics displayed successfully.")

if __name__ == "__main__":
    main()