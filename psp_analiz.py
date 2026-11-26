# PSP (REG1a) revision analyses: all steps in one script (same code as psp_analiz.ipynb)
# Kullanım (Colab): psp_data.xlsx ve bu dosyayı yükleyin, sonra bir hücrede:  !python psp_analiz.py
# Gerekli paketler:  pip install numpy pandas scipy scikit-learn statsmodels openpyxl matplotlib


# ======================================================================
# PSP revizyonu: analizler (adım adım)
#
# **Kullanım:** 1) Sol panelden `psp_data.xlsx` dosyasını yükleyin (Colab'da `/content` içine). 2) Hücreleri yukarıdan aşağı sırayla çalıştırın. Her adımın sonucu hemen altında görünür ve `outputs/` klasörüne yazılır.
#
# Veri anonimdir (HİS, ad ve doğum tarihi yok). Rastgele tohum 42.
# ======================================================================
# Ayarlar: veri dosyası ve çıktı klasörü
INP = "psp_data.xlsx"     # Colab'da yüklenen dosya /content içinde olur. Başka yerdeyse yolunu yazın.
OUT = "outputs"
import os
assert os.path.exists(INP), f"{INP} bulunamadı. Sol panelden yükleyin veya INP yolunu düzeltin."
print("Veri bulundu:", INP)

# ======================================================================
# Ortak fonksiyonlar (veri yükleme, DeLong, bootstrap)
# Bu hücreyi bir kez çalıştırın.
# ======================================================================
import os, sys, warnings
import numpy as np, pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score
warnings.filterwarnings("ignore")
SEED, B = 42, 2000
SERI = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]   # doğrulanmış kategorik palet, slot 1-5

def args():
    return INP, OUT

def outdir(out, name):
    p = os.path.join(out, name); os.makedirs(p, exist_ok=True); return p

def load(path):
    d = pd.read_excel(path, sheet_name="Analiz_Tablosu")
    c = pd.read_excel(path, sheet_name="Kontroller")
    d["ex"] = 1 - d["sonlanim_analiz_0exitus_1sag"]          # 1 = ex
    d["sepsis"] = d["sepsis_PSS"]
    d["PSP"] = d["PSP_ng_mL"]
    d["sok"] = d["septik_sok_duzeltilmis"]
    d["log2psp"] = np.log2(d["PSP"])
    d["log2yas"] = np.log2(d["yas_ay"] + 1)                 # yaş 0 ay olan hasta var, bu yüzden +1
    for v in ("PCT", "CRP", "Laktat", "BUN", "Krea"):
        d["log2" + v.lower()] = np.log2(d[v])
    c = c.rename(columns={"PSP_ng_mL_form": "PSP"})
    c["log2psp"] = np.log2(c["PSP"])
    return d, c

def iqr(x):
    x = pd.Series(x).dropna(); q = np.percentile(x, [25, 50, 75]); return f"{q[1]:.2f} ({q[0]:.2f}-{q[2]:.2f})"

def p_fmt(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"

# ---------- DeLong (Sun & Xu 2014, hızlı sürüm) ----------
def _midrank(x):
    j = np.argsort(x); z = x[j]; n = len(x); t = np.zeros(n); i = 0
    while i < n:
        k = i
        while k < n and z[k] == z[i]: k += 1
        t[i:k] = 0.5 * (i + k - 1) + 1; i = k
    r = np.empty(n); r[j] = t; return r

def delong(y, X):
    """y: 0/1, X: (n, k) tahminler. AUC'ler (k,) ve kovaryans (k, k) döner."""
    y = np.asarray(y); X = np.asarray(X, float)
    pos, neg = X[y == 1], X[y == 0]; m, n = len(pos), len(neg); k = X.shape[1]
    tx = np.empty((m, k)); ty = np.empty((n, k)); tz = np.empty((m + n, k))
    for r in range(k):
        tx[:, r] = _midrank(pos[:, r]); ty[:, r] = _midrank(neg[:, r]); tz[:, r] = _midrank(np.r_[pos[:, r], neg[:, r]])
    aucs = tz[:m].sum(axis=0) / m / n - (m + 1.0) / 2.0 / n
    v01 = (tz[:m] - tx) / n; v10 = 1.0 - (tz[m:] - ty) / m
    cov = np.cov(v01.T).reshape(k, k) / m + np.cov(v10.T).reshape(k, k) / n
    return aucs, cov

def delong_ci(y, x, alpha=0.05):
    a, cov = delong(y, np.asarray(x).reshape(-1, 1)); se = np.sqrt(cov[0, 0]); z = stats.norm.ppf(1 - alpha / 2)
    return a[0], max(0, a[0] - z * se), min(1, a[0] + z * se)

def delong_test(y, x1, x2):
    """İki AUC arasındaki fark, %95 GA ve iki yönlü p."""
    a, cov = delong(y, np.c_[x1, x2]); diff = a[0] - a[1]; var = cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]
    se = np.sqrt(var); z = diff / se if se > 0 else 0
    return diff, diff - 1.96 * se, diff + 1.96 * se, 2 * stats.norm.sf(abs(z))

def boot_auc_ci(y, x, B=B, seed=SEED):
    rng = np.random.default_rng(seed); y = np.asarray(y); x = np.asarray(x, float); r = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max(): continue
        r.append(roc_auc_score(y[i], x[i]))
    return np.percentile(r, [2.5, 97.5])

def boot_auc_diff(y, x1, x2, B=B, seed=SEED):
    rng = np.random.default_rng(seed); y = np.asarray(y); x1 = np.asarray(x1, float); x2 = np.asarray(x2, float); r = []
    for _ in range(B):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max(): continue
        r.append(roc_auc_score(y[i], x1[i]) - roc_auc_score(y[i], x2[i]))
    return np.percentile(r, [2.5, 97.5])

# ---------- ortak sonlanımlar ----------
def kume(d):
    """Analiz kümeleri: (ad, y, maske)"""
    return [("Sepsis tanısı (tüm hasta)", d["sepsis"], np.ones(len(d), bool)),
            ("Ölüm (tüm hasta)", d["ex"], np.ones(len(d), bool)),
            ("Ölüm (yalnız septik)", d["ex"], (d["sepsis"] == 1).values)]

# ======================================================================
# Adım 00: veri kontrol
#
# 00 - Veri kontrolü: eksik değer, aralık, mantık tutarlılığı, tekrar eden satırlar.
# Çıktı: outputs/00_veri_kontrol/kontrol_raporu.csv
# ======================================================================
import numpy as np, pandas as pd
inp, out = args(); o = outdir(out, "00_veri_kontrol"); d, c = load(inp)
rapor = []
def ekle(kontrol, sonuc, ayrinti=""): rapor.append([kontrol, "TAMAM" if sonuc else "KONTROL ET", ayrinti])

