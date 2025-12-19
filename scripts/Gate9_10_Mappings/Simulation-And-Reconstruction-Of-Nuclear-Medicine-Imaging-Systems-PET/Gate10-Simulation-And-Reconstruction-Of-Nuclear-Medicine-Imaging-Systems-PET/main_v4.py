import opengate as gate
from pathlib import Path
import os

def main():
    sim = gate.Simulation()
    
    # Setup output
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    sim.output_dir = output_dir
    
    # Minimal world
    sim.world.size = [1 * gate.g4_units.m] * 3
    sim.world.material = "G4_AIR"
    
    # Simple detector volume
    detector = sim.add_volume("Box", "detector")
    detector.mother = "world"
    detector.material = "G4_AIR"
    detector.size = [10 * gate.g4_units.cm] * 3
    
    # THIS LINE CAUSES THE BUG - just creating the object (comment the line below to see the expected behavior)
    # rpt = gate.geometry.volumes.RepeatParametrisedVolume(
    #      name="repeat_detector",
    #      repeated_volume=detector
    # )
    # No need to add it or set any attributes - bug occurs anyway
    
    # Simple physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    
    # Simple source
    source = sim.add_source("GenericSource", "test_source")
    source.particle = "gamma"
    source.energy.mono = 511 * gate.g4_units.keV
    source.activity = 100000 * gate.g4_units.Bq
    source.direction.type = "iso"
    
    # Statistics actor (produces stat.txt - this persists)
    stats = sim.add_actor("SimulationStatisticsActor", "Stats")
    stats.output_filename = "stat.txt"
    
    # Actor that produces ROOT file
    hits = sim.add_actor("DigitizerHitsCollectionActor", "Hits")
    hits.attached_to = ["detector"]
    hits.output_filename = "test_hits.root"
    hits.write_to_disk = True
    hits.attributes = ["TotalEnergyDeposit", "GlobalTime"]
    
    # Run
    sim.run_timing_intervals = [[0, 1 * gate.g4_units.s]]
    sim.run()
    
    # Check output
    print("Output files:", os.listdir("output"))
    # BUG: stat.txt persists but test_hits.root will be missing

if __name__ == "__main__":
    main()