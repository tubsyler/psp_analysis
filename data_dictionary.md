# Data dictionary

Columns of the `Analiz_Tablosu` sheet (patients, n=56) and the `Kontroller` sheet (controls, n=20). Column and sheet names are in Turkish, as in the source file, because the code reads them by name.

## `Analiz_Tablosu` (patients)

| Column | Description | Unit | Coding / note |
|---|---|---|---|
| satir_no | Patient order (1–56). Same as plate order and main Excel row (main Excel row = satir_no + 1). | number |  |
| yas_ay | Age, calculated from date of birth and PICU admission date | months |  |
| yas_yil | yas_ay / 12 | years |  |
| cinsiyet_0K_1E | Sex |  | 0 female, 1 male |
| yatis_tani_kodu | PICU admission diagnosis group |  | 1 respiratory, 2 neurological, 3 trauma, 4 infection, 5 gastrointestinal, 6 postoperative, 7 hemato-oncological, 8 intoxication, 9 renal |
| altta_yatan_var_ana_excel | Underlying disease flag in the main Excel file (before correction) |  | 0 no, 1 yes. Not used in the analysis. |
| altta_yatan_tur_ham | Underlying disease type in the main Excel file (mixed codes and text) |  | Not used; altta_yatan_grup is used instead |
| PICU_yatis_gun | PICU length of stay (discharge date − admission date) | days |  |
| yatistan_ornekleme_gun | Time from PICU admission to PSP sampling date | days | 0 = day of admission |
| ornekten_olume_gun | Time from PSP sampling to death | days | Filled only for patients who died |
| sonuc_kodu_0exitus_1taburcu_2devam | Outcome code in the main Excel file (updated) |  | 0 died, 1 discharged alive. No patient is coded 2 (still admitted). |
| sonlanim_analiz_0exitus_1sag | Outcome used in the analysis |  | 0 died, 1 survived |
| IMV | Invasive mechanical ventilation |  | 0 no, 1 yes |
| ECMO | Extracorporeal membrane oxygenation |  | 0 no, 1 yes |
| CRRT | Continuous renal replacement therapy |  | 0 no, 1 yes |
| plazmaferez | Plasmapheresis |  | 0 no, 1 yes |
| CVK | Central venous catheter |  | 0 no, 1 yes |
| kan_tx | Blood transfusion |  | 0 no, 1 yes |
| PSS | Phoenix Sepsis Score (calculated with MDCalc) | points | ≥2 = sepsis |
| PRISM3 | PRISM-III | points | Calculated on the day of PSP sampling |
| PELOD2 | PELOD-2 | points | Calculated on the day of PSP sampling |
| CODS | CODS score (main Excel file). Not used in the analysis. | points | Definition as in the main Excel file |
| WBC | White blood cell count | /µL |  |
| NEU | Neutrophil count | /µL |  |
| HB | Haemoglobin | g/dL |  |
| PLT | Platelet count | ×10³/µL |  |
| BUN | Blood urea nitrogen | mg/dL |  |
| Krea | Creatinine | mg/dL | Had been mixed up with the K column; corrected |
| AST | Aspartate aminotransferase | U/L |  |
| ALT | Alanine aminotransferase | U/L |  |
| TBIL | Total bilirubin | mg/dL |  |
| Laktat | Lactate | mmol/L |  |
| Albümin | Albumin | g/dL |  |
| UA | Uric acid | mg/dL | Not used in the analysis. |
| NA | Sodium | mmol/L |  |
| K | Potassium (re-extracted from the main Excel file) | mmol/L | Was a copy of creatinine in the previous table |
| CA | Calcium | mg/dL |  |
| INR | International normalized ratio |  |  |
| CRP | C-reactive protein | mg/L |  |
| PCT | Procalcitonin | ng/mL | Value of 100 in two patients; may be the assay ceiling |
| PSP_ng_mL | Pancreatic stone protein (Sunred REG1a ELISA) | ng/mL | 6 patients above 4 ng/mL on the plate were extrapolated |
| sepsis_PSS | Sepsis (Phoenix, PSS ≥ 2) |  | 0 no, 1 yes |
| inotrop | Need for vasoactive/inotropic drugs |  | 0 no, 1 yes |
| septik_sok_duzeltilmis | Septic shock (Phoenix: sepsis + cardiovascular points; inotrope or lactate > 5) |  | 0 no, 1 yes |
| septik_sok_PSS_arac | Septic shock, output of the calculation tool |  | The tool did not count lactate > 5 as shock in 2 patients |
| ab_ornekten_once_basladi | Antibiotics started before PSP sampling |  | 0 no, 1 yes |
| PICU_kaynakli_vekil_ornek_gt2gun | Proxy for PICU-acquired: sampled more than 2 days after PICU admission |  | 0 no, 1 yes |
| kaynak_1toplum_2hastane | Source of admission |  | 1 community, 2 hospital/PICU |
| sepsis_suphesi | Suspected sepsis (main Excel file) |  | 0 no, 1 yes |
| kanitlanmis_sepsis | Proven sepsis (main Excel file) |  | 0 no, 1 yes |
| kulturde_ureme | Growth in any culture |  | 0 no, 1 yes |
| kan_kulturu_ureme | Growth in blood culture |  | 0 no, 1 yes |
| kateter_kulturu_ureme | Growth in catheter culture |  | 0 no, 1 yes |
| tak_kulturu_ureme | Growth in tracheal aspirate culture |  | 0 no, 1 yes. "TAK" is the abbreviation used in the main Excel file |
| baska_kultur_ureme | Growth in another culture |  | 0 no, 1 yes |
| mikroorganizma | Microorganism grown (free text, in Turkish) |  | 0 = no growth |
| PSP_ust_standart_ustu | PSP above the highest standard (4 ng/mL), extrapolated |  | 0 no, 1 yes |
| yatis_tanisi_yazili | Admission diagnosis (free text, in Turkish) |  |  |
| altta_yatan_yazili | Underlying disease (free text, in Turkish) |  |  |
| bobrek_hastaligi | Chronic kidney disease |  | 0 no, 1 yes (1 patient) |
| pankreas_hastaligi | Pancreatic disease |  | Exclusion criterion; all 0 |
| gis_hastaligi | Gastrointestinal disease |  | Exclusion criterion; all 0 |
| altta_yatan_var | Chronic/underlying disease present (from written diagnosis; used in the analysis) |  | 0 no, 1 yes (44/56) |
| altta_yatan_grup | Underlying disease group |  | Values as stored: Yok (none), Nörolojik (neurological), Kardiyak (cardiac), Hemato-onkolojik (hemato-oncological), İmmünolojik (immunological), Genetik (genetic), Romatolojik (rheumatological), Renal (renal) |

## `Kontroller` (healthy controls)

| Column | Description | Unit | Coding / note |
|---|---|---|---|
| SMP_no_plaka | Sample number on the plate |  |  |
| cinsiyet_0K_1E | Sex |  | 0 female, 1 male |
| yas_yil | Age | years |  |
| PSP_ng_mL_form | PSP value on the data form. Used in the analysis. | ng/mL |  |
| PSP_ng_mL_plaka | PSP value calculated from the plate reading | ng/mL | For checking only |
| fark_yuzde | Difference between form and plate values: (form − plate) / plate × 100 | % | Excel formula |
