#!/usr/bin/env python3
"""
Can classical-NLP / surface features predict Opus reasoning-quality?
Two honest tests:
  (1) WITHIN-question TF-IDF -> quality (topic held constant): does *vocabulary*
      separate good from bad rollouts of the SAME claim?  (CV AUC, vs length baseline)
  (2) LEAVE-ONE-QUESTION-OUT on topic-free STYLE features (discourse markers, hedging,
      lexical diversity, length): does style->quality GENERALIZE to an unseen claim?
"""
import json, re, statistics as st
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, LeaveOneGroupOut
from sklearn.metrics import roc_auc_score

rows = [json.loads(l) for l in open("data/cross_phrasing_8b.jsonl")]
ok = [r for r in rows if r["ok"] and r["reasoning"] and r["scores"].get("overall") is not None]
qs = sorted(set(r["qid"] for r in ok))

# label = top vs bottom half by quality WITHIN question (median split), drop middle ties
def make_labels(group):
    qsv = sorted(r["scores"]["overall"] for r in group)
    med = st.median(qsv)
    lab = []
    for r in group:
        lab.append(1 if r["scores"]["overall"] > med else 0)
    return lab

DISC = ["however", "but", "although", "though", "whereas", "on the other hand",
        "nevertheless", "yet", "while", "conversely", "in contrast"]
HEDGE = ["might", "perhaps", "possibly", "seems", "arguably", "may", "could",
         "uncertain", "unclear", "to some extent", "not necessarily"]

def style_feats(txt):
    t = txt.lower(); words = re.findall(r"[a-z']+", t); n = len(words) or 1
    uniq = len(set(words))
    return [
        len(txt),                                   # char length
        n,                                          # word count
        uniq / n,                                   # type-token ratio
        sum(t.count(d) for d in DISC) / n * 100,    # discourse-marker density
        sum(t.count(h) for h in HEDGE) / n * 100,   # hedging density
        t.count("?") , t.count("because"),          # questions, causal markers
    ]

print("=== TEST 1: within-question TF-IDF -> quality (5-fold CV AUC) ===")
print(f"{'question':26} {'AUC[tfidf]':>10} {'AUC[length]':>11} {'n':>4}")
tfidf_aucs = []
for q in qs:
    g = [r for r in ok if r["qid"] == q]
    y = np.array(make_labels(g))
    if len(set(y)) < 2:
        continue
    txt = [r["reasoning"] for r in g]
    length = np.array([[len(r["reasoning"])] for r in g])
    # TF-IDF CV
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    preds = np.zeros(len(y)); lpreds = np.zeros(len(y))
    for tr, te in skf.split(txt, y):
        vec = TfidfVectorizer(max_features=400, ngram_range=(1,2), min_df=2, stop_words="english")
        Xtr = vec.fit_transform([txt[i] for i in tr]); Xte = vec.transform([txt[i] for i in te])
        clf = LogisticRegression(max_iter=1000, C=1.0).fit(Xtr, y[tr])
        preds[te] = clf.predict_proba(Xte)[:,1]
        lc = LogisticRegression(max_iter=1000).fit(length[tr], y[tr])
        lpreds[te] = lc.predict_proba(length[te])[:,1]
    a = roc_auc_score(y, preds); al = roc_auc_score(y, lpreds)
    tfidf_aucs.append(a)
    print(f"{q:26} {a:>10.2f} {al:>11.2f} {len(y):>4}")
print(f"{'MEAN':26} {st.mean(tfidf_aucs):>10.2f}")

print()
print("=== TEST 2: leave-one-QUESTION-out, topic-free STYLE features -> quality ===")
print("    (train on 4 questions, predict the 5th. tests if STYLE generalizes, not topic)")
X = np.array([style_feats(r["reasoning"]) for r in ok])
groups = np.array([r["qid"] for r in ok])
# global median split for label (per-question median to keep balanced within q)
y = []
for r in ok:
    g = [x for x in ok if x["qid"] == r["qid"]]
    med = st.median(x["scores"]["overall"] for x in g)
    y.append(1 if r["scores"]["overall"] > med else 0)
y = np.array(y)
logo = LeaveOneGroupOut()
aucs = []
for tr, te in logo.split(X, y, groups):
    mu, sd = X[tr].mean(0), X[tr].std(0)+1e-9
    clf = LogisticRegression(max_iter=2000).fit((X[tr]-mu)/sd, y[tr])
    p = clf.predict_proba((X[te]-mu)/sd)[:,1]
    held = groups[te][0]
    if len(set(y[te]))>1:
        a = roc_auc_score(y[te], p); aucs.append(a)
        print(f"   held-out {held:26} AUC={a:.2f}")
print(f"   MEAN generalization AUC = {st.mean(aucs):.2f}   (0.5 = style does NOT transfer)")
