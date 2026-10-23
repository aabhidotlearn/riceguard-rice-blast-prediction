# Reproducible minority-class sample run

Executed on the public Mendeley rice-leaf image sample described in the root
`DATA_ATTRIBUTION.md`. For this demonstration, 400 images per disease class were
sampled across filename families, then Blast was intentionally reduced to 120
images to make a minority class. The production-style training command defaults
to the whole dataset and does not force this artificial imbalance.

```text
Sample before split: Bacterialblight 400, Blast 120, Brownspot 400, Tungro 400
Filename-family holdout: Bacterialblight 67, Blast 23, Brownspot 88, Tungro 80
Training before SMOTE: Bacterialblight 333, Blast 97, Brownspot 312, Tungro 320
Training after SMOTE:  Bacterialblight 333, Blast 333, Brownspot 333, Tungro 333
Holdout accuracy: 0.996
Holdout macro F1: 0.993
```

SMOTE ran after the grouped train/holdout split, so synthetic examples were only
created from the training rows. The single holdout error was one Bacterialblight
image predicted as Blast. This small, same-source evaluation is only a pipeline
check: the dataset lacks healthy leaves and a high score here does not establish
performance on new fields, cameras, cultivars, or lighting.
