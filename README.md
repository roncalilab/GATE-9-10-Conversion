# GATE-9-10-Conversion

This repository contains GATE simulation scripts for both GATE 9 and GATE 10 (OpenGate), including test cases and conversion mappings between versions.

In case of questions, please contact us: https://roncalilab.engineering.ucdavis.edu

## Folder Structure

```
scripts/
├── Gate10/
├── Gate9/
├── Gate9_Testcases/
└── Gate9_10_Mappings/
```

---

## Gate10

**Purpose:** GATE 10 (OpenGate) Python scripts

**How to contribute:**
- Create a folder of your python (.py) scripts for a particular project.
- Upload your folder directly to this folder
- Scripts should use the OpenGate Python API

**Example:**
```
Gate10/Example1
├── my_simulation.py
├── dose_calculation.py
└── particle_source.py
```

---

## Gate9

**Purpose:** GATE 9 macro (.mac) files and related scripts

**How to contribute:**
- Create a folder of your macros (.mac) scripts for a particular project.
- Upload your project folder directly to this folder
- Include any associated material databases or configuration files

**Example:**
```
Gate9/Example1
├── my_simulation.mac
├── GateMaterials.db
└── physics_config.mac
```

---

## Gate9_Testcases

**Purpose:** Converted GATE 9 test cases from GATE 10 tests

**How to contribute:**
1. Create a subfolder with **the exact same name** as the corresponding GATE 10 test case
2. Upload your converted GATE 9 scripts to that subfolder
3. Include validation/post-processing scripts if applicable

**Naming Convention:**
- Folder name must match the GATE 10 test case name
- Example: If GATE 10 test is `test003_g4_materials`, create folder `test003_g4_materials`

**Example:**
```
Gate9_Testcases/
├── test003_g4_materials/
│   ├── test_material.mac
│   ├── validate_materials.py
│   └── CustomMaterials.db
├── test005_proton_beam/
│   ├── proton_beam.mac
│   └── validate_output.py
└── test010_dose_actor/
    ├── dose_simulation.mac
    └── analyze_dose.py
```

**Requirements:**
- Folder name = GATE 10 test case name
- Include all necessary files (.mac, .db, validation scripts)
- Add a README in the subfolder if the conversion has specific notes

---

## Gate9_10_Mappings

**Purpose:** Side-by-side comparisons of equivalent GATE 9 and GATE 10 implementations

**How to contribute:**
1. Create a main folder for your example (e.g., `Example1`)
2. Inside that folder, create two subfolders:
   - `Gate10-Example1/` - Contains GATE 10 version
   - `Gate9-Example1/` - Contains GATE 9 version
3. Upload corresponding scripts to each subfolder

**Folder Structure Template:**
```
Gate9_10_Mappings/
└── ExampleName/
    ├── Gate10-ExampleName/
    │   └── [GATE 10 scripts here]
    └── Gate9-ExampleName/
        └── [GATE 9 scripts here]
```

**Example:**
```
Gate9_10_Mappings/
├── MaterialTest/
│   ├── Gate10-MaterialTest/
│   │   └── test_materials.py
│   └── Gate9-MaterialTest/
│       ├── test_materials.mac
│       └── validate_materials.py
├── ProtonTherapy/
│   ├── Gate10-ProtonTherapy/
│   │   └── proton_therapy.py
│   └── Gate9-ProtonTherapy/
│       ├── proton_therapy.mac
│       └── analysis.py
└── PETScanner/
    ├── Gate10-PETScanner/
    │   └── pet_simulation.py
    └── Gate9-PETScanner/
        ├── pet_scanner.mac
        └── coincidence_sorter.mac
```

**Requirements:**
- Main folder name describes the example
- Two subfolders: `Gate10-[ExampleName]/` and `Gate9-[ExampleName]/`
- Scripts in both folders should implement the same functionality
- Consider adding a README in the main folder explaining the mapping if required.

---

## Contribution Guidelines

1. **Follow the folder structure** as described above
2. **Include comments** in your scripts explaining key sections
3. **Add validation scripts** when possible (especially for test cases)
4. **Document dependencies** (required physics lists, materials, etc.)
5. **Test your scripts** before uploading
6. **Use clear naming conventions** for files and folders
7. **Tell us if/ how you would like to be acknowledged**
