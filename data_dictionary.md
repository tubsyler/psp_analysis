# Data dictionary

Columns of the `Analiz_Tablosu` sheet (patients, n=56) and `Kontroller` sheet (controls, n=20). Descriptions are in Turkish, as in the source file.

| Column | Description | Unit | Coding / note |
|---|---|---|---|
| satir_no | Hasta sırası (1–56). Plaka sırası ve ana Excel satırıyla aynı (ana Excel satırı = satir_no + 1). | sayı |  |
| yas_ay | Yaş, doğum tarihi ve YBÜ yatış tarihinden hesaplandı | ay |  |
| yas_yil | yas_ay / 12 | yıl |  |
| cinsiyet_0K_1E | Cinsiyet |  | 0 kadın, 1 erkek |
| yatis_tani_kodu | YBÜ yatış tanısı grubu |  | 1 sol., 2 nöro, 3 travma, 4 enfeksiyon, 5 GİS, 6 postop, 7 hemato-onko, 8 intoksikasyon, 9 renal |
| altta_yatan_var_ana_excel | Ana Excel'deki altta yatan hastalık işareti (düzeltme öncesi) |  | 0 yok, 1 var. Analizde kullanılmaz. |
| altta_yatan_tur_ham | Ana Excel'deki altta yatan hastalık türü (karışık kod ve metin) |  | Analizde kullanılmaz, altta_yatan_grup kullanılır |
| PICU_yatis_gun | YBÜ yatış süresi (çıkış tarihi − yatış tarihi) | gün |  |
| yatistan_ornekleme_gun | YBÜ yatışından PSP örnek tarihine kadar geçen süre | gün | 0 = yatış günü |
| ornekten_olume_gun | PSP örneğinden ölüme kadar süre | gün | Yalnızca ölenlerde dolu |
| sonuc_kodu_0exitus_1taburcu_2devam | Ana Excel sonuç kodu (güncel) |  | 0 exitus, 1 taburcu (sağ). 2 devam kalmadı. |
| sonlanim_analiz_0exitus_1sag | Analizde kullanılan sonlanım |  | 0 exitus, 1 sağ |
| IMV | İnvaziv mekanik ventilasyon |  | 0 yok, 1 var |
| ECMO | ECMO kullanımı |  | 0 yok, 1 var |
| CRRT | CRRT kullanımı |  | 0 yok, 1 var |
| plazmaferez | Plazmaferez |  | 0 yok, 1 var |
| CVK | Santral venöz kateter |  | 0 yok, 1 var |
| kan_tx | Kan transfüzyonu |  | 0 yok, 1 var |
| PSS | Phoenix Sepsis Skoru (kullandığınız hesaplama aracı) | puan | ≥2 = sepsis |
| PRISM3 | PRISM-III | puan | PSP gününde hesaplandı |
| PELOD2 | PELOD-2 | puan | PSP gününde hesaplandı |
| CODS | CODS puanı (ana Excel) | puan | Tanım ana Excel'den, teyit edin |
| OF | Organ yetmezliği var mı |  | 0 yok, 1 var |
| organ_yetmezlik_sayisi | Yetmezlik olan organ sayısı | sayı |  |
| WBC | Beyaz küre | /µL |  |
| NEU | Nötrofil | /µL |  |
| HB | Hemoglobin | g/dL |  |
| PLT | Trombosit | ×10³/µL |  |
| BUN | BUN | mg/dL |  |
| Krea | Kreatinin | mg/dL | K sütunuyla karıştırılmıştı, düzeltildi |
| AST | AST | U/L |  |
| ALT | ALT | U/L |  |
| TBIL | Total bilirubin | mg/dL |  |
| Laktat | Laktat | mmol/L |  |
| Albümin | Albümin | g/dL |  |
| UA | UA (ana Excel sütunu) |  | Birim ve tanım teyit edilecek (ürik asit olabilir) |
| NA | Sodyum | mmol/L |  |
| K | Potasyum (ana Excel'den yeniden alındı) | mmol/L | Önceki tabloda kreatininin kopyasıydı |
| CA | Kalsiyum | mg/dL |  |
| INR | INR |  |  |
| CRP | CRP | mg/L | Birim teyit edilecek (şokta düşük değerler var) |
| PCT | Prokalsitonin | ng/mL | 100 iki hastada, ölçüm tavanı olabilir |
| PSP_ng_mL | Pankreatik taş proteini (Sunred REG1a ELISA) | ng/mL | Plakada 4 ng/mL üstü 6 hasta ekstrapole |
| sepsis_PSS | Sepsis (Phoenix, PSS ≥ 2) |  | 0 yok, 1 var |
| inotrop | Vazoaktif/inotrop ihtiyacı |  | 0 yok, 1 var |
| septik_sok_duzeltilmis | Septik şok (Phoenix: sepsis + kardiyovasküler puan; inotrop veya laktat > 5) |  | 0 yok, 1 var |
| septik_sok_PSS_arac | Septik şok, hesaplama aracının çıktısı |  | Araç 2 hastada laktat > 5 durumunu şok saymadı |
| ab_ornekten_once_basladi | Antibiyotik PSP örneğinden önce başladı mı |  | 0 hayır, 1 evet |
| PICU_kaynakli_vekil_ornek_gt2gun | YBÜ kaynaklı vekil: örnekleme YBÜ yatışından > 2 gün sonra |  | 0 hayır, 1 evet |
| kaynak_1toplum_2hastane | Geliş kaynağı |  | 1 toplum, 2 hastane/YBÜ |
| sepsis_suphesi | Sepsis şüphesi (ana Excel) |  | 0 yok, 1 var |
| kanitlanmis_sepsis | Kanıtlanmış sepsis (ana Excel) |  | 0 yok, 1 var |
| kulturde_ureme | Herhangi bir kültürde üreme |  | 0 yok, 1 var |
| kan_kulturu_ureme | Kan kültüründe üreme |  | 0 yok, 1 var |
| kateter_kulturu_ureme | Kateter kültüründe üreme |  | 0 yok, 1 var |
| tak_kulturu_ureme | Trakeal aspirat kültüründe üreme |  | 0 yok, 1 var. Kısaltma ana Excel'de "TAK" |
| baska_kultur_ureme | Başka kültürde üreme |  | 0 yok, 1 var |
| mikroorganizma | Üreyen mikroorganizma (metin) |  | 0 = üreme yok |
| PSP_ust_standart_ustu | PSP en yüksek standardın (4 ng/mL) üstünde, ekstrapole |  | 0 hayır, 1 evet |
| yatis_tanisi_yazili | Yazılı yatış tanısı (sizin doldurduğunuz form) |  |  |
| altta_yatan_yazili | Yazılı altta yatan hastalık (sizin doldurduğunuz form) |  |  |
| bobrek_hastaligi | Kronik böbrek hastalığı |  | 0 yok, 1 var (1 hasta) |
| pankreas_hastaligi | Pankreas hastalığı |  | Dışlama kriteri, hepsi 0 |
| gis_hastaligi | GİS hastalığı |  | Dışlama kriteri, hepsi 0 |
| altta_yatan_var | Kronik/altta yatan hastalık var mı (yazılı tanıya göre, analizde kullanılan) |  | 0 yok, 1 var (44/56) |
| altta_yatan_grup | Altta yatan hastalık grubu |  | Yok, Nörolojik, Kardiyak, Hemato-onkolojik, İmmünolojik, Genetik, Romatolojik, Renal |