ekle("Hasta sayısı = 56", len(d) == 56, str(len(d)))
ekle("Kontrol sayısı = 20", len(c) == 20, str(len(c)))
ekle("satir_no benzersiz ve 1..56", d.satir_no.tolist() == list(range(1, 57)))
miss = d.drop(columns=["ornekten_olume_gun"]).isna().sum(); miss = miss[miss > 0]
ekle("Eksik değer yok (ornekten_olume_gun hariç)", len(miss) == 0, miss.to_dict())
ekle("ornekten_olume_gun yalnız ölenlerde dolu", ((d.ex == 1) == d.ornekten_olume_gun.notna()).all())
ekle("sepsis_PSS = (PSS ≥ 2)", ((d.PSS >= 2).astype(int) == d.sepsis_PSS).all())
ekle("Septik şok sepsis olmadan yok", ((d.septik_sok_duzeltilmis == 1) & (d.sepsis_PSS == 0)).sum() == 0)
ekle("Örnekleme günü ≤ YBÜ yatış süresi", (d.yatistan_ornekleme_gun <= d.PICU_yatis_gun).all())
ekle("Geliş kaynağı = toplum ise örnekleme günü ≤ 2", d.loc[d.kaynak_1toplum_2hastane == 1, "yatistan_ornekleme_gun"].le(2).all())
ekle("Kültür sütunları tutarlı (kulturde_ureme ≥ kan/kateter/tak/başka)", (d.kulturde_ureme >= d[["kan_kulturu_ureme", "kateter_kulturu_ureme", "tak_kulturu_ureme", "baska_kultur_ureme"]].max(axis=1)).all())
ekle("Pankreas ve GİS hastalığı yok (dışlama kriteri)", (d.pankreas_hastaligi.sum() + d.gis_hastaligi.sum()) == 0)
ekle("İkili sütunlar yalnız 0/1", all(set(d[v].unique()) <= {0, 1} for v in ["cinsiyet_0K_1E", "IMV", "ECMO", "CRRT", "plazmaferez", "CVK", "kan_tx", "inotrop", "ex", "sepsis_PSS"]))
# fizyolojik aralıklar
ARALIK = {"yas_ay": (0, 228), "HB": (3, 20), "PLT": (5, 1500), "Krea": (0.05, 10), "K": (2, 8), "NA": (110, 180), "CA": (5, 14), "INR": (0.7, 10), "Albümin": (1, 6), "Laktat": (0.3, 30), "PCT": (0, 100), "CRP": (0, 500), "PSP_ng_mL": (0.1, 20)}
for v, (lo, hi) in ARALIK.items():
    ok = d[v].between(lo, hi).all(); ekle(f"{v} beklenen aralıkta ({lo}-{hi})", ok, "" if ok else d.loc[~d[v].between(lo, hi), ["satir_no", v]].values.tolist())
ekle("K sütunu kreatininin kopyası değil", not (d.K == d.Krea).all())
ekle("PCT = 100 (ölçüm tavanı olabilir)", True, f"{int((d.PCT == 100).sum())} hasta, satırlar {d.loc[d.PCT == 100, 'satir_no'].tolist()}")
ekle("PSP standart üstü (ekstrapole) hasta", True, f"{int(d.PSP_ust_standart_ustu.sum())} hasta, satırlar {d.loc[d.PSP_ust_standart_ustu == 1, 'satir_no'].tolist()}")
dup = d.PSP[d.PSP.duplicated(keep=False)]
ekle("Aynı PSP değeri olan hastalar (plaka OD'si aynı, rastlantı olarak kabul edildi)", True, d.loc[dup.index, ["satir_no", "PSP"]].values.tolist())
ekle("Kontrol PSP: form ile plaka farkı < %1", c.fark_yuzde.abs().max() < 1, f"en büyük %{c.fark_yuzde.abs().max():.2f}")
r = pd.DataFrame(rapor, columns=["kontrol", "durum", "ayrinti"]); r.to_csv(f"{o}/kontrol_raporu.csv", index=False, encoding="utf-8-sig")
print(r.to_string(index=False))

# ======================================================================
# Adım 01: normallik
#
# 01 - Normallik: Shapiro-Wilk, ham ve log2 dönüştürülmüş, tüm hastalar ve gruplara göre.
# Çıktı: outputs/01_normallik/normallik.csv
# Küçük gruplarda Kolmogorov-Smirnov güçsüz olduğu için Shapiro-Wilk kullanıldı (hakem küçük itiraz 7).
# ======================================================================
import numpy as np, pandas as pd
from scipy.stats import shapiro
inp, out = args(); o = outdir(out, "01_normallik"); d, c = load(inp)
DEG = ["yas_ay", "PICU_yatis_gun", "yatistan_ornekleme_gun", "PRISM3", "PELOD2", "PSS", "WBC", "NEU", "HB", "PLT", "BUN", "Krea", "AST", "ALT", "TBIL", "Laktat", "Albümin", "NA", "K", "CA", "INR", "CRP", "PCT", "PSP"]
satir = []
def sw(x):
    x = pd.Series(x).dropna()
    return shapiro(x) if len(x) >= 3 and x.nunique() > 1 else (np.nan, np.nan)
for v in DEG:
    for grup, mask in (("Tüm hastalar", np.ones(len(d), bool)), ("Septik", d.sepsis == 1), ("Septik olmayan", d.sepsis == 0)):
        x = d.loc[mask, v]; w, p = sw(x)
        xl = np.log2(x[x > 0]) if (x > 0).all() else None; wl, pl = sw(xl) if xl is not None else (np.nan, np.nan)
        satir.append([v, grup, len(x), round(w, 3), p, "evet" if p > 0.05 else "hayır", round(wl, 3) if xl is not None else "", pl if xl is not None else "", ("evet" if pl > 0.05 else "hayır") if xl is not None else ""])
for grup, x in (("Kontrol", c.PSP),):
    w, p = sw(x); wl, pl = sw(np.log2(x)); satir.append(["PSP", grup, len(x), round(w, 3), p, "evet" if p > 0.05 else "hayır", round(wl, 3), pl, "evet" if pl > 0.05 else "hayır"])
r = pd.DataFrame(satir, columns=["degisken", "grup", "n", "W", "p", "normal(p>0.05)", "W_log2", "p_log2", "log2_normal"])
r.to_csv(f"{o}/normallik.csv", index=False, encoding="utf-8-sig")
tum = r[r.grup == "Tüm hastalar"]
print("Tüm hastalarda normal dağılan değişkenler (ham):", tum.loc[tum["normal(p>0.05)"] == "evet", "degisken"].tolist())
print("Log2 sonrası normal:", tum.loc[tum["log2_normal"] == "evet", "degisken"].tolist())
print("PSP:"); print(r[r.degisken == "PSP"][["grup", "n", "W", "p", "p_log2"]].to_string(index=False))

# ======================================================================
# Adım 02: tanimlayici
#
# 02 - Tanımlayıcı istatistik (Tablo 1): septik / septik olmayan ve ölenler / yaşayanlar.
# Sürekli değişken: medyan (IQR), Mann-Whitney. Kategorik: n (%), Fisher (2 sınıf) veya ki-kare.
# Kontroller için yaş ve cinsiyet karşılaştırması da yapılır.
# Çıktı: outputs/02_tanimlayici/
# ======================================================================
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu, fisher_exact, chi2_contingency
inp, out = args(); o = outdir(out, "02_tanimlayici"); d, c = load(inp)
d["yas_yil_"] = d.yas_ay / 12
SUREKLI = [("yas_yil_", "Yaş (yıl)"), ("PICU_yatis_gun", "YBÜ yatış süresi (gün)"), ("yatistan_ornekleme_gun", "Yatıştan örneğe süre (gün)"), ("PRISM3", "PRISM-III"), ("PELOD2", "PELOD-2"), ("PSS", "Phoenix skoru"), ("WBC", "WBC"), ("NEU", "Nötrofil"), ("HB", "Hemoglobin"), ("PLT", "Trombosit"), ("BUN", "BUN"), ("Krea", "Kreatinin"), ("AST", "AST"), ("ALT", "ALT"), ("TBIL", "T. bilirubin"), ("Laktat", "Laktat"), ("Albümin", "Albümin"), ("NA", "Sodyum"), ("K", "Potasyum"), ("CA", "Kalsiyum"), ("INR", "INR"), ("CRP", "CRP"), ("PCT", "PCT"), ("PSP", "PSP (ng/mL)")]
KATEGORIK = [("cinsiyet_0K_1E", "Erkek"), ("altta_yatan_var", "Kronik hastalık var"), ("IMV", "İnvaziv ventilasyon"), ("ECMO", "ECMO"), ("CRRT", "CRRT"), ("plazmaferez", "Plazmaferez"), ("CVK", "Santral kateter"), ("kan_tx", "Kan transfüzyonu"), ("inotrop", "Vazoaktif ilaç"), ("sok", "Septik şok"), ("kaynak_1toplum_2hastane", "Geliş kaynağı hastane/YBÜ"), ("PICU_kaynakli_vekil_ornek_gt2gun", "YBÜ kaynaklı (vekil)"), ("ab_ornekten_once_basladi", "Antibiyotik örnekten önce"), ("kulturde_ureme", "Kültürde üreme"), ("kan_kulturu_ureme", "Kan kültüründe üreme"), ("ex", "Ölüm")]
def tablo(grup_col, etiket):
    g1 = d[d[grup_col] == 1]; g0 = d[d[grup_col] == 0]; sat = []
    sat.append(["n", len(d), len(g1), len(g0), ""])
    for v, ad in SUREKLI:
        p = mannwhitneyu(g1[v], g0[v], alternative="two-sided").pvalue
        sat.append([ad, iqr(d[v]), iqr(g1[v]), iqr(g0[v]), p_fmt(p)])
    for v, ad in KATEGORIK:
        if v == grup_col or (grup_col == "ex" and v == "ex"): continue
        if v == "kaynak_1toplum_2hastane": a = (d[v] == 2).astype(int); a1 = (g1[v] == 2).astype(int); a0 = (g0[v] == 2).astype(int)
        else: a, a1, a0 = d[v], g1[v], g0[v]
        t = [[a1.sum(), len(a1) - a1.sum()], [a0.sum(), len(a0) - a0.sum()]]
        p = fisher_exact(t)[1]
        sat.append([ad, f"{int(a.sum())} ({100*a.mean():.0f}%)", f"{int(a1.sum())} ({100*a1.mean():.0f}%)", f"{int(a0.sum())} ({100*a0.mean():.0f}%)", p_fmt(p)])
    g = pd.crosstab(d["altta_yatan_grup"], d[grup_col]); p = chi2_contingency(g)[1]
    sat.append(["Altta yatan hastalık grubu (ki-kare, beklenen sayılar küçük)", "", "", "", p_fmt(p)])
    return pd.DataFrame(sat, columns=["degisken", "Tüm hastalar", etiket[0], etiket[1], "p"])
