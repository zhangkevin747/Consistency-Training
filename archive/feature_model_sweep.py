#!/usr/bin/env python3
"""
Sweep feature sets x model classes for the cross-question transfer reward model.
Metric: leave-one-question-out AUC. We report MEAN, MEDIAN, and MIN (floor) --
the floor matters most: a reward at/below chance on its worst question is unsafe.
"""
import json, re, statistics as st
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import roc_auc_score

rows=[json.loads(l) for l in open("data/cross_phrasing_8b.jsonl")]
ok=[r for r in rows if r["ok"] and r["reasoning"] and r["probability"] is not None
    and r["scores"].get("overall") is not None]
qs=sorted(set(r["qid"] for r in ok))

DISC=["however","but","although","though","whereas","nevertheless","yet","while","conversely","contrast"]
HEDGE=["might","perhaps","possibly","seems","arguably","may","could","uncertain","unclear","not necessarily"]
CERT=["clearly","obviously","definitely","certainly","must","cannot","necessarily","undeniably","of course"]
TWOSIDE=["proponent","critic","opponent","some argue","others","on the other hand","objection",
         "counterargument","one could","might object","defender"]

# claim-engagement: cosine(reasoning, the claim it answered), via shared tf-idf space
all_txt=[r["reasoning"] for r in ok]+[r["rephrasing_text"] for r in ok]
tv=TfidfVectorizer(max_features=3000, stop_words="english").fit(all_txt)
def cos(a,b):
    va=tv.transform([a]); vb=tv.transform([b])
    num=(va.multiply(vb)).sum(); da=np.sqrt(va.multiply(va).sum()); db=np.sqrt(vb.multiply(vb).sum())
    return float(num/(da*db)) if da and db else 0.0

def featrow(r,med):
    t=r["reasoning"].lower(); w=re.findall(r"[a-z']+",t); n=len(w) or 1
    sents=max(1,t.count(".")+t.count("?")+t.count("!"))
    dens=lambda L: sum(t.count(x) for x in L)/n*100
    return {
        "prob": r["probability"], "dist_consensus": abs(r["probability"]-med),  # sign-flippers
        "len": len(r["reasoning"]), "words": n, "ttr": len(set(w))/n,
        "disc": dens(DISC), "hedge": dens(HEDGE), "cert": dens(CERT), "twoside": dens(TWOSIDE),
        "because": t.count("because"), "qmarks": t.count("?"),
        "avg_sent_len": n/sents, "claim_engage": cos(r["reasoning"], r["rephrasing_text"]),
    }

FR={}; Y=[]; G=[]
for q in qs:
    g=[r for r in ok if r["qid"]==q]; med=st.median(r["probability"] for r in g)
    qmed=st.median(r["scores"]["overall"] for r in g)
    for r in g:
        FR.setdefault("_rows",[]).append(featrow(r,med)); Y.append(1 if r["scores"]["overall"]>qmed else 0); G.append(q)
ROWS=FR["_rows"]; Y=np.array(Y); G=np.array(G)
allkeys=list(ROWS[0].keys())
def mat(keys): return np.array([[row[k] for k in keys] for row in ROWS])

FEATURE_SETS={
    "base7 (orig)": ["prob","dist_consensus","len","ttr","disc","hedge","because"],
    "no-prob (sign-stable)": ["len","words","ttr","disc","hedge","cert","twoside","because","qmarks","avg_sent_len","claim_engage"],
    "all features": allkeys,
}
MODELS={
    "logistic": lambda: LogisticRegression(max_iter=5000),
    "hist-gbm": lambda: HistGradientBoostingClassifier(max_iter=300, max_depth=3, learning_rate=0.05),
    "random-forest": lambda: RandomForestClassifier(n_estimators=300, max_depth=6, random_state=0),
}

logo=LeaveOneGroupOut()
print(f"{len(ROWS)} rollouts, {len(qs)} questions. LOQO transfer AUC.\n")
print(f"{'feature set':24} {'model':14} {'mean':>6} {'median':>7} {'MIN(floor)':>11} {'#<0.55':>7}")
for fname,keys in FEATURE_SETS.items():
    X=mat(keys)
    for mname,mk in MODELS.items():
        aucs={}
        for tr,te in logo.split(X,Y,G):
            mu,sd=X[tr].mean(0),X[tr].std(0)+1e-9
            clf=mk().fit((X[tr]-mu)/sd,Y[tr])
            p=clf.predict_proba((X[te]-mu)/sd)[:,1]
            if len(set(Y[te]))>1: aucs[G[te][0]]=roc_auc_score(Y[te],p)
        v=list(aucs.values())
        print(f"{fname:24} {mname:14} {st.mean(v):>6.2f} {st.median(v):>7.2f} "
              f"{min(v):>11.2f} {sum(1 for x in v if x<0.55):>7}")
