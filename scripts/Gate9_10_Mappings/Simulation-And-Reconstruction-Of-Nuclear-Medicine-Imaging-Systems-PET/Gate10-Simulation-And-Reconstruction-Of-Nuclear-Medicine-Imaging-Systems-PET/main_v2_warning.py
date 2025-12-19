#!/usr/bin/env python3
"""
GATE 10 Main Simulation Script
Translated from GATE 9 main.mac
"""

import opengate as gate
from pathlib import Path
import time

def main():
    sim = gate.Simulation()
    script_dir = Path(__file__).parent.resolve()
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    # sim.keep_all_actor_outputs = True
    # sim.store_all_actor_outputs = True
    sim.output_dir = output_dir
    # =========================================================================
    # (from verbose.mac)
    # =========================================================================
    sim.g4_verbose = True
    sim.g4_verbose_level = 0
    sim.visu = False
    sim.random_seed = "auto"
    
    sim.volume_manager.add_material_database(
        "data/GateMaterials.db"
    )
    
    # GEOMETRY - WORLD (from world.mac)
    # =========================================================================
    world = sim.world
    world.size = [1.5 * gate.g4_units.m, 1.5 * gate.g4_units.m, 1.5 * gate.g4_units.m]
    world.material = "G4_AIR"
    
    # =========================================================================
    # GEOMETRY - CYLINDRICAL PHANTOM (from cylindrical_phantom.mac)
    # =========================================================================
    phantom = sim.add_volume("Tubs", "phantom")
    phantom.mother = "world"
    phantom.material = "G4_WATER"
    phantom.rmin = 0.0 * gate.g4_units.cm
    phantom.rmax = 10.0 * gate.g4_units.cm
    phantom.dz = 70.0 * gate.g4_units.cm / 2.0
    phantom.color = [0, 0, 1, 1]
    
    # =========================================================================
    # GEOMETRY - PET SCANNER (from pet_head.mac)
    # =========================================================================
    # Cylindrical PET main volume
    cylindricalPET = sim.add_volume("Tubs", "cylindricalPET")
    cylindricalPET.mother = "world"
    cylindricalPET.material = "G4_AIR"
    cylindricalPET.rmin = 39.9 * gate.g4_units.cm
    cylindricalPET.rmax = 52.0 * gate.g4_units.cm
    cylindricalPET.dz = 40.2 * gate.g4_units.cm / 2.0
    cylindricalPET.translation = [0, 0, 0]
    cylindricalPET.color = [1, 1, 1, 1]  # white
    
    # Head (rsector)
    head = sim.add_volume("Box", "head")
    head.mother = "cylindricalPET"
    head.material = "G4_AIR"
    head.size = [8.0 * gate.g4_units.cm, 32.0 * gate.g4_units.cm, 40.2 * gate.g4_units.cm]
    head.translation = [44.0 * gate.g4_units.cm, 0, 0]
    
    # Module
    module = sim.add_volume("Box", "module")
    module.mother = "head"
    module.material = "G4_AIR"
    module.size = [3.0 * gate.g4_units.cm, 8.0 * gate.g4_units.cm, 10.0 * gate.g4_units.cm]
    module.translation = [2.5 * gate.g4_units.cm, 0, 0]
    
    # Block (submodule)
    block = sim.add_volume("Box", "block")
    block.mother = "module"
    block.material = "G4_AIR"
    block.size = [30 * gate.g4_units.mm, 15.9 * gate.g4_units.mm, 19.9 * gate.g4_units.mm]
    block.translation = [0, 0, 0]
    
    # Crystal
    crystal = sim.add_volume("Box", "crystal")
    crystal.mother = "block"
    crystal.material = "G4_AIR"
    crystal.size = [3.0 * gate.g4_units.cm, 3.0 * gate.g4_units.mm, 3.8 * gate.g4_units.mm]
    crystal.translation = [0, 0, 0]
    
    
    # LSO layer (sensitive detector)
    LSO = sim.add_volume("Box", "LSO")
    LSO.mother = "crystal"
    LSO.material = "LSO"  # G4's LSO material
    LSO.size = [3.0 * gate.g4_units.cm, 3.0 * gate.g4_units.mm, 3.8 * gate.g4_units.mm]
    LSO.translation = [0, 0, 0]
    LSO.color = [0, 1, 0, 1]  # green
    
    # =========================================================================
    # REPEATERS - Must be defined after all volumes
    # =========================================================================
    # Repeaters - Crystal (5x5 array)
    size_crystal = [1, 5, 5]
    tr_crystal = [0, 3.2 * gate.g4_units.mm, 4.0 * gate.g4_units.mm]
    rpt_crystal = gate.geometry.volumes.RepeatParametrisedVolume(
        name=f"repeat_{crystal.name}",
        repeated_volume=crystal
    )
    sim.volume_manager.add_volume(rpt_crystal)
    rpt_crystal.linear_repeat = size_crystal
    rpt_crystal.translation = tr_crystal
    rpt_crystal.start = [-(x - 1) * y / 2.0 for x, y in zip(size_crystal, tr_crystal)]
    
    # Repeaters - Block (5x5 array)
    size_block = [1, 5, 5]
    tr_block = [0, 1.6 * gate.g4_units.cm, 2.0 * gate.g4_units.cm]
    rpt_block = gate.geometry.volumes.RepeatParametrisedVolume(
        name=f"repeat_{block.name}",
        repeated_volume=block
    )
    sim.volume_manager.add_volume(rpt_block)
    rpt_block.linear_repeat = size_block
    rpt_block.translation = tr_block
    rpt_block.start = [-(x - 1) * y / 2.0 for x, y in zip(size_block, tr_block)]
    
    # Repeaters - Module (4x4 array)
    size_module = [1, 4, 4]
    tr_module = [0, 8.0 * gate.g4_units.cm, 10.0 * gate.g4_units.cm]
    rpt_module = gate.geometry.volumes.RepeatParametrisedVolume(
        name=f"repeat_{module.name}",
        repeated_volume=module
    )
    sim.volume_manager.add_volume(rpt_module)
    rpt_module.linear_repeat = size_module
    rpt_module.translation = tr_module
    rpt_module.start = [-(x - 1) * y / 2.0 for x, y in zip(size_module, tr_module)]
    
    # Repeaters - Head (ring with 8 sectors)
    # Repeaters – Head (ring with 8 sectors)
    translations_head, rotations_head = gate.geometry.utility.get_circular_repetition(
        number_of_repetitions=8,
        first_translation=[44.0 * gate.g4_units.cm, 0, 0],
        axis=[0, 0, 1]
    )
    head.translation = translations_head
    head.rotation = rotations_head

    
    
    # =========================================================================
    # PHYSICS (from physics.mac)
    # =========================================================================
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    
    # Set production cuts by region
    sim.physics_manager.set_production_cut(
        particle_name="gamma",
        volume_name="world",
        value=1 * gate.g4_units.km
    )
    sim.physics_manager.set_production_cut(
        particle_name="electron",
        volume_name="world",
        value=1 * gate.g4_units.km
    )
    sim.physics_manager.set_production_cut(
        particle_name="positron",
        volume_name="world",
        value=1 * gate.g4_units.km
    )
    
    # Phantom cuts
    sim.physics_manager.set_production_cut(
        particle_name="gamma",
        volume_name="phantom",
        value=1.0 * gate.g4_units.mm
    )
    sim.physics_manager.set_production_cut(
        particle_name="electron",
        volume_name="phantom",
        value=1.0 * gate.g4_units.mm
    )
    sim.physics_manager.set_production_cut(
        particle_name="positron",
        volume_name="phantom",
        value=1.0 * gate.g4_units.mm
    )
    
    # LSO cuts
    sim.physics_manager.set_production_cut(
        particle_name="gamma",
        volume_name="LSO",
        value=1.0 * gate.g4_units.mm
    )
    sim.physics_manager.set_production_cut(
        particle_name="electron",
        volume_name="LSO",
        value=1.0 * gate.g4_units.mm
    )
    sim.physics_manager.set_production_cut(
        particle_name="positron",
        volume_name="LSO",
        value=1.0 * gate.g4_units.mm
    )
    
    # =========================================================================
    # SOURCES (from sources.mac - using the two-source version)
    # =========================================================================
    # F18 Line Source - using box approximation for cylindrical source
    source_f18 = sim.add_source("GenericSource", "F18LineSource")
    source_f18.particle = "e+"
    source_f18.activity = 100 * gate.g4_units.Bq
    source_f18.half_life = 6586.2 * gate.g4_units.s
    source_f18.energy.type = "F18"
    source_f18.position.type = "box"  # Using box as workaround for cylinder issue
    source_f18.position.size = [1.0 * gate.g4_units.mm, 1.0 * gate.g4_units.mm, 68.0 * gate.g4_units.cm]
    source_f18.position.translation = [0, -2.0 * gate.g4_units.cm, 0]
    source_f18.direction.type = "iso"
    
    # O15 Line Source - using box approximation for cylindrical source
    source_o15 = sim.add_source("GenericSource", "O15LineSource")
    source_o15.particle = "e+"
    source_o15.activity = 100 * gate.g4_units.Bq
    source_o15.half_life = 122.24 * gate.g4_units.s
    source_o15.energy.type = "O15"
    source_o15.position.type = "box"  # Using box as workaround for cylinder issue
    source_o15.position.size = [1.0 * gate.g4_units.mm, 1.0 * gate.g4_units.mm, 68.0 * gate.g4_units.cm]
    source_o15.position.translation = [0, 2.0 * gate.g4_units.cm, 0]
    source_o15.direction.type = "iso"
    

    # print("\n=== Gate Volumes in Simulation ===")
    # for name, vol in sim.volume_manager.volumes.items():
    #     print(f"{name:20s} | material={vol.material} | mother={vol.mother}")

    stats_actor = sim.add_actor("SimulationStatisticsActor", "Stats")
    stats_actor.output_filename = "stat.txt"
    # =========================================================================
    # DIGITIZER (from pet_digitizer.mac)
    # =========================================================================
    # Hits collection
    hits = sim.add_actor("DigitizerHitsCollectionActor", "Hits")
    hits.attached_to = ["LSO"]
    hits.authorize_repeated_volumes = True
    hits.output_filename = "hits.root"
    hits.write_to_disk = True
    hits.attributes = [
        "TotalEnergyDeposit",
        "PostPosition",
        "PrePosition",
        "GlobalTime",
        "KineticEnergy",
        "ProcessDefinedStep",
        "TrackVolumeName",
        "TrackID",
        "ParentID",
        "EventID", 
        "PreStepUniqueVolumeID",
        "PostStepUniqueVolumeID"
    ]
    
    # Singles digitizer chain (Adder - groups hits at readout depth)
    singles = sim.add_actor("DigitizerAdderActor", "Singles")
    singles.input_digi_collection = "Hits"
    singles.policy = "EnergyWeightedCentroidPosition"
    singles.output_filename = "singles.root"
    singles.write_to_disk = True
    
    # Energy resolution (Gaussian blurring)
    energy_blur = sim.add_actor("DigitizerBlurringActor", "EnergyBlur")
    energy_blur.input_digi_collection = singles.name
    energy_blur.blur_attribute = "TotalEnergyDeposit"
    energy_blur.blur_fwhm = 0.26
    energy_blur.blur_reference_value = 511 * gate.g4_units.keV
    energy_blur.output_filename = "energy_blur.root"
    energy_blur.write_to_disk = True
    
    # Energy window
    energy_window = sim.add_actor("DigitizerEnergyWindowsActor", "EnergyWindow")
    energy_window.input_digi_collection = energy_blur.name
    energy_window.channels = [
        {
            "name": "main_window",
            "min": 350 * gate.g4_units.keV,
            "max": 650 * gate.g4_units.keV
        }
    ]
    energy_window.authorize_repeated_volumes = True
    energy_window.output_filename = "singles_filtered.root"
    energy_window.write_to_disk = True
    # =========================================================================
    # ACTORS - OUTPUT (from output.mac)
    # =========================================================================
    # Statistics actor

    
    # =========================================================================
    # RANDOM ENGINE
    # =========================================================================
    sim.random_engine = "MersenneTwister"
    sim.random_seed = "auto"
    
    
    # =========================================================================
    # TIMING
    # =========================================================================
    sim.run_timing_intervals = [
        [0, 60 * gate.g4_units.s],
        [60 * gate.g4_units.s, 120 * gate.g4_units.s]
    ]
    
    # =========================================================================
    # RUN SIMULATION
    # =========================================================================
    sim.run()
    print("Output paths:")
    for actor in sim.actor_manager.actors.values():
        try:
            print(f"{actor.name}: {actor.get_output_path()}")
        except Exception:
            pass

    print("\n" + "="*80)
    print("Simulation completed")
    print("="*80)
    import os
    print("Output directory contents:")
    print(os.listdir("output"))
    return sim

if __name__ == "__main__":
    sim = main()