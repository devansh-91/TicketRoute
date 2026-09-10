from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ticketroute.generate_data import write_csv
from ticketroute.preprocess import normalize
from ticketroute.taxonomy import DEPARTMENTS, URGENCY

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "tickets.csv"
MODELS = ROOT / "models"
METRICS = ROOT / "reports" / "metrics.json"


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
                LogisticRegression(
                    max_iter=400,
                    class_weight="balanced",
                    solver="lbfgs",
                ),
            ),
        ]
    )


def _slice_report(y_true, y_pred, labels) -> dict:
    return classification_report(
        y_true, y_pred, labels=labels, output_dict=True, zero_division=0
    )


def train() -> dict:
    if not DATA.exists():
        write_csv(DATA)
    df = pd.read_csv(DATA)
    df["text"] = df["text"].map(normalize)
    X = df["text"]
    idx = df.index.to_list()
    train_i, test_i = train_test_split(
        idx, test_size=0.2, random_state=42, stratify=df["department"]
    )
    X_tr, X_te = X.loc[train_i], X.loc[test_i]
    dept_clf = _pipe()
    urg_clf = _pipe()
    dept_clf.fit(X_tr, df.loc[train_i, "department"])
    urg_clf.fit(X_tr, df.loc[train_i, "urgency"])
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(dept_clf, MODELS / "department.joblib")
    joblib.dump(urg_clf, MODELS / "urgency.joblib")

    y_dept = dept_clf.predict(X_te)
    y_urg = urg_clf.predict(X_te)
    metrics = {
        "n_train": int(len(train_i)),
        "n_test": int(len(test_i)),
        "department": _slice_report(
            df.loc[test_i, "department"], y_dept, DEPARTMENTS
        ),
        "urgency": _slice_report(df.loc[test_i, "urgency"], y_urg, URGENCY),
        "by_language": {},
    }
    te = df.loc[test_i].copy()
    te["pred_dept"] = y_dept
    te["pred_urg"] = y_urg
    for lang, g in te.groupby("language"):
        metrics["by_language"][str(lang)] = {
            "n": int(len(g)),
            "department_acc": float((g["department"] == g["pred_dept"]).mean()),
            "urgency_acc": float((g["urgency"] == g["pred_urg"]).mean()),
        }
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    m = train()
    print("dept acc", round(m["department"]["accuracy"], 3))
    print("urg acc", round(m["urgency"]["accuracy"], 3))
    print("by language", m["by_language"])
    print("wrote", MODELS)