t1 = tablo("sepsis", ("Septik", "Septik olmayan")); t1.to_csv(f"{o}/tablo1_septik_vs_septik_olmayan.csv", index=False, encoding="utf-8-sig")
t2 = tablo("ex", ("Ölen", "Yaşayan")); t2.to_csv(f"{o}/tablo1b_ex_vs_sag.csv", index=False, encoding="utf-8-sig")
# kronik hastalık grupları ve geliş kaynağı
d["altta_yatan_grup"].value_counts().rename("n").to_csv(f"{o}/altta_yatan_gruplar.csv", encoding="utf-8-sig")
# kontrol karşılaştırması
k = pd.DataFrame([["n", len(d), len(c), ""],
    ["Yaş (yıl), medyan (IQR)", iqr(d.yas_yil_), iqr(c.yas_yil), p_fmt(mannwhitneyu(d.yas_yil_, c.yas_yil).pvalue)],
    ["Erkek, n (%)", f"{int(d.cinsiyet_0K_1E.sum())} ({100*d.cinsiyet_0K_1E.mean():.0f}%)", f"{int(c.cinsiyet_0K_1E.sum())} ({100*c.cinsiyet_0K_1E.mean():.0f}%)",
     p_fmt(fisher_exact([[d.cinsiyet_0K_1E.sum(), len(d) - d.cinsiyet_0K_1E.sum()], [c.cinsiyet_0K_1E.sum(), len(c) - c.cinsiyet_0K_1E.sum()]])[1])]],
    columns=["degisken", "Hastalar", "Kontroller", "p"])
k.to_csv(f"{o}/hasta_vs_kontrol_yas_cinsiyet.csv", index=False, encoding="utf-8-sig")
print(k.to_string(index=False)); print(); print(t1.to_string(index=False))

# ======================================================================
# Adım 03: psp yas
#
# 03 - PSP ve yaş: saçılım grafiği, Spearman, yaş düzeltmeli lojistik model (hakem yorum 3).
# Çıktı: outputs/03_psp_yas/ (şekil, korelasyon, model_auc, model_OR)
# ======================================================================
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr, chi2
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
inp, out = args(); o = outdir(out, "03_psp_yas"); d, c = load(inp)
d["yas_yil"] = d.yas_ay / 12
# --- korelasyon ---
satir = []
for ad, x, y in (("Tüm hastalar", d.yas_yil, d.PSP), ("Septik", d.yas_yil[d.sepsis == 1], d.PSP[d.sepsis == 1]),
                 ("Septik olmayan", d.yas_yil[d.sepsis == 0], d.PSP[d.sepsis == 0]), ("Kontroller", c.yas_yil, c.PSP)):
    r, p = spearmanr(x, y); satir.append([ad, len(x), round(r, 2), round(p, 4)])
cor = pd.DataFrame(satir, columns=["grup", "n", "spearman_rho", "p"]); cor.to_csv(f"{o}/yas_psp_korelasyon.csv", index=False)
# --- şekil ---
fig, ax = plt.subplots(figsize=(7.2, 5.2), dpi=200)
for ad, alt, renk in (("Septik", d[d.sepsis == 1], SERI[0]), ("Septik olmayan", d[d.sepsis == 0], SERI[1])):
    sag, ex = alt[alt.ex == 0], alt[alt.ex == 1]
    ax.scatter(sag.yas_yil, sag.PSP, s=34, marker="o", facecolor=renk, edgecolor="white", linewidth=1, label=f"{ad} (sağ)")
    if len(ex): ax.scatter(ex.yas_yil, ex.PSP, s=46, marker="X", facecolor=renk, edgecolor="white", linewidth=0.8, label=f"{ad} (ex)")
ax.scatter(c.yas_yil, c.PSP, s=34, marker="s", facecolor=SERI[2], edgecolor="white", linewidth=1, label="Kontrol")
ax.axhline(4.0, color="#8a8984", lw=1, ls=(0, (4, 3))); ax.text(ax.get_xlim()[1], 4.0, " üst standart 4 ng/mL", va="bottom", ha="right", fontsize=8, color="#52514e")
ax.set_yscale("log"); ax.set_xlabel("Yaş (yıl)"); ax.set_ylabel("PSP (ng/mL, log ölçek)")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e4e3df", lw=0.6); ax.set_axisbelow(True)
ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3)
fig.tight_layout(); fig.savefig(f"{o}/sekil_psp_yas.png"); plt.close(fig)
# --- modeller: sonlanım ~ log2(PSP) + log2(yaş+1) ---
def logit(y, X): return sm.Logit(y, sm.add_constant(X)).fit(disp=0)
res, orr = [], []
for ad, y in (("Sepsis tanısı", d.sepsis), ("Ölüm", d.ex)):
    for mad, cols in (("Yalnız yaş", ["log2yas"]), ("Yalnız PSP", ["log2psp"]), ("PSP + yaş", ["log2psp", "log2yas"])):
        X = d[cols]; m = logit(y, X); p_fit = m.predict(sm.add_constant(X))
        cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=SEED); a = []
        for tr, te in cv.split(X, y):
            f = LogisticRegression(C=1e6, max_iter=1000).fit(X.values[tr], y.values[tr]); a.append(roc_auc_score(y.values[te], f.predict_proba(X.values[te])[:, 1]))
        lo, hi = boot_auc_ci(y, p_fit)
        res.append([ad, mad, len(d), int(y.sum()), round(roc_auc_score(y, p_fit), 3), f"{lo:.2f}-{hi:.2f}", round(float(np.mean(a)), 3)])
        ci = np.exp(m.conf_int())
        for v in cols: orr.append([ad, mad, v, round(np.exp(m.params[v]), 2), f"{ci.loc[v, 0]:.2f}-{ci.loc[v, 1]:.2f}", round(m.pvalues[v], 4)])
    m0, m1 = logit(y, d[["log2yas"]]), logit(y, d[["log2psp", "log2yas"]]); lrt = 2 * (m1.llf - m0.llf)
    res.append([ad, "LRT: PSP yaşa ek katkı", "", "", "", f"chi2={lrt:.2f}, p={chi2.sf(lrt, 1):.3f}", ""])
