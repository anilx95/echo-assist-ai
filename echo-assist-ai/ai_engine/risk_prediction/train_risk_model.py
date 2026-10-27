import os
import random

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


OBJECT_RISK = {
    "person": 2,
    "pole": 2,
    "car": 5,
    "dog": 3,
    "bike": 4,
    "chair": 2,
    "bench": 2,
    "door": 1,
    "tree": 3,
    "bus": 5,
    "stairs": 5,
    "pothole": 5,
    "traffic_light": 1,
    "zebra_crossing": 1,
}


def calculate_label(
    distance_cm,
    speed,
    direction,
    object_risk,
    surface_risk,
    lighting_risk,
):
    score = 0

    if distance_cm < 50:
        score += 40
    elif distance_cm < 100:
        score += 30
    elif distance_cm < 200:
        score += 20
    else:
        score += 5

    score += object_risk * 6
    score += min(speed * 4, 15)
    score += direction * 5
    score += surface_risk * 3
    score += lighting_risk * 3

    score = min(int(score), 100)

    if score >= 80:
        risk_class = 3
    elif score >= 60:
        risk_class = 2
    elif score >= 40:
        risk_class = 1
    else:
        risk_class = 0

    return score, risk_class


def generate_dataset(samples=5000):
    rows = []

    object_names = list(OBJECT_RISK.keys())

    for _ in range(samples):
        object_name = random.choice(object_names)

        distance_cm = random.uniform(20, 500)
        speed = random.uniform(0, 5)

        # 0 = side, 1 = center path
        direction = random.choice([0, 1])

        object_risk = OBJECT_RISK[object_name]

        # 1 low, 2 medium, 3 high
        surface_risk = random.randint(1, 3)
        lighting_risk = random.randint(1, 3)

        risk_score, risk_class = calculate_label(
            distance_cm,
            speed,
            direction,
            object_risk,
            surface_risk,
            lighting_risk,
        )

        rows.append({
            "distance_cm": round(distance_cm, 2),
            "speed": round(speed, 2),
            "direction": direction,
            "object_risk": object_risk,
            "surface_risk": surface_risk,
            "lighting_risk": lighting_risk,
            "risk_score": risk_score,
            "risk_class": risk_class,
        })

    return pd.DataFrame(rows)


print("Generating ECHO-ASSIST AI risk dataset...")

df = generate_dataset()

dataset_path = os.path.join(
    DATA_DIR,
    "risk_training_data.csv"
)

df.to_csv(dataset_path, index=False)

print("Dataset saved:")
print(dataset_path)


features = [
    "distance_cm",
    "speed",
    "direction",
    "object_risk",
    "surface_risk",
    "lighting_risk",
]

X = df[features]
y = df["risk_class"]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    class_weight="balanced",
)


print("\nTraining Random Forest model...")

model.fit(X_train, y_train)


predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)


print("\nModel Accuracy:")
print(round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions
    )
)


model_path = os.path.join(
    MODEL_DIR,
    "risk_model.joblib"
)

joblib.dump(model, model_path)


print("\nModel saved:")
print(model_path)