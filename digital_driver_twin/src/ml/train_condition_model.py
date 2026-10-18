import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.utils.class_weight import compute_sample_weight

DATA_FILE = "data/processed/ml_driver_sessions.csv"
MODEL_FILE = "models/ml_condition_classifier.joblib"

# Only use direct camera measurements.
# Exclude rule-engine outputs to reduce target leakage.
FEATURES = [
    "ear",
    "perclos",
    "mar",
    "yawns",
    "pitch",
    "yaw",
    "roll",
]

LABELS = [
    "normal",
    "simulated_eye_closure",
    "simulated_distraction",
]


def main():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required = FEATURES + ["condition_label", "session_id"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.dropna(subset=required).copy()
    df = df[df["condition_label"].isin(LABELS)].copy()

    if df.empty:
        raise ValueError("No labelled training rows found.")

    session_labels = df.groupby("session_id")["condition_label"].nunique()
    if (session_labels != 1).any():
        raise ValueError(
            "At least one session contains multiple condition labels. "
            "Check session labeling before training."
        )

    X = df[FEATURES].apply(pd.to_numeric, errors="coerce")
    valid = X.notna().all(axis=1)
    df = df.loc[valid].copy()
    X = X.loc[valid]

    y = df["condition_label"]
    groups = df["session_id"]

    print("\n=== DATASET ===")
    print("Rows:", len(df))
    print("Sessions:", groups.nunique())
    print("\nRows per condition:")
    print(y.value_counts().to_string())
    print("\nSessions per condition:")
    print(
        df.groupby("condition_label")["session_id"]
          .nunique()
          .to_string()
    )

    if y.nunique() != len(LABELS):
        raise ValueError("All three condition labels must be present.")

    if groups.nunique() < 3:
        raise ValueError("More independent sessions are needed.")

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced_subsample",
        min_samples_leaf=2,
        n_jobs=-1,
    )

    # Evaluate each complete session as unseen test data.
    cv = LeaveOneGroupOut()
    predictions = cross_val_predict(
        model,
        X,
        y,
        groups=groups,
        cv=cv,
        n_jobs=1,
    )

    print("\n=== SESSION-HELD-OUT EVALUATION ===")
    print(
        "Accuracy:",
        round(accuracy_score(y, predictions), 4)
    )
    print("\nClassification report:")
    print(
        classification_report(
            y,
            predictions,
            labels=LABELS,
            zero_division=0,
            digits=3,
        )
    )

    print("Confusion matrix (rows=true, columns=predicted):")
    print(pd.DataFrame(
        confusion_matrix(y, predictions, labels=LABELS),
        index=LABELS,
        columns=LABELS,
    ).to_string())

    # Fit the deployable prototype model on all collected data.
    final_model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced_subsample",
        min_samples_leaf=2,
        n_jobs=-1,
    )
    final_model.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    joblib.dump(
        {
            "model": final_model,
            "features": FEATURES,
            "labels": LABELS,
            "model_type": "RandomForestClassifier",
            "purpose": "simulated_test_condition_classification",
        },
        MODEL_FILE,
    )

    print(f"\nSaved model to: {MODEL_FILE}")
    print(
        "\nIMPORTANT: This model classifies the collected simulated "
        "test conditions. It is not clinically validated and must not "
        "replace the existing rule-based safety logic."
    )


if __name__ == "__main__":
    main()