pd.DataFrame(res, columns=["sonlanim", "model", "n", "olay", "AUC_gorunur", "AUC_gorunur_95GA(bootstrap)", "AUC_5kat_capraz_ort"]).to_csv(f"{o}/model_auc.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(orr, columns=["sonlanim", "model", "degisken", "OR(her iki katına)", "GA95", "p"]).to_csv(f"{o}/model_OR.csv", index=False, encoding="utf-8-sig")
print(cor.to_string(index=False)); print(pd.read_csv(f"{o}/model_auc.csv").to_string(index=False))

# ======================================================================
# Adım 04: ikili karsilastirmalar
#
# 04 - İkili karşılaştırmalar (Mann-Whitney U): PSP, PCT, CRP.
# a) septik vs septik olmayan   b) septik vs kontrol   c) septik olmayan vs kontrol   d) ölen vs yaşayan
# e) septik şok var vs yok (yalnız septikler)   f) üç grup: Kruskal-Wallis + ikili karşılaştırmalar (Bonferroni, yalnız burada)
# Çıktı: outputs/04_ikili_karsilastirmalar/
# ======================================================================
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu, kruskal
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
inp, out = args(); o = outdir(out, "04_ikili_karsilastirmalar"); d, c = load(inp)
def mw(a, b): return mannwhitneyu(a, b, alternative="two-sided").pvalue
sat = []
def ekle(ad, deg, a, b, an, bn):
    sat.append([ad, deg, f"{an} (n={len(a)})", iqr(a), f"{bn} (n={len(b)})", iqr(b), mw(a, b)])
for deg in ("PSP", "PCT", "CRP"):
    ekle("Septik vs septik olmayan", deg, d.loc[d.sepsis == 1, deg], d.loc[d.sepsis == 0, deg], "Septik", "Septik olmayan")
    ekle("Ölen vs yaşayan", deg, d.loc[d.ex == 1, deg], d.loc[d.ex == 0, deg], "Ölen", "Yaşayan")
    ekle("Septik şok var vs yok (septik hastalar)", deg, d.loc[(d.sepsis == 1) & (d.sok == 1), deg], d.loc[(d.sepsis == 1) & (d.sok == 0), deg], "Şok var", "Şok yok")
ekle("Septik vs kontrol", "PSP", d.loc[d.sepsis == 1, "PSP"], c.PSP, "Septik", "Kontrol")
ekle("Septik olmayan vs kontrol", "PSP", d.loc[d.sepsis == 0, "PSP"], c.PSP, "Septik olmayan", "Kontrol")
ekle("Tüm hastalar vs kontrol", "PSP", d.PSP, c.PSP, "Hasta", "Kontrol")
r = pd.DataFrame(sat, columns=["karsilastirma", "degisken", "grup1", "grup1_medyan_IQR", "grup2", "grup2_medyan_IQR", "p"])
# üç grup
g = {"Septik": d.loc[d.sepsis == 1, "PSP"], "Septik olmayan": d.loc[d.sepsis == 0, "PSP"], "Kontrol": c.PSP}
kw = kruskal(*g.values()).pvalue; ikili = []
for a, b in (("Septik", "Septik olmayan"), ("Septik", "Kontrol"), ("Septik olmayan", "Kontrol")):
    p = mw(g[a], g[b]); ikili.append([f"{a} vs {b}", p, min(1, 3 * p)])
u = pd.DataFrame(ikili, columns=["karsilastirma", "p_duzeltilmemis", "p_Bonferroni(x3)"])
r["p"] = r["p"].map(p_fmt); r.to_csv(f"{o}/ikili_karsilastirmalar.csv", index=False, encoding="utf-8-sig")
u.to_csv(f"{o}/uc_grup_PSP.csv", index=False, encoding="utf-8-sig")
# şekil: PSP, üç grup
fig, ax = plt.subplots(figsize=(5.6, 4.6), dpi=200); rng = np.random.default_rng(42)
for i, (ad, v) in enumerate(g.items()):
    x = i + rng.uniform(-0.12, 0.12, len(v)); ax.scatter(x, v, s=26, facecolor=SERI[i], edgecolor="white", linewidth=0.8, zorder=3)
    ax.hlines(v.median(), i - 0.25, i + 0.25, color="#0b0b0b", lw=1.6, zorder=4)
ax.set_xticks(range(3)); ax.set_xticklabels([f"{k}\n(n={len(v)})" for k, v in g.items()]); ax.set_yscale("log"); ax.set_ylabel("PSP (ng/mL, log ölçek)")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e4e3df", lw=0.6); ax.set_axisbelow(True); fig.tight_layout(); fig.savefig(f"{o}/sekil_psp_uc_grup.png"); plt.close(fig)
print(r.to_string(index=False)); print(f"\nKruskal-Wallis (3 grup, PSP) p={p_fmt(kw)}"); print(u.round(3).to_string(index=False))

# ======================================================================
# Adım 05: auc ga
#
# 05 - AUC ve %95 güven aralığı: DeLong ve bootstrap. Sepsis tanısı ve ölüm.
# Dairesel göstergeler: sepsis tanımı Phoenix'e dayandığı için PSS ve PELOD-2'nin sepsis AUC'si bağımsız değildir ("dairesel" işaretlenir).
# Çıktı: outputs/05_auc_ga/auc_tablosu.csv ve ROC şekilleri
# ======================================================================
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
inp, out = args(); o = outdir(out, "05_auc_ga"); d, c = load(inp)
MARK = [("PSP", "PSP"), ("PCT", "PCT"), ("CRP", "CRP"), ("PRISM3", "PRISM-III"), ("PELOD2", "PELOD-2"), ("PSS", "Phoenix")]
sat = []
for ad, y, mask in kume(d):
    for v, etk in MARK:
        yy = y[mask].values; x = d.loc[mask, v].values
        a, lo, hi = delong_ci(yy, x); blo, bhi = boot_auc_ci(yy, x)
        dairesel = "dairesel" if ("Sepsis" in ad and v in ("PSS", "PELOD2")) else ""
        sat.append([ad, etk, int(mask.sum()), int(yy.sum()), round(a, 3), f"{lo:.2f}-{hi:.2f}", f"{blo:.2f}-{bhi:.2f}", dairesel])
r = pd.DataFrame(sat, columns=["sonlanim", "gosterge", "n", "olay", "AUC", "GA95_DeLong", "GA95_bootstrap", "not"])
r.to_csv(f"{o}/auc_tablosu.csv", index=False, encoding="utf-8-sig")
# ROC şekilleri
for ad, y, mask, kod, liste in ((kume(d)[0][0], d["sepsis"], np.ones(len(d), bool), "sepsis", ["PSP", "PCT", "CRP", "PRISM3"]),
                                  (kume(d)[1][0], d["ex"], np.ones(len(d), bool), "olum", ["PSP", "PCT", "CRP", "PRISM3", "PELOD2"])):
    fig, ax = plt.subplots(figsize=(5.2, 5.2), dpi=200)
    for i, v in enumerate(liste):
        f, t, _ = roc_curve(y, d[v]); a = roc_auc_score(y, d[v])
        ax.plot(f, t, color=SERI[i], lw=2, ls=("-", "--", "-.", ":", "-")[i], label=f"{dict(MARK)[v]} (AUC {a:.2f})")
    ax.plot([0, 1], [0, 1], color="#8a8984", lw=1); ax.set_xlabel("1 - Özgüllük"); ax.set_ylabel("Duyarlılık"); ax.set_title(ad, fontsize=10)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="lower right"); ax.set_aspect("equal"); fig.tight_layout(); fig.savefig(f"{o}/roc_{kod}.png"); plt.close(fig)
print(r.to_string(index=False))
# Saptanabilir en küçük AUC: %80 güç, iki yönlü alfa 0.05, H0: AUC = 0.5 (Hanley-McNeil)
import numpy as np, pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq
inp, out = args(); o = outdir(out, "05_auc_ga"); d, c = load(inp)
def se_hm(a, n1, n0):
    q1, q2 = a / (2 - a), 2 * a**2 / (1 + a)
    return np.sqrt((a * (1 - a) + (n1 - 1) * (q1 - a**2) + (n0 - 1) * (q2 - a**2)) / (n1 * n0))
