from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ticketroute.generate_data import write_csv
from ticketroute.preprocess import normalize
from ticketroute.taxonomy import ROUTEABLE, URGENCY

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "tickets.csv"
MODELS = ROOT / "models"
METRICS = ROOT / "reports" / "metrics.json"

KEYWORDS = {
    "Billing & Payments": ["refund", "invoice", "upi", "bill", "payment", "रिफंड", "बिल", "kat", "paise"],
    "Account / KYC / Login": ["login", "otp", "kyc", "pan", "password", "account", "लॉगिन"],
    "Technical / App crash": ["crash", "app", "android", "hang", "क्रैश"],
    "Product / Order / Delivery": ["order", "deliver", "tracking", "ऑर्डर", "saman"],
    "Abuse / Safety / Fraud": ["phishing", "otp", "fraud", "scam", "fake", "फेक", "धोखा"],
    "Feedback / General": ["thanks", "thank", "dashboard", "suggestion", "धन्यवाद", "shukriya"],
}


def _pipe() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=20000,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(max_iter=400, class_weight="balanced", solver="lbfgs"),
            ),
        ]
    )


def keyword_predict(texts: pd.Series) -> list[str]:
    out = []
    for t in texts:
        tl = str(t).lower()
        scores = {d: sum(k.lower() in tl for k in kws) for d, kws in KEYWORDS.items()}
        out.append(max(scores, key=scores.get) if max(scores.values()) else "Feedback / General")
    return out


def train() -> dict:
    if not DATA.exists():
        write_csv(DATA)
    df = pd.read_csv(DATA)
    df["text"] = df["text"].map(normalize)
    idx = df.index.to_list()
    train_i, temp_i = train_test_split(
        idx, test_size=0.30, random_state=42, stratify=df["department"]
    )
    val_i, test_i = train_test_split(
        temp_i, test_size=0.50, random_state=42, stratify=df.loc[temp_i, "department"]
    )
    X = df["text"]
    dept_clf, urg_clf = _pipe(), _pipe()
    dept_clf.fit(X.loc[train_i], df.loc[train_i, "department"])
    urg_clf.fit(X.loc[train_i], df.loc[train_i, "urgency"])
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(dept_clf, MODELS / "department.joblib")
    joblib.dump(urg_clf, MODELS / "urgency.joblib")

    def pack(split_i, name):
        y_dept = dept_clf.predict(X.loc[split_i])
        y_urg = urg_clf.predict(X.loc[split_i])
        y_kw = keyword_predict(X.loc[split_i])
        gold_d = df.loc[split_i, "department"]
        gold_u = df.loc[split_i, "urgency"]
        p1_mask = gold_u == "P1"
        te = df.loc[split_i].copy()
        te["pred_dept"] = y_dept
        te["pred_urg"] = y_urg
        by_lang = {}
        for lang, g in te.groupby("language"):
            by_lang[str(lang)] = {
                "n": int(len(g)),
                "department_acc": float((g["department"] == g["pred_dept"]).mean()),
                "urgency_acc": float((g["urgency"] == g["pred_urg"]).mean()),
            }
        return {
            "n": int(len(split_i)),
            "department": classification_report(
                gold_d, y_dept, labels=ROUTEABLE, output_dict=True, zero_division=0
            ),
            "urgency": classification_report(
                gold_u, y_urg, labels=URGENCY, output_dict=True, zero_division=0
            ),
            "p1_recall": float(recall_score(gold_u, y_urg, labels=["P1"], average="micro", zero_division=0))
            if p1_mask.any()
            else None,
            "keyword_baseline_dept_acc": float((gold_d == y_kw).mean()),
            "by_language": by_lang,
            "note": name,
        }

    metrics = {
        "n_train": int(len(train_i)),
        "n_val": int(len(val_i)),
        "n_test": int(len(test_i)),
        "split": "70/15/15 stratified by department",
        "disclaimer": (
            "Scores on synthetic templates are high (template memorisation). "
            "Quote keyword_baseline vs sklearn, language slices, and P1 recall. "
            "Do not present test accuracy as production F1."
        ),
        "val": pack(val_i, "val"),
        "test": pack(test_i, "test"),
    }
    # flatten test block for older report readers
    metrics["department"] = metrics["test"]["department"]
    metrics["urgency"] = metrics["test"]["urgency"]
    metrics["by_language"] = metrics["test"]["by_language"]
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    m = train()
    t = m["test"]
    print("test dept acc", round(t["department"]["accuracy"], 3))
    print("keyword baseline", round(t["keyword_baseline_dept_acc"], 3))
    print("p1 recall", t["p1_recall"])
    print("by language", t["by_language"])
    print("wrote", MODELS)
