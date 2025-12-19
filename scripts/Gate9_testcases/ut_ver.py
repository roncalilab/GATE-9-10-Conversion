#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for GATE 9 test008_dose_actor
"""

from pathlib import Path
import utility as util


def main():
    script_dir = Path(__file__).parent
    ref = script_dir / "test020_profiling_ref"
    test = script_dir / "test020_profiling_stat"

    print("=" * 70)
    print("GATE 9 Test008 Dose Actor - Verification")
    print("=" * 70)

    stats_ref = util.read_gate9_stat_file(ref / "stat.txt")
    stats_test = util.read_gate9_stat_file(test / "stat.txt")

    if not stats_ref or not stats_test:
        print("❌ Failed to read stat files")
        return

    ok = util.assert_stats(stats_test, stats_ref, tolerance=0.1)

    ok &= util.assert_images(
        ref / "image-Edep.mhd",
        test / "image-Edep.mhd",
        tolerance=79,
        ignore_value_data2=0,
        apply_ignore_mask_to_sum_check=False,
        stats = stats_test,
        fig_name=test / "Edep_comparison.png"
    )

    # ok &= util.assert_images(
    #     ref / "test008_dose_actor-Edep-Squared.mhd",
    #     test / "test008_dose_actor-Edep-Squared.mhd",
    #     tolerance=8,
    #     sum_tolerance=1.5,
    #     fig_name=test / "Edep_Squared_comparison.png"
    # )

    # ok &= util.assert_images(
    #     ref / "test008_dose_actor-Edep-Uncertainty.mhd",
    #     test / "test008_dose_actor-Edep-Uncertainty.mhd",
    #     tolerance=30,
    #     sum_tolerance=3,
    #     fig_name=test / "Edep_Uncertainty_comparison.png"
    # )

    util.test_ok(ok)


if __name__ == "__main__":
    main()
