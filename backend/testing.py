import requests
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

API_URL = "http://localhost:8000/api/chat/message"
df = pd.read_csv("dataset_uji.csv")

y_true = []
y_pred = []

for _, row in df.iterrows():
    try:
        resp = requests.post(API_URL, json={"message": row["kalimat"]})
        result = resp.json()
        predicted = result.get("intent", "lainnya")
        if predicted == "not_understood":
            predicted = "lainnya"
        y_true.append(row["intent"])
        y_pred.append(predicted)
        print(f"[{row['intent']}] '{row['kalimat']}' -> {predicted} ({result.get('confidence', 0):.2f})")
    except Exception as e:
        print(f"Error: {e}")
        y_true.append(row["intent"])
        y_pred.append("lainnya")

print("\n=== CLASSIFICATION REPORT ===")
print(classification_report(y_true, y_pred, zero_division=0))

labels = sorted(df["intent"].unique())
cm = confusion_matrix(y_true, y_pred, labels=labels)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)

fig, ax = plt.subplots(figsize=(14, 12))
disp.plot(ax=ax, cmap="Blues", colorbar=True)
plt.xticks(rotation=45, ha="right", fontsize=9)
plt.yticks(fontsize=9)
plt.title("Confusion Matrix - PUSPA Chatbot BPK RI", fontsize=14, pad=20)
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=150, bbox_inches="tight")
print("\nGambar disimpan sebagai confusion_matrix.png")
