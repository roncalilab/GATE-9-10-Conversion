#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-processing verification script for GATE 9 test008_dose_actor
Compares test output against reference data
"""

import numpy as np
import itk
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os
from typing import Optional


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


def print_test(ok, message):
    """Print test result with OK/FAILED prefix"""
    status = "✓" if ok else "✗"
    color = "\033[92m" if ok else "\033[91m"
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


def get_info_from_image(img):
    """Extract image metadata"""
    class ImageInfo:
        def __init__(self):
            self.size = None
            self.spacing = None
            self.origin = None
            self.dir = None
    
    info = ImageInfo()
    info.size = np.array(itk.size(img))
    info.spacing = np.array(img.GetSpacing())
    info.origin = np.array(img.GetOrigin())
    info.dir = np.array(img.GetDirection())
    return info


def assert_images_properties(info1, info2):
    """Check if image properties match"""
    is_ok = True
    
    if not np.all(info1.size == info2.size):
        print_test(False, f"Sizes differ: {info1.size} vs {info2.size}")
        is_ok = False
    
    if not np.allclose(info1.spacing, info2.spacing):
        print_test(False, f"Spacing differs: {info1.spacing} vs {info2.spacing}")
        is_ok = False
    
    if not np.allclose(info1.origin, info2.origin):
        print_test(False, f"Origin differs: {info1.origin} vs {info2.origin}")
        is_ok = False
    
    if not np.all(info1.dir == info2.dir):
        print_test(False, f"Direction differs: {info1.dir} vs {info2.dir}")
        is_ok = False
    
    print_test(is_ok, f"Images have same size/spacing/origin/dir: {is_ok}")
    print(f"  Image1: size={info1.size}, spacing={info1.spacing}, origin={info1.origin}")
    print(f"  Image2: size={info2.size}, spacing={info2.spacing}, origin={info2.origin}")
    
    return is_ok


def assert_img_sum_logic(s1, s2, sum_tolerance, threshold=0):
    """Check if image sums are within tolerance"""
    if s1 < threshold and s2 < threshold:
        diff = 0
        b = True
    elif s2 == 0:
        diff = 100
        b = False
    else:
        diff = np.fabs(s1 - s2) / s2 * 100
        b = diff < sum_tolerance
    
    print_test(b, f"Image sums: {s1:.2f} vs {s2:.2f}, diff={diff:.2f}% (tol={sum_tolerance:.2f}%)")
    return b


def plot_img_axis(ax, img, label, axis='z'):
    """Plot image profile along specified axis"""
    data = itk.GetArrayFromImage(img)
    
    if axis == 'x':
        profile = np.sum(data, axis=(0, 1))
    elif axis == 'y':
        profile = np.sum(data, axis=(0, 2))
    else:  # z
        profile = np.sum(data, axis=(1, 2))
    
    ax.plot(profile, label=label)
    ax.legend()
    ax.set_xlabel(f'{axis} axis')
    ax.set_ylabel('Sum')
    ax.grid(True)
    
    return profile


def assert_images(ref_filename, test_filename, stats_events=None, tolerance=0,
                 ignore_value_data1=None, ignore_value_data2=None,
                 apply_ignore_mask_to_sum_check=True, axis='z',
                 fig_name=None, sum_tolerance=5, test_sad=True):
    """Compare two images with various metrics"""
    
    print(f"\nComparing images:")
    print(f"  Reference: {ref_filename}")
    print(f"  Test:      {test_filename}")
    
    # Read images
    img1 = itk.imread(str(ref_filename))
    img2 = itk.imread(str(test_filename))
    
    info1 = get_info_from_image(img1)
    info2 = get_info_from_image(img2)
    
    # Check properties
    is_ok = assert_images_properties(info1, info2)
    
    # Get pixel data
    data1 = itk.GetArrayViewFromImage(img1).ravel()
    data2 = itk.GetArrayViewFromImage(img2).ravel()
    
    # Apply ignore masks if specified
    if ignore_value_data1 is None and ignore_value_data2 is None:
        d1 = data1
        d2 = data2
    else:
        if ignore_value_data1 is not None and ignore_value_data2 is not None:
            mask = np.logical_or(data1 != ignore_value_data1, data2 != ignore_value_data2)
        elif ignore_value_data1 is not None:
            mask = data1 != ignore_value_data1
        else:
            mask = data2 != ignore_value_data2
        d1 = data1[mask]
        d2 = data2[mask]
    
    # Check sums
    if apply_ignore_mask_to_sum_check:
        s1, s2 = np.sum(d1), np.sum(d2)
    else:
        s1, s2 = np.sum(data1), np.sum(data2)
    
    b = assert_img_sum_logic(s1, s2, sum_tolerance)
    is_ok = is_ok and b
    
    # Normalize by events if provided
    if stats_events is not None:
        d1 = d1 / stats_events
        d2 = d2 / stats_events
    
    # Normalize by sum
    s = np.sum(d2)
    if s != 0:
        d1 = d1 / s
        d2 = d2 / s
    
    # Sum of absolute differences
    if test_sad:
        sad = np.fabs(d1 - d2).sum() * 100
        b = sad < tolerance
        non_zero = len(data2[data2 != 0])
        total = len(data2.ravel())
        print_test(b, f"SAD: {sad:.2f}% (tol={tolerance:.2f}%) on {non_zero}/{total} voxels")
        is_ok = is_ok and b
    
    # Create comparison plot
    if fig_name:
        _, ax = plt.subplots(ncols=1, nrows=1, figsize=(12, 6))
        plot_img_axis(ax, img1, 'reference', axis)
        plot_img_axis(ax, img2, 'test', axis)
        ax.set_title(f'Profile comparison along {axis} axis')
        plt.tight_layout()
        print(f"  Saving plot: {fig_name}")
        plt.savefig(fig_name)
        plt.close()
    
    return is_ok


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
    """Main verification function"""
    
    # Setup paths
    script_dir = Path(__file__).parent
    ref_path = script_dir / "test008_dose_actor_ref"
    test_path = script_dir / "test008_dose_actor_stat"
    
    print("="*70)
    print("GATE 9 Test008 Dose Actor - Post-Processing Verification")
    print("="*70)
    
    # Check paths exist
    if not ref_path.exists():
        print(f"ERROR: Reference path not found: {ref_path}")
        sys.exit(1)
    
    if not test_path.exists():
        print(f"ERROR: Test path not found: {test_path}")
        sys.exit(1)
    
    is_ok = True
    
    # Read statistics using the correct GATE 9 parser
    stats_ref = read_gate9_stat_file(ref_path / "stat008_dose_actor.txt")
    stats_test = read_gate9_stat_file(test_path / "stat008_dose_actor.txt")
    
    if not stats_ref or not stats_test:
        print("ERROR: Failed to read statistics files")
        sys.exit(1)
    
    
    is_ok = assert_stats(stats_test, stats_ref, tolerance=0.11) and is_ok
    
    # Compare EDEP images
    print("\n" + "="*70)
    print("EDEP IMAGE COMPARISON")
    print("="*70)
    
    is_ok = assert_images(
        ref_path / "test008_dose_actor-Edep.mhd",
        test_path / "test008_dose_actor-Edep.mhd",
        stats_events=stats_test.events,
        tolerance=13,
        ignore_value_data2=0,
        sum_tolerance=2.5,
        fig_name=test_path / "edep_comparison.png"
    ) and is_ok
    
    # Compare Squared images
    print("\n" + "="*70)
    print("EDEP-SQUARED IMAGE COMPARISON")
    print("="*70)
    
    is_ok = assert_images(
        ref_path / "test008_dose_actor-Edep-Squared.mhd",
        test_path / "test008_dose_actor-Edep-Squared.mhd",
        stats_events=stats_test.events,
        tolerance=8,
        ignore_value_data2=0,
        sum_tolerance=1.5,
        fig_name=test_path / "edep_squared_comparison.png"
    ) and is_ok
    
    # Compare Uncertainty images
    print("\n" + "="*70)
    print("EDEP-UNCERTAINTY IMAGE COMPARISON")
    print("="*70)
    
    is_ok = assert_images(
        ref_path / "test008_dose_actor-Edep-Uncertainty.mhd",
        test_path / "test008_dose_actor-Edep-Uncertainty.mhd",
        stats_events=stats_test.events,
        tolerance=30,
        ignore_value_data2=0,
        sum_tolerance=3,
        fig_name=test_path / "edep_uncertainty_comparison.png"
    ) and is_ok
    
    # Final result
    test_ok(is_ok)


if __name__ == "__main__":
    main()