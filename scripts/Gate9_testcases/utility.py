#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE 9 Verification Utilities
Standalone module for image and statistics comparison
"""

import numpy as np
import itk
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os
from typing import Optional


# -------------------------------------------------------------------------
#  Basic Classes and Utility Functions
# -------------------------------------------------------------------------

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
        self.raw_data = {}


def print_test(ok, message):
    """Print test result with OK/FAILED prefix"""
    status = "✓" if ok else "✗"
    color = "\033[92m" if ok else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {message}")


def test_ok(is_ok: bool):
    """Print final test result summary"""
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


# -------------------------------------------------------------------------
#  GATE 9 Statistics Comparison
# -------------------------------------------------------------------------

def read_gate9_stat_file(filename: str) -> Optional[Stats]:
    """Read GATE 9 SimulationStatisticActor output file"""
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

            line = line[2:].strip()
            if '=' in line:
                key, value = map(str.strip, line.split('=', 1))
                try:
                    if '.' in value:
                        raw_data[key] = float(value)
                    else:
                        raw_data[key] = int(value)
                except ValueError:
                    raw_data[key] = value

    stats.runs = raw_data.get('NumberOfRun', 0)
    stats.events = raw_data.get('NumberOfEvents', 0)
    stats.tracks = raw_data.get('NumberOfTracks', 0)
    stats.steps = raw_data.get('NumberOfSteps', 0)
    stats.pps = raw_data.get('PPS (Primary per sec)', 0.0)
    stats.tps = raw_data.get('TPS (Track per sec)', 0.0)
    stats.sps = raw_data.get('SPS (Step per sec)', 0.0)
    stats.raw_data = raw_data

    return stats


def assert_stats(stats1: Stats, stats2: Stats, tolerance: float = 0.0) -> bool:
    """Compare two Stats objects"""
    is_ok = True
    print("\n" + "="*70)
    print("STATISTICS COMPARISON")
    print("="*70)

    def rel_diff(v1, v2):
        return (v1 / v2 * 100 - 100) if v2 != 0 else 100

    diffs = {
        'events': rel_diff(stats1.events, stats2.events),
        'tracks': rel_diff(stats1.tracks, stats2.tracks),
        'steps': rel_diff(stats1.steps, stats2.steps),
    }

    # Runs
    b = stats1.runs == stats2.runs
    print_test(b, f"Runs: {stats1.runs} {stats2.runs}")
    is_ok &= b

    # Events
    b = abs(diffs['events']) <= tolerance * 100
    print_test(b, f"Events: {stats1.events} {stats2.events} Δ={diffs['events']:+.2f}% tol={tolerance*100:.1f}%")
    is_ok &= b

    # Tracks
    b = abs(diffs['tracks']) <= tolerance * 100
    print_test(b, f"Tracks: {stats1.tracks} {stats2.tracks} Δ={diffs['tracks']:+.2f}% tol={tolerance*100:.1f}%")
    is_ok &= b

    # Steps
    b = abs(diffs['steps']) <= tolerance * 100
    print_test(b, f"Steps: {stats1.steps} {stats2.steps} Δ={diffs['steps']:+.2f}% tol={tolerance*100:.1f}%")
    is_ok &= b

    return is_ok


# -------------------------------------------------------------------------
#  Image Comparison Functions
# -------------------------------------------------------------------------

def get_info_from_image(img):
    class Info:
        pass
    info = Info()
    info.size = np.array(itk.size(img))
    info.spacing = np.array(img.GetSpacing())
    info.origin = np.array(img.GetOrigin())
    info.dir = np.array(img.GetDirection())
    return info


def assert_images_properties(info1, info2):
    """Compare image size/spacing/origin/direction"""
    is_ok = True
    if not np.all(info1.size == info2.size):
        print_test(False, f"Size differs: {info1.size} vs {info2.size}")
        is_ok = False
    if not np.allclose(info1.spacing, info2.spacing):
        print_test(False, f"Spacing differs: {info1.spacing} vs {info2.spacing}")
        is_ok = False
    if not np.allclose(info1.origin, info2.origin):
        print_test(False, f"Origin differs: {info1.origin} vs {info2.origin}")
        is_ok = False
    if not np.all(info1.dir == info2.dir):
        print_test(False, f"Direction differs.")
        is_ok = False
    return is_ok


def assert_img_sum_logic(s1, s2, sum_tolerance):
    """Check if total sums match within tolerance"""
    if s2 == 0:
        diff = 100
        ok = False
    else:
        diff = np.fabs(s1 - s2) / s2 * 100
        ok = diff < sum_tolerance
    print_test(ok, f"Image sums diff={diff:.2f}% (tol={sum_tolerance:.2f}%)")
    return ok


def plot_img_axis(ax, img, label, axis='z'):
    data = itk.GetArrayFromImage(img)
    if axis == 'x':
        prof = np.sum(data, axis=(0, 1))
    elif axis == 'y':
        prof = np.sum(data, axis=(0, 2))
    else:
        prof = np.sum(data, axis=(1, 2))
    ax.plot(prof, label=label)
    ax.legend()
    ax.set_xlabel(axis)
    ax.grid(True)


def assert_images(ref_filename, test_filename, tolerance=10, sum_tolerance=5, axis='z', 
    ignore_value_data1=None,
    ignore_value_data2=None,
    apply_ignore_mask_to_sum_check=True,
    stats = None,
    test_sad = True,
    fig_name=None):
    """Compare two MHD images"""
    img1 = itk.imread(str(ref_filename))
    img2 = itk.imread(str(test_filename))
    info1 = get_info_from_image(img1)
    info2 = get_info_from_image(img2)

    is_ok = assert_images_properties(info1, info2)
    data1 = itk.GetArrayViewFromImage(img1).ravel()
    data2 = itk.GetArrayViewFromImage(img2).ravel()

    if ignore_value_data1 is None and ignore_value_data2 is None:
        d1 = data1
        d2 = data2
    else:
        if ignore_value_data1 is not None and ignore_value_data2 is not None:
            mask = np.logical_or(
                data1 != ignore_value_data1, data2 != ignore_value_data2
            )
        elif ignore_value_data1 is not None:
            mask = data1 != ignore_value_data1
        else:
            mask = data2 != ignore_value_data2
        d1 = data1[mask]
        d2 = data2[mask]

    # this is a patch to make the function back-compatible
    # because the ignore value was previously applied only after
    # taking the sum and some tests fail after that change
    # apply_ignore_mask_to_sum_check = False recreates the old behavior
    if apply_ignore_mask_to_sum_check is True:
        s1 = np.sum(d1)
        s2 = np.sum(d2)
    else:
        s1 = np.sum(data1)
        s2 = np.sum(data2)

    is_ok &= assert_img_sum_logic(s1, s2, sum_tolerance)

    if stats is not None:
        d1 = d1 / stats.events
        d2 = d2 / stats.events

    # normalize by sum of d1
    s = np.sum(d2)
    d1 = d1 / s
    d2 = d2 / s

    if test_sad:
        # sum of absolute difference (in %)
        sad = np.fabs(d1 - d2).sum() * 100
        b = sad < tolerance
        print_test(
            b,
            f"Image diff computed on {len(data2[data2 != 0])}/{len(data2.ravel())} \n"
            f"SAD (per event/total): {sad:.2f} % "
            f" (tolerance is {tolerance :.2f} %)",
        )
        is_ok = is_ok and b


    # if fig_name:
    #     _, ax = plt.subplots(figsize=(10, 4))
    #     plot_img_axis(ax, img1, 'ref', axis)
    #     plot_img_axis(ax, img2, 'test', axis)
    #     plt.title(Path(ref_filename).stem)
    #     plt.tight_layout()
    #     plt.savefig(fig_name)
    #     plt.close()

    return is_ok