sat = []
for ad, y in (("Sepsis tanısı", d.sepsis), ("Ölüm", d.ex)):
    n1, n0 = int((y == 1).sum()), int((y == 0).sum())
    a = brentq(lambda A: A - 0.5 - norm.ppf(0.975) * se_hm(0.5, n1, n0) - norm.ppf(0.80) * se_hm(A, n1, n0), 0.5001, 0.999)
    sat.append([ad, n1, n0, round(a, 3)])
r = pd.DataFrame(sat, columns=["sonlanim", "olay", "olay_yok", "en_kucuk_saptanabilir_AUC"])
r.to_csv(f"{o}/saptanabilir_auc.csv", index=False, encoding="utf-8-sig"); print(r.to_string(index=False))

# ======================================================================
# Adım 06: auc fark
#
# 06 - AUC farklarının formal testi (hakem yorum 6): PSP ile diğer göstergeler.
# DeLong testi (eşleşmiş) ve eşleşmiş bootstrap farkı (%95 GA). Dairesel karşılaştırmalar (sepsis için PSS, PELOD-2) işaretlenir.
# Çıktı: outputs/06_auc_fark/auc_fark.csv
# ======================================================================
import numpy as np, pandas as pd
inp, out = args(); o = outdir(out, "06_auc_fark"); d, c = load(inp)
DIGER = [("PCT", "PCT"), ("CRP", "CRP"), ("PRISM3", "PRISM-III"), ("PELOD2", "PELOD-2"), ("PSS", "Phoenix")]
sat = []
for ad, y, mask in kume(d):
    yy = y[mask].values; psp = d.loc[mask, "PSP"].values
    for v, etk in DIGER:
        x = d.loc[mask, v].values; fark, lo, hi, p = delong_test(yy, psp, x); blo, bhi = boot_auc_diff(yy, psp, x)
        sat.append([ad, f"PSP - {etk}", round(fark, 3), f"{lo:.2f} - {hi:.2f}", f"{blo:.2f} - {bhi:.2f}", p_fmt(p), "dairesel" if ("Sepsis" in ad and v in ("PSS", "PELOD2")) else ""])
r = pd.DataFrame(sat, columns=["sonlanim", "karsilastirma", "AUC_farki(PSP-diger)", "GA95_DeLong", "GA95_bootstrap", "p_DeLong", "not"])
r.to_csv(f"{o}/auc_fark.csv", index=False, encoding="utf-8-sig"); print(r.to_string(index=False))

# ======================================================================
# Adım 07: bobrek psp
#
# 07 - Böbrek fonksiyonu ve PSP (hakem yorum 8): Spearman (PSP-kreatinin, PSP-BUN), CRRT'ye göre PSP, CRRT hariç duyarlılık,
# kronik böbrek hastalığı sayısı, yaştan bağımsız (kısmi, sıralar üzerinden) korelasyon.
# Çıktı: outputs/07_bobrek_psp/
# ======================================================================
import numpy as np, pandas as pd
from scipy.stats import spearmanr, mannwhitneyu, rankdata, pearsonr
from sklearn.metrics import roc_auc_score
inp, out = args(); o = outdir(out, "07_bobrek_psp"); d, c = load(inp)
def kismi(x, y, z):
    rx, ry, rz = (rankdata(v) for v in (x, y, z)); ex = rx - np.polyval(np.polyfit(rz, rx, 1), rz); ey = ry - np.polyval(np.polyfit(rz, ry, 1), rz)
    return pearsonr(ex, ey)
sat = []
for v, ad in (("Krea", "Kreatinin"), ("BUN", "BUN")):
    r, p = spearmanr(d.PSP, d[v]); rk, pk = kismi(d.PSP, d[v], d.yas_ay)
    sat.append([f"PSP - {ad}", len(d), round(r, 2), p_fmt(p), round(rk, 2), p_fmt(pk)])
kor = pd.DataFrame(sat, columns=["iliski", "n", "spearman_rho", "p", "rho_yasa_gore_duzeltilmis", "p_kismi"]); kor.to_csv(f"{o}/korelasyon.csv", index=False, encoding="utf-8-sig")
# CRRT
g1, g0 = d[d.CRRT == 1], d[d.CRRT == 0]
crrt = pd.DataFrame([["CRRT var", len(g1), iqr(g1.PSP)], ["CRRT yok", len(g0), iqr(g0.PSP)], ["Mann-Whitney p (CRRT n=2, yorumlanamaz)", "", p_fmt(mannwhitneyu(g1.PSP, g0.PSP).pvalue)]], columns=["grup", "n", "PSP medyan (IQR)"])
crrt.to_csv(f"{o}/crrt_psp.csv", index=False, encoding="utf-8-sig")
# kronik böbrek hastalığı
bobrek = d.loc[d.bobrek_hastaligi == 1, ["satir_no", "PSP", "Krea", "sepsis", "ex"]]; bobrek.to_csv(f"{o}/kronik_bobrek_hastalari.csv", index=False)
# duyarlılık: CRRT, ECMO ve kronik böbrek hastalığı olanlar hariç
m = ((d.CRRT == 0) & (d.bobrek_hastaligi == 0)).values; sat = []
for ad, y, mk in kume(d):
    for etiket, mm in (("Tüm", mk), ("CRRT ve kronik böbrek hastalığı hariç", mk & m)):
        yy = y[mm].values; x = d.loc[mm, "PSP"].values; a, lo, hi = delong_ci(yy, x)
        sat.append([ad, etiket, int(mm.sum()), int(yy.sum()), round(a, 3), f"{lo:.2f}-{hi:.2f}"])
duy = pd.DataFrame(sat, columns=["sonlanim", "kume", "n", "olay", "PSP_AUC", "GA95"]); duy.to_csv(f"{o}/duyarlilik_crrt_haric.csv", index=False, encoding="utf-8-sig")
print(kor.to_string(index=False)); print(crrt.to_string(index=False)); print(bobrek.to_string(index=False)); print(duy.to_string(index=False))

# ======================================================================
# Adım 08: log regresyon
#
# 08 - Lojistik regresyon (hakem yorum 9): çarpık değişkenler log2 dönüştürülür.
# Tek değişkenli ve yaş düzeltmeli (gösterge + log2 yaş) modeller. 21 ölümle modele en fazla 2 değişken girer.
# OR: standartlaştırılmış (1 SD artış başına) ve log2 değişkenler için "her iki katına çıkış başına".
# Çıktı: outputs/08_log_regresyon/lojistik.csv
# ======================================================================
import numpy as np, pandas as pd
import statsmodels.api as sm
inp, out = args(); o = outdir(out, "08_log_regresyon"); d, c = load(inp)
d["z_log2psp"] = (d.log2psp - d.log2psp.mean()) / d.log2psp.std()
GOST = [("log2psp", "PSP (log2)", True), ("log2pct", "PCT (log2)", True), ("log2crp", "CRP (log2)", True), ("log2laktat", "Laktat (log2)", True), ("log2bun", "BUN (log2)", True),
        ("PRISM3", "PRISM-III", False), ("PELOD2", "PELOD-2", False), ("log2yas", "Yaş (log2 ay+1)", True)]
def fit(y, X):
    try:
        m = sm.Logit(y, sm.add_constant(X)).fit(disp=0); return m, ""
    except Exception as e:
        return None, "ayrışma/yakınsama sorunu"
sat = []
for ad, y, mask in ((" Sepsis tanısı", d.sepsis, np.ones(len(d), bool)), ("Ölüm (tüm hasta)", d.ex, np.ones(len(d), bool))):
    for v, etk, logv in GOST:
        if ad.strip().startswith("Sepsis") and v == "PELOD2": continue  # dairesel
        for model in ("tek değişkenli", "yaş düzeltmeli"):
            if model == "yaş düzeltmeli" and v == "log2yas": continue
            cols = [v] if model == "tek değişkenli" else [v, "log2yas"]
            X = d.loc[mask, cols].copy(); sd = X[v].std(); X[v] = (X[v] - X[v].mean()) / sd   # 1 SD başına
            m, not_ = fit(d.loc[mask, "sepsis" if ad.strip().startswith("Sepsis") else "ex"], X)
            if m is None: sat.append([ad.strip(), etk, model, "", "", "", "", not_]); continue
            ci = np.exp(m.conf_int()).loc[v]; b = m.params[v]; per2x = np.exp(b / sd) if logv else np.nan
            sat.append([ad.strip(), etk, model, round(np.exp(b), 2), f"{ci[0]:.2f}-{ci[1]:.2f}", p_fmt(m.pvalues[v]), round(per2x, 2) if logv else "", not_])
