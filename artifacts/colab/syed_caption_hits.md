hit_cells=5


===== CELL 32 (markdown) =====
# Stage C: Cross-Modal Read-Out and Caption Baselines

===== CELL 33 (markdown) =====


Stage C investigates the cross-modal transferability of emotional appraisal representations from text to vision within the Visual Language Model (VLM). This stage includes two main parts: Cross-Modal Read-Out and Caption Baselines



===== CELL 38 (markdown) =====
### Caption Baselines (`stage_c_caption`)
This part explores the role of verbalization in the observed cross-modal transfer by introducing caption baselines. It aims to disentangle whether the VLM is processing emotional information inherently from the image's 'shared geometry' or merely through its ability to generate and process textual descriptions of the images.

1.  **Neutral Caption Baseline:** Images are described with neutral captions, and the read-out performance from these captions is compared to the direct image read-out. The goal is to see how much of the image's appraisal information can be explained solely by its basic verbal description.
2.  **Rich Caption Baseline:** More detailed, 'rich' captions are generated for images. By comparing the read-out from these rich captions to the image read-out, the experiment assesses whether even comprehensive verbalization can fully account for the appraisal information present in the image's direct representation.

The findings from the caption baselines indicate that while captions can reproduce a significant portion of the image-based appraisal read-out (e.g., rich captions reproduce ~89% of pleasantness), a statistically significant unique contribution from the image's direct representation remains. This suggests that the VLM extracts emotional appraisal information from visual input that is not fully captured or mediated by explicit linguistic descriptions, hinting at a 'shared-geometry' of appraisal representation across modalities.

===== CELL 39 (code) =====
!python -m src.experiments.stage_c_caption

===== CELL 40 (code) =====
!python -m src.experiments.stage_c_caption --style rich