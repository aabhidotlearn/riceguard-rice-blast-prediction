# Sample image and training data attribution

The four sample images shipped in `frontend/public/samples/` and the bundled
educational classifier come from **Rice Leaf Disease Image Samples** by Prabira
Kumar Sethy, Mendeley Data, Version 1, DOI: <https://doi.org/10.17632/fwcj7stb8r.1>.
The dataset page identifies the files as available under the Creative Commons
Attribution 4.0 International license (CC BY 4.0):
<https://data.mendeley.com/datasets/fwcj7stb8r/1>.

Sample file mapping:

- `bacterial-blight.jpg` — `Bacterialblight/BACTERAILBLIGHT4_126.jpg`
- `blast.jpg` — `Blast/BLAST4_114.jpg`
- `brown-spot.jpg` — `Brownspot/BROWNSPOT2_065.jpg`
- `tungro.jpg` — `Tungro/TUNGRO2_085.jpg`

The source dataset has 5,932 images across four disease classes: bacterial blight
(1,584), blast (1,440), brown spot (1,600), and tungro (1,308). It has no healthy
class. The included model is a demonstration of an image-feature MLP and SMOTE
workflow. Its results do not establish field performance or diagnosis quality.