r = pd.DataFrame(sat, columns=["sonlanim", "gosterge", "model", "OR_1SD_basina", "GA95", "p", "OR_iki_katina_cikis(log2 icin)", "not"])
r.to_csv(f"{o}/lojistik.csv", index=False, encoding="utf-8-sig"); print(r.to_string(index=False))

# ======================================================================
# Adım 09: esik iyimserlik
#
# 09 - Youden eşiği, duyarlılık/özgüllük/PPV/NPV ve bootstrap iyimserlik düzeltmesi (hakem yorum 10, Harrell yöntemi).
# Eşikler veriden türetildi (önceden belirlenmedi). Yüksek değer = pozitif kabul edilir.
# PPV ve NPV bu kohortun prevalansına (sepsis %73, ölüm %38) bağlıdır, başka ortamlara aktarılamaz.
# Çıktı: outputs/09_esik_iyimserlik/esikler.csv
# ======================================================================
import numpy as np, pandas as pd
from sklearn.metrics import roc_curve
from statsmodels.stats.proportion import proportion_confint
def wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson"); return f"{lo:.2f}-{hi:.2f}"
inp, out = args(); o = outdir(out, "09_esik_iyimserlik"); d, c = load(inp); BB = 1000
def youden(y, x):
    f, t, th = roc_curve(y, x); j = t - f; i = int(np.argmax(j)); return th[i]
def sens_spec(y, x, th):
    pos = x >= th; return pos[y == 1].mean(), (~pos)[y == 0].mean()
MARK = [("PSP", "PSP"), ("PCT", "PCT"), ("CRP", "CRP"), ("PRISM3", "PRISM-III"), ("PELOD2", "PELOD-2")]
rng = np.random.default_rng(SEED); sat = []
for ad, y, mask in kume(d)[:2]:
    for v, etk in MARK:
        if "Sepsis" in ad and v == "PELOD2": continue        # dairesel
        yy = y[mask].values; x = d.loc[mask, v].values.astype(float); th = youden(yy, x); se, sp = sens_spec(yy, x, th)
        ppv = (yy[x >= th] == 1).mean() if (x >= th).any() else np.nan; npv = (yy[x < th] == 0).mean() if (x < th).any() else np.nan
        os_, op_ = [], []
        for _ in range(BB):
            i = rng.integers(0, len(yy), len(yy)); yb, xb = yy[i], x[i]
            if yb.min() == yb.max(): continue
            tb = youden(yb, xb); sb, pb = sens_spec(yb, xb, tb); so, po = sens_spec(yy, x, tb); os_.append(sb - so); op_.append(pb - po)
        sat.append([ad, etk, round(float(th), 2), round(se, 2), round(sp, 2), round(se - np.mean(os_), 2), round(sp - np.mean(op_), 2), round(ppv, 2), round(npv, 2),
                    wilson(int((x[yy == 1] >= th).sum()), int((yy == 1).sum())), wilson(int((x[yy == 0] < th).sum()), int((yy == 0).sum()))])
r = pd.DataFrame(sat, columns=["sonlanim", "gosterge", "esik(Youden)", "duyarlilik", "ozgullik", "duyarlilik_iyimserlik_duzeltilmis", "ozgullik_iyimserlik_duzeltilmis", "PPV", "NPV", "duyarlilik_GA95_Wilson", "ozgullik_GA95_Wilson"])
r.to_csv(f"{o}/esikler.csv", index=False, encoding="utf-8-sig"); print(r.to_string(index=False))

# ======================================================================
# Adım 10: ust standart
#
# Üst standart (4 ng/mL) üstü 6 hasta için duyarlılık analizi (hakem yorum 1): değerleri 4'te sınırla veya çıkar.
#
# Çıktı: `10_ust_standart/ust_standart_duyarlilik.csv`
# ======================================================================
import numpy as np, pandas as pd
inp, out = args(); o = outdir(out, "10_ust_standart"); d, c = load(inp)
ust = d["PSP_ust_standart_ustu"] == 1
print("Üst standart üstü hasta sayısı:", int(ust.sum()), "| satırlar:", d.loc[ust, "satir_no"].tolist())
kumeler = {"Tüm veri": (d["PSP"].values, np.ones(len(d), bool)),
           "Üst değerler 4 ng/mL'de sınırlandı": (np.minimum(d["PSP"].values, 4.0), np.ones(len(d), bool)),
           "Üst standart üstü 6 hasta çıkarıldı": (d["PSP"].values, ~ust.values)}
sat = []
for ad, y, mask in kume(d):
    for k, (x, m) in kumeler.items():
        mm = mask & m; yy = y[mm].values; xx = x[mm]; a, lo, hi = delong_ci(yy, xx)
        sat.append([ad, k, int(mm.sum()), int(yy.sum()), round(a, 3), f"{lo:.2f}-{hi:.2f}"])
r = pd.DataFrame(sat, columns=["sonlanim", "kume", "n", "olay", "PSP_AUC", "GA95_DeLong"])
r.to_csv(f"{o}/ust_standart_duyarlilik.csv", index=False, encoding="utf-8-sig"); print(r.to_string(index=False))

# ======================================================================
# Adım 11: ybu suresi
#
# YBÜ yatış süresi yalnız yaşayanlarda ve 28. günde YBÜ'süz gün (küçük itiraz 4).
#
# Çıktı: `11_ybu_suresi/ybu_suresi.csv`
# ======================================================================
import numpy as np, pandas as pd
from scipy import stats
inp, out = args(); o = outdir(out, "11_ybu_suresi"); d, c = load(inp)
sag = d[d["ex"] == 0].copy()
d["ybusuz_gun_28"] = np.where(d["ex"] == 1, 0, np.maximum(0, 28 - d["PICU_yatis_gun"]))   # ölen = 0 gün
sat = []
def satir(ad, a, b, ea, eb):
    p = stats.mannwhitneyu(a, b, alternative="two-sided").pvalue
    sat.append([ad, ea, len(a), iqr(a), eb, len(b), iqr(b), p_fmt(p)])
s, n = sag[sag["sepsis"] == 1], sag[sag["sepsis"] == 0]
satir("YBÜ yatış süresi (gün), yalnız yaşayanlar", s["PICU_yatis_gun"], n["PICU_yatis_gun"], "Septik", "Septik olmayan")
satir("YBÜ'süz gün (28. gün), tüm hastalar", d.loc[d.sepsis == 1, "ybusuz_gun_28"], d.loc[d.sepsis == 0, "ybusuz_gun_28"], "Septik", "Septik olmayan")
ps, pn = sag, None
sat.append(["YBÜ yatış süresi (gün), tüm yaşayanlar", "", len(sag), iqr(sag["PICU_yatis_gun"]), "", "", "", ""])
r = pd.DataFrame(sat, columns=["olcut", "grup1", "n1", "grup1_medyan_IQR", "grup2", "n2", "grup2_medyan_IQR", "p"])
r.to_csv(f"{o}/ybu_suresi.csv", index=False, encoding="utf-8-sig"); print(r.to_string(index=False))
print("\nYatışı devam eden hasta sayısı (sonuç kodu 2):", int((d["sonuc_kodu_0exitus_1taburcu_2devam"] == 2).sum()))

