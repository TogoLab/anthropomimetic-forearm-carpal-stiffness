# Anthropomimetic Soft Robotic Forearm with Independently Articulated Carpal Bones

🌍 English (this page)  
📘 [Japanese](./README_JP.md)

---

## Overview

![Anthropomimetic Soft Robotic Forearm](overview.png)

This repository provides open-hardware data for an **anatomically accurate anthropomimetic soft robotic forearm** composed of eight independently movable carpal bones interconnected by ligaments, 22 actuated muscles, and compliant fingertips, together with the CAD data of the assembly and experimental jigs, the muscle control firmware, and the wrist-stiffness / carpal-motion analysis code. The purpose of this repository is to improve the reproducibility of the following paper.

Yoshinobu Obata, Yinlai Jiang, Hiroshi Yokoi, and Shunta Togo.  
“Anthropomimetic Soft Robotic Forearm with Independently Articulated Carpal Bones Enabling Human-Like Adaptive Stiffness Modulability.”  
arXiv:TODO [cs.RO], 2026.  
https://doi.org/TODO

---

## Repository Structure

```
analysis/   Wrist stiffness ellipse fitting and carpal motion analysis code with measured data, Python
firmware/   Muscle (Dynamixel) control firmware for the robotic forearm, PlatformIO
cad/        CAD files of the forearm and the experimental/assembly jigs (STEP, F3D)
stl/        STL files for 3D printing (bones, fingertip molds, TFCC, motor tower and pulleys, assembly and experimental jigs)
media/      Supplementary video
licenses/   Full text of the applicable licenses (CC BY 4.0, CC BY-SA 2.1 JP)
```

---

## Bill of Materials (BOM)

- [Bill of Materials (BOM)](./BOM.md)

---

## License

Multiple licenses apply to different parts of this repository.  
The bone models and fingertip molds are derived from **BodyParts3D** (Life Science Integrated Database Center) and are distributed under **CC BY-SA 2.1 JP**; all other materials are original works by the authors and are distributed under **CC BY 4.0**.  
Please make sure to check the license associated with each file before use.  
For details, see `LICENSE.txt` and the contents of the `licenses/` directory.

---

## Notes and Disclaimer

- This data is provided for educational and research purposes.
- Use, modification, and redistribution are performed at your own risk.
- The authors and affiliated institutions assume no responsibility for any damage or loss resulting from the use of this repository.

---

## Author and Contact

Shunta Togo  
Associate Professor  
Department of Mechanical and Intelligent Systems Engineering  
Graduate School of Informatics and Engineering  
The University of Electro-Communications  

- [ResearchMap](https://researchmap.jp/shuntatogo?lang=en)  
- [Togo Laboratory](http://www.hi.mce.uec.ac.jp/togolab/)  
- [X (Twitter)](https://twitter.com/togo_lab/)  
- [Instagram](https://www.instagram.com/togolab_uec/)  
- [YouTube](https://www.youtube.com/channel/UC10spcvW8-pCTLKy5rrDHyw)

For questions or bug reports, please use GitHub Issues or contact:  
s.togo[at]uec.ac.jp

Support for educational and research activities at the Togo Laboratory is also welcome.  
- https://www.uec.ac.jp/kikin/archives/fund/togolab

---

## Related Publications

* Yoshinobu Obata, Yinlai Jiang, Hiroshi Yokoi and Shunta Togo, "Design of anthropomimetic robotic wrist joint and forearm," 2023 IEEE International Conference on Systems, Man, and Cybernetics (SMC), pp. 1766–1771, Oahu, Hawaii, USA, Oct. 1–4, 2023.
