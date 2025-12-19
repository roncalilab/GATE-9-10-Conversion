#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import pathlib

# ================ Parameters =================
output_folder = "output"
output_name = "pet_test"
low_e_threshold = 200.0  # keV
activity = 20000.0  # Bq
simulation_time = 5.0  # seconds

# Create output directory
pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)

# ============================================
# Create the simulation
# ============================================
sim = gate.Simulation()

# Units
m = gate.g4_units.m
mm = gate.g4_units.mm
cm = gate.g4_units.cm
keV = gate.g4_units.keV
MeV = gate.g4_units.MeV
Bq = gate.g4_units.Bq
deg = gate.g4_units.deg
s = gate.g4_units.s

# ============================================
# Main options
# ============================================
sim.g4_verbose = False
sim.g4_verbose_level = 1
sim.visu = False
sim.random_seed = "auto"
sim.random_engine = "MersenneTwister"

# World
sim.world.size = [800 * mm, 800 * mm, 2000 * mm]
sim.world.material = "G4_AIR"

# ============================================
# Physics
# ============================================
# Use QGSP_BERT with Livermore EM physics (polarized)
sim.physics_manager.physics_list_name = "QGSP_BERT_LIV"
sim.physics_manager.enable_decay = True
sim.physics_manager.global_production_cuts.all = 1 * mm

# Set user limits for tracking
sim.physics_manager.set_user_limits_particles = ["gamma", "e-", "e+"]

# ============================================
# Geometry
# ============================================

# Cylindrical PET scanner
cylindrical_pet = sim.add_volume("Tubs", "cylindricalPET")
cylindrical_pet.mother = sim.world.name
cylindrical_pet.material = "G4_AIR"
cylindrical_pet.rmin = 320 * mm
cylindrical_pet.rmax = 390 * mm
cylindrical_pet.dz = 1620 * mm / 2  # half-length
cylindrical_pet.color = [0, 0, 0, 1]

# Bundle (rsector) - repeated in a ring
bundle = sim.add_volume("Box", "bundle")
bundle.mother = cylindrical_pet.name
bundle.material = "G4_AIR"
bundle.size = [16 * mm, 60 * mm, 1620 * mm]
bundle.color = [1, 0, 0, 1]

# Generate translations and rotations for ring repetition (125 bundles)
bundle_translations, bundle_rotations = gate.geometry.utility.get_circular_repetition(
    number_of_repetitions=125,
    first_translation=[0, 350 * mm, 0],
    axis=[0, 0, 1]
)
bundle.translation = bundle_translations
bundle.rotation = bundle_rotations

# Fibre (crystal/module) - repeated in cubic array (4x15x1)
fibre = sim.add_volume("Box", "fibre")
fibre.mother = bundle.name
fibre.material = "G4_PLASTIC_SC_VINYLTOLUENE"  # EJ230 equivalent
fibre.size = [4 * mm, 4 * mm, 1600 * mm]
fibre.color = [0, 0, 1, 1]

# Generate translations for cubic array repetition
fibre_translations = gate.geometry.utility.get_grid_repetition(
    size=[4, 15, 1],
    spacing=[4 * mm, 4 * mm, 0]
)
fibre.translation = fibre_translations

# ============================================
# Source - Point source emitting 511 keV gammas
# ============================================
source = sim.add_source("GenericSource", "simplegamma")
source.particle = "gamma"
source.energy.type = "mono"
source.energy.mono = 0.511 * MeV
source.position.type = "box"
source.position.radius = 0.5 * mm
source.position.translation = [0, 0, 0]
source.position.size = [1 * mm, 1 * mm, 1 * mm]  # cylinder height = 1 mm (halfz * 2)
source.direction.type = "iso"
source.activity = activity * Bq

# ============================================
# Digitizer
# ============================================

# Create hits collection
hits_collection = sim.add_actor("DigitizerHitsCollectionActor", "Hits")
hits_collection.attached_to = fibre.name
hits_collection.authorize_repeated_volumes = True  # Allow collection from repeated volumes
hits_collection.attributes = [
    "TotalEnergyDeposit",
    "PostPosition",
    "PrePosition",
    "GlobalTime",
    "PreStepUniqueVolumeID",  # Required for repeated volumes
    "PostStepUniqueVolumeID",
]

# Singles digitizer chain
singles = sim.add_actor("DigitizerAdderActor", "Singles")
singles.attached_to = hits_collection.attached_to
singles.input_digi_collection = "Hits"
singles.policy = "EnergyWinnerPosition"
singles.authorize_repeated_volumes = True
singles.group_volume = bundle.name  # Readout depth 1
singles.output_filename = f"{output_folder}/{output_name}_singles.root"

# Energy window
energy_window = sim.add_actor("DigitizerEnergyWindowsActor", "EnergyWindow")
energy_window.attached_to = singles.attached_to
energy_window.input_digi_collection = "Singles"
energy_window.authorize_repeated_volumes = True
energy_window.channels = [
    {
        "name": "energy_window",
        "min": low_e_threshold * keV,
        "max": 1000 * keV,
    }
]
energy_window.output_filename = f"{output_folder}/{output_name}.root"

# ============================================
# Statistics and output
# ============================================
stats = sim.add_actor("SimulationStatisticsActor", "stats")
stats.track_types_flag = True
stats.output = f"{output_folder}/{output_name}.digit_summary.txt"

# ============================================
# Timing
# ============================================
sim.run_timing_intervals = [[0, simulation_time * s]]

# ============================================
# Run simulation
# ============================================
print("Starting GATE 10 PET simulation...")
print(f"Activity: {activity} Bq")
print(f"Simulation time: {simulation_time} s")
print(f"Output: {output_folder}/{output_name}.root")

sim.run()

# Print statistics
print(stats)
print("Simulation completed successfully!")