# ======================================================================
# Adım 12: zaman
#
# Örnekten ölüme süre ve kaynağa göre örnekleme zamanı (hakem yorum 2).
#
# Çıktı: `12_zaman/ornekten_olume.csv, ornekleme_zamani_kaynak.csv`
# ======================================================================
import numpy as np, pandas as pd
from scipy import stats
inp, out = args(); o = outdir(out, "12_zaman"); d, c = load(inp)
ol = d[d["ex"] == 1]["ornekten_olume_gun"].dropna()
sat = [["Örnekten ölüme süre (gün), tüm ölenler", len(ol), iqr(ol), f"{ol.min():.0f}-{ol.max():.0f}"],
       ["Ölümü örnekten sonraki ≤7 gün içinde olan, n (%)", int((ol <= 7).sum()), f"{(ol <= 7).mean()*100:.0f}%", ""],
       ["Ölümü örnekten sonraki ≤28 gün içinde olan, n (%)", int((ol <= 28).sum()), f"{(ol <= 28).mean()*100:.0f}%", ""]]
pd.DataFrame(sat, columns=["olcut", "n", "medyan_IQR_veya_yuzde", "aralik"]).to_csv(f"{o}/ornekten_olume.csv", index=False, encoding="utf-8-sig")
print(pd.DataFrame(sat, columns=["olcut", "n", "medyan_IQR_veya_yuzde", "aralik"]).to_string(index=False))
g = d.assign(kaynak=d["kaynak_1toplum_2hastane"].map({1: "Toplum", 2: "Hastane/YBÜ"}),
             grup=np.where(d["sepsis"] == 1, "Septik", "Septik olmayan"))
t = g.groupby(["grup", "kaynak"])["yatistan_ornekleme_gun"].agg(n="count", medyan_IQR=iqr).reset_index()
t.to_csv(f"{o}/ornekleme_zamani_kaynak.csv", index=False, encoding="utf-8-sig"); print("\n", t.to_string(index=False))

# ======================================================================
# Adım 13: mikrobiyoloji
#
# Kültür yerleri ve organizma grupları (küçük itiraz 6). Organizma sınıflaması anahtar kelimeyle, elle kontrol edin.
#
# Çıktı: `13_mikrobiyoloji/kultur_yerleri.csv, organizma_gruplari.csv`
# ======================================================================
import numpy as np, pandas as pd
from scipy import stats
inp, out = args(); o = outdir(out, "13_mikrobiyoloji"); d, c = load(inp)
yer = {"kulturde_ureme": "Herhangi bir kültür", "kan_kulturu_ureme": "Kan", "kateter_kulturu_ureme": "Kateter", "tak_kulturu_ureme": "Trakeal aspirat",
       "baska_kultur_ureme": "Diğer"}
s, n = d[d.sepsis == 1], d[d.sepsis == 0]; sat = []
for k, ad in yer.items():
    a, b = int(s[k].sum()), int(n[k].sum()); p = stats.fisher_exact([[a, len(s) - a], [b, len(n) - b]])[1]
    sat.append([ad, int(d[k].sum()), f"{a} ({a/len(s)*100:.0f}%)", f"{b} ({b/len(n)*100:.0f}%)", p_fmt(p)])
r = pd.DataFrame(sat, columns=["kultur_yeri", "tum_hasta", "septik_n41", "septik_olmayan_n15", "p"])
r.to_csv(f"{o}/kultur_yerleri.csv", index=False, encoding="utf-8-sig"); print(r.to_string(index=False))
# Organizma grupları: serbest metinden anahtar kelimeyle. SONUCU KONTROL EDİN, yazım hataları olabilir.
def grupla(t):
    t = str(t).lower(); g = []
    if any(k in t for k in ["candida", "mantar", "galakto", "aspergil"]): g.append("Mantar")
    if any(k in t for k in ["psod", "pseud", "acineto", "kleb", "kelb", "klab", "e col", "ecoli", "serratia", "citro", "proteus", "stanotrof", "maltof", "enterobac", "carba", "gram neg"]): g.append("Gram negatif")
    if any(k in t for k in ["mssa", "mrsa", "staf", "strep", "enterokok", "vre", "kns", "gram poz", "pnom", "cornebac", "miti", "oralis"]): g.append("Gram pozitif")
    return g
org = d.loc[d["mikroorganizma"].astype(str).str.strip() != "0", ["satir_no", "sepsis", "mikroorganizma"]].copy()
org["grup"] = org["mikroorganizma"].apply(grupla)
sat = []
for ad in ["Gram negatif", "Gram pozitif", "Mantar"]:
    m = org["grup"].apply(lambda g: ad in g)
    sat.append([ad, int(m.sum()), int(m[org.sepsis == 1].sum()), int(m[org.sepsis == 0].sum())])
r2 = pd.DataFrame(sat, columns=["organizma_grubu", "hasta_sayisi", "septik", "septik_olmayan"])
r2.to_csv(f"{o}/organizma_gruplari.csv", index=False, encoding="utf-8-sig"); print("\n", r2.to_string(index=False))
org["grup"] = org["grup"].apply(", ".join); org.drop(columns="satir_no").to_csv(f"{o}/organizma_listesi_kontrol.csv", index=False, encoding="utf-8-sig")
print("\nSınıflanamayan kayıt:", int((org["grup"] == "").sum()), "(organizma_listesi_kontrol.csv dosyasına bakın)")

# ======================================================================
# Adım 14: plaka kalitesi
#
# Plaka kalite verisi (hakem yorum 1): standart eğri uyumu, standartların geri kazanımı, standart aralığı dışındaki numuneler.
# Girdi: üreticinin okuyucu dosyası (ham OD'ler). Hasta bilgisi içermez.
# Çıktı: `14_plaka_kalite/plaka_standartlar.csv, plaka_ozet.csv`
# ======================================================================
import numpy as np, pandas as pd, openpyxl
from scipy.optimize import curve_fit
inp, out = args(); o = outdir(out, "14_plaka_kalite")
PLAKA = "Sunred_REG1a_240606.xlsx"     # ham plaka dosyası, /content içine yükleyin
if not os.path.exists(PLAKA):
    print(f"{PLAKA} yüklenmedi, adım 14 atlandı.")
else:
    ws = openpyxl.load_workbook(PLAKA, data_only=True).active

    std_conc = np.array([4000, 2000, 1000, 500, 250.])
    std_od = np.array([ws.cell(r, 1).value for r in range(4, 9)])   # A4:A8
    od = np.array([ws.cell(r, c).value for c in range(1, 12) for r in range(4, 12)
                   if isinstance(ws.cell(r, c).value, (int, float)) and not (c == 1 and r <= 8)])

    quad = lambda y, a, b: a * y**2 + b * y                       # orijinden geçen ikinci derece
    p2, _ = curve_fit(quad, std_od, std_conc)
    f4 = lambda x, a, b, c, d: d + (a - d) / (1 + (x / c)**b)    # 4PL
    p4, _ = curve_fit(f4, std_conc, std_od, p0=[0.05, 1, 2000, 2], maxfev=20000)
    inv4 = lambda y: p4[2] * ((p4[0] - p4[3]) / (y - p4[3]) - 1)**(1 / p4[1])

    std = pd.DataFrame({"standart_pg_mL": std_conc, "OD": std_od,
        "hesaplanan_ikinci_derece": quad(std_od, *p2),
        "geri_kazanim_%_ikinci_derece": quad(std_od, *p2) / std_conc * 100,
        "geri_kazanim_%_4PL": inv4(std_od) / std_conc * 100}).round(2)
    std.to_csv(f"{o}/plaka_standartlar.csv", index=False, encoding="utf-8-sig")

    conc = quad(od, *p2)
    ozet = pd.DataFrame([
        ["Numune sayısı (tekli kuyu, seyreltme yok)", len(od)],
        ["Standart aralığında (250-4000 pg/mL)", int(((od >= std_od[-1]) & (od <= std_od[0])).sum())],
        ["En düşük standardın altında", int((od < std_od[-1]).sum())],
        ["En yüksek standardın üstünde (ekstrapole)", int((od > std_od[0]).sum())],
        ["Beyan edilen üst sınırın (7200 pg/mL) üstünde", int((conc > 7200).sum())],
        ["Geri kazanım % (ikinci derece)", f"{std.iloc[:,3].min():.1f}-{std.iloc[:,3].max():.1f}"],
        ["Geri kazanım % (4PL)", f"{std.iloc[:,4].min():.1f}-{std.iloc[:,4].max():.1f}"],
        ["Eğri formülü (konsantrasyon = a*OD^2 + b*OD)", f"a={p2[0]:.1f}, b={p2[1]:.1f}"],
    ], columns=["olcut", "deger"])
    ozet.to_csv(f"{o}/plaka_ozet.csv", index=False, encoding="utf-8-sig")
    print(std.to_string(index=False)); print(); print(ozet.to_string(index=False))

