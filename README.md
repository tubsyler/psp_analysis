# PSP (REG1a) in critically ill children: revision analyses

Analysis code for the revised manuscript on pancreatic stone protein (PSP/REG1a) in the paediatric intensive care unit (PICU), submitted to the *European Journal of Pediatrics*.

All analyses were re-run from scratch in Python on the corrected dataset. This repository contains the code only. The de-identified dataset is available from the corresponding author on reasonable request, within the limits of the ethics approval.

## Contents

| File | Description |
|---|---|
| `psp_analiz.ipynb` | Notebook with all analysis steps (00 to 17). Run the cells from top to bottom. |
| `psp_analiz.py` | The same code as a single script (`python psp_analiz.py`). |
| `requirements.txt` | Package versions used. |
| `LICENSE` | MIT licence. |
| `data_dictionary.md` | Description of every column of the patient and control sheets. |

## How to run

1. Open the notebook in Google Colab or Jupyter.
2. Place `psp_data.xlsx` (sheets `Analiz_Tablosu`, `Kontroller`) in the working directory. For step 14, also place the raw plate file `Sunred_REG1a_240606.xlsx`. Without it, step 14 is skipped.
3. Run the cells in order. Each step prints its result and writes CSV and PNG files to `outputs/<step>/`. The last cell zips the outputs.

Random seed: 42 (bootstrap and cross-validation). Package versions are listed in `requirements.txt`. Python 3.13.18 was used.

## Steps and the reviewer comments they address

| Step | Content | Reviewer comment |
|---|---|---|
| 00 | Data checks: missing values, ranges, logical consistency, duplicate PSP values | General |
| 01 | Normality (Shapiro-Wilk, raw and log2) | Minor 7 |
| 02 | Descriptive statistics (Table 1): septic vs non-septic, died vs survived, patients vs controls | General, Comment 7 |
| 03 | PSP and age: scatter plot, Spearman correlation, age-adjusted logistic models, likelihood-ratio test | Comment 3 |
| 04 | Pairwise comparisons of PSP, PCT and CRP (Mann-Whitney; Kruskal-Wallis with Bonferroni for three groups) | Minor 2 |
| 05 | AUCs with 95% CI (DeLong and bootstrap), ROC curves. Circular indicators (Phoenix, PELOD-2 for sepsis) are flagged. Smallest AUC detectable with 80% power (Hanley-McNeil). | Comments 4 and 5 |
| 06 | Formal test of AUC differences (DeLong and paired bootstrap) | Comment 6 |
| 07 | Kidney function and PSP: correlations, CRRT, sensitivity analysis | Comment 8 |
| 08 | Logistic regression (log2-transformed, univariable and age-adjusted), including BUN | Comment 9 |
| 09 | Youden thresholds, sensitivity, specificity (with Wilson 95% CIs), PPV, NPV, bootstrap optimism correction | Comment 10 |
| 10 | Sensitivity analysis for six samples above the highest standard (as measured, capped at 4 ng/mL, excluded) | Comment 1 |
| 11 | PICU stay in survivors and PICU-free days at day 28 | Minor 4 |
| 12 | Time from sampling to death; sampling time by source of admission | Comment 2 |
| 13 | Culture sites and organism groups | Minor 6 |
| 14 | Plate quality: standard curve fit, back-calculated recovery, samples outside the standard range | Comment 1 |
| 15 | Manuscript figures 1 to 3 (flow diagram, ROC curves, PSP and age). Screening counts in the flow diagram are entered by hand. | Comment 3, Minor 1 |
| 16 | Admission diagnoses of non-septic patients | STARD item 21b |
| 17 | Saves Python and package versions to requirements.txt | Reproducibility |
## Assay quality (step 14)

The PSP concentrations were measured with a research-use-only sandwich ELISA kit (Human REG1a ELISA Kit, catalogue no. 201-12-2476, lot 202605). All samples were run once, in single wells, on one plate, without dilution.

- Standards: 250 to 4000 pg/mL (five points).
- Standard recovery: 98.4 to 103.3% (quadratic fit through the origin) and 98.8 to 101.9% (four-parameter logistic fit).
- 70 of 76 samples were within the standard range. Six samples were above the highest standard and were extrapolated. Three of these exceeded the upper limit stated by the manufacturer (7200 pg/mL).
- No independent validation data (coefficients of variation, spike-recovery, linearity) were available from the manufacturer. Stored sera were no longer available for re-measurement. These are limitations discussed in the manuscript.

## Notes and known limitations

- Organism groups in step 13 were assigned by keyword matching on free text and were checked by hand.
- The partial correlation in step 07 is computed on ranks, and its p value uses n-2 degrees of freedom instead of n-3. The difference is small.
- Thresholds in step 09 were derived from the same data. They were not pre-specified. Predictive values depend on the prevalence in this cohort (sepsis 73%, mortality 38%).
- Apparent AUCs of the models in step 03 are optimistic. The cross-validated AUC is reported next to them.

## AI-assisted coding

The code was written with the assistance of Claude (Anthropic) at the authors' request. The authors ran the code, checked the outputs and take responsibility for the analyses.

## Citation

Manuscript under revision at European Journal of Pediatrics.

## Licence

MIT.
