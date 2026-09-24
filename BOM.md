# Bill of Materials (BOM)

Print data for all 3D-printed parts is included in `stl/` of this repository. Only purchased components and the raw materials required for printing are listed below.

## Robotic forearm

| Component | Specification / Notes | Quantity |
| --- | --- | ---: |
| Servo motor (muscle actuator) | Dynamixel XL330-M288-T, Robotis; 12 mm radius pulley | 22 |
| Ligament | Chain-knitted polyethylene (PE) wire, φ0.23 mm | - |
| Tendon | Polyethylene (PE) wire, φ0.3 mm | - |
| Tendon sheath | PTFE tube, outer diameter 2 mm | - |
| Fingertip skin (outer layer) | Shore E30 silicone, 1 mm thickness (Young's modulus 22.1 kPa) | - |
| Fingertip subcutaneous tissue (inner layer) | Expanded silicone | - |

## 3D-printed parts and printing materials

See `stl/` (STL) and `cad/` (STEP, F3D) for the print data.

| Part group | Process / Material | Data |
| --- | --- | --- |
| Bones (carpals, metacarpals, phalanges, radius, ulna) and fingernails | Stereolithography (SLA) / White Resin, Formlabs | `stl/bone_*.stl` |
| Triangular fibrocartilage disc (TFCC) | Fused deposition modeling (FDM) / TPU | `stl/soft_tissue_tfcc.stl` |
| Fingertip molds | Stereolithography (SLA) / White Resin, Formlabs | `stl/mold_*.stl` |
| Base plate, motor tower and pulleys | Fused deposition modeling (FDM) / PolyLite ASA, Polymaker | `stl/tower_*.stl` |
| Assembly jigs (ligament length, carpal bones) | Fused deposition modeling (FDM) / PolyLite ASA, Polymaker | `stl/jig_*.stl` |
| Experimental jigs (humerus fixation, hand fixation, force gauge) | Fused deposition modeling (FDM) / PolyLite ASA, Polymaker | `stl/exp_*.stl` |

## Control system

| Component | Specification / Notes | Quantity |
| --- | --- | ---: |
| Microcontroller board | Teensy 4.1 (SDIO and I/O count required) | 1 |
| Dynamixel interface board | TTL2DXIF (BTE094B), Best Technology; TTL / RS-485 conversion. Connected to Teensy Serial2 (pins 7–8), direction control pin 2 | 1 |
| microSD card | 32 GB (used via the built-in SDIO of Teensy 4.1) | 1 |
| DC-DC converter (5 V supply) | AE-MYMGK00506ERSR-5V0 (5 V / 6 A DC-DC converter module kit based on MYMGK00506ERSR), Akizuki Denshi. Supplies the XL330-M288-T actuators. Sold as an assembly kit | 4 |