# ======================================================================
# Adım 15: makale şekilleri
#
# Makaledeki Şekil 1 (akış şeması), Şekil 2 (ROC) ve Şekil 3 (PSP ve yaş).
#
# Çıktı: `15_makale_sekilleri/`
# ======================================================================
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from sklearn.metrics import roc_curve, roc_auc_score
inp, out = args(); o = outdir(out, "15_makale_sekilleri"); d, c = load(inp)

# ---------- Şekil 1: akış şeması (tarama sayıları hasta listesinden elle girildi) ----------
fig, ax = plt.subplots(figsize=(8.4, 7), dpi=300); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
def box(x, y, w, h, t):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="square,pad=0.02", fc="white", ec="black", lw=1))
    ax.text(x, y, t, ha="center", va="center", fontsize=8)
def arr(a, b): ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", lw=1))
n, ns, nns = len(d), int(d.sepsis.sum()), int((d.sepsis == 0).sum())
box(3.2, 9.3, 4.4, .8, "PICU patients, September 2025 – May 2026\n(n = 205)"); arr((3.2, 8.9), (3.2, 7.2))
box(7.8, 8.1, 3.8, .7, "Sepsis not clinically suspected\n(n = 130)"); arr((3.2, 8.1), (5.9, 8.1))
box(3.2, 6.8, 4.4, .8, "Sepsis clinically suspected\n(n = 75)"); arr((3.2, 6.4), (3.2, 4.5))
box(7.9, 5.5, 4.0, 1.3, "Excluded (n = 19)\nFamily refusal (n = 16)\nPICU stay < 24 h (n = 2)\nRecent bone marrow transplant (n = 1)"); arr((3.2, 5.5), (5.9, 5.5))
box(3.2, 4.1, 4.4, .8, f"Included and PSP measured\n(n = {n})")
arr((3.2, 3.7), (1.8, 2.7)); arr((3.2, 3.7), (4.9, 2.7))
box(1.8, 2.3, 2.7, .8, f"Sepsis\n(n = {ns}; {int(d.ex[d.sepsis == 1].sum())} died)")
box(4.9, 2.3, 2.7, .8, f"No sepsis\n(n = {nns}; {int(d.ex[d.sepsis == 0].sum())} died)")
box(7.8, 4.1, 3.8, .8, f"Healthy controls\n(n = {len(c)})")
fig.savefig(f"{o}/Figure1_flow.png", bbox_inches="tight"); plt.close(fig)

# ---------- Şekil 2: ROC ----------
COL = {"PSP": "#000000", "PCT": "#eb6834", "CRP": "#1baf7a", "PRISM III": "#2a78d6", "PELOD-2": "#eda100", "Phoenix": "#e87ba4"}
SRC = {"PSP": "PSP", "PCT": "PCT", "CRP": "CRP", "PRISM III": "PRISM3", "PELOD-2": "PELOD2", "Phoenix": "PSS"}
panels = (("A. Sepsis", "sepsis", ["PSP", "PCT", "CRP", "PRISM III"]),
          ("B. PICU mortality", "ex", ["PSP", "PCT", "CRP", "PRISM III", "PELOD-2", "Phoenix"]))
fig, axes = plt.subplots(1, 2, figsize=(10, 5), dpi=300)
for ax, (title, col, markers) in zip(axes, panels):
    for name in markers:
        auc = roc_auc_score(d[col], d[SRC[name]]); fpr, tpr, _ = roc_curve(d[col], d[SRC[name]])
        ax.plot(fpr, tpr, color=COL[name], lw=2.2 if name == "PSP" else 1.4, label=f"{name} (AUC {auc:.2f})")
        print(f"{title:18s} {name:10s} AUC={auc:.3f}")
    ax.plot([0, 1], [0, 1], color="#999999", lw=0.8, ls="--")
    ax.set_title(title, loc="left", fontsize=11); ax.set_xlabel("1 - Specificity"); ax.set_ylabel("Sensitivity"); ax.set_aspect("equal")
    ax.legend(loc="lower right", fontsize=7.5, frameon=False)
fig.tight_layout(); fig.savefig(f"{o}/Figure2_ROC.png"); plt.close(fig)

# ---------- Şekil 3: PSP ve yaş ----------
d["yas_yil"] = d["yas_ay"] / 12
fig, ax = plt.subplots(figsize=(7.2, 5.2), dpi=300)
for name, sub, color in (("Sepsis", d[d.sepsis == 1], "#2a78d6"), ("No sepsis", d[d.sepsis == 0], "#eb6834")):
    alive, died = sub[sub.ex == 0], sub[sub.ex == 1]
    ax.scatter(alive.yas_yil, alive.PSP, s=34, marker="o", color=color, label=f"{name}, survived")
    if len(died): ax.scatter(died.yas_yil, died.PSP, s=46, marker="X", color=color, label=f"{name}, died")
ax.scatter(c.yas_yil, c.PSP, s=34, marker="s", color="#1baf7a", label="Healthy control")
ax.axhline(4.0, color="#888888", lw=1, ls="--")
ax.text(0.99, 4.15, "Highest standard (4 ng/mL)", transform=ax.get_yaxis_transform(), ha="right", fontsize=8)
ax.set_yscale("log"); ax.set_xlabel("Age (years)"); ax.set_ylabel("PSP (ng/mL, log scale)")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3)
fig.tight_layout(); fig.savefig(f"{o}/Figure3_PSP_age.png"); plt.close(fig)
print("Şekiller kaydedildi:", o)

# ======================================================================
# Adım 16: septik olmayanlarda yatış tanısı
#
# STARD madde 21b.
#
# Çıktı: `16_septik_olmayan_tani/septik_olmayan_tanilar.csv`
# ======================================================================
import pandas as pd
inp, out = args(); o = outdir(out, "16_septik_olmayan_tani"); d, c = load(inp)
TANI = {1: "Respiratory", 2: "Neurological", 3: "Trauma", 4: "Infection", 5: "Gastrointestinal",
        6: "Postoperative", 7: "Hemato-oncological", 8: "Intoxication", 9: "Renal"}
t = d.loc[d.sepsis == 0, "yatis_tani_kodu"].map(TANI).fillna("Missing").value_counts().rename("n")
t.to_csv(f"{o}/septik_olmayan_tanilar.csv"); print(t.to_string())

# ======================================================================
# Adım 17: sürümleri kaydet
#
# Python ve paket sürümlerini `requirements.txt` dosyasına yazar. Bu dosyayı GitHub'a koyun.
# Çıktı: `requirements.txt` ve `outputs/python_surumu.txt`
# ======================================================================
import sys, subprocess, importlib.metadata as md
PAKETLER = ["numpy", "pandas", "scipy", "scikit-learn", "statsmodels", "openpyxl", "matplotlib"]
satir = [f"{p}=={md.version(p)}" for p in PAKETLER]
open("requirements.txt", "w").write("\n".join(satir) + "\n")
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/python_surumu.txt", "w").write(sys.version + "\n")
print("Python:", sys.version.split()[0]); print("\n".join(satir))

# ======================================================================
# Çıktıları indirme
# ======================================================================
import shutil
shutil.make_archive("psp_sonuclar", "zip", OUT)
try:
    from google.colab import files; files.download("psp_sonuclar.zip")
except Exception:
    print("psp_sonuclar.zip oluşturuldu, dosya panelinden indirin.")
