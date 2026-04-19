import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# 1. Läs in filen
df = pd.read_csv('dataset_sdn.csv')

# 2. Välj ut relevanta features (pktcount = paketantal, bytecount = datamängd, dur = varaktighet)
features = ['pktcount', 'bytecount', 'dur']
X = df[features]
y = df['label'] # 0 = Benign (Normal), 1 = Malicious (Attack)

# 3. SPLIT: Vi sparar 20% helt separat för din skarpa REDOVISNING
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

# 4. Spara undan TEST-DATAT (Denna fil används för AI-läget i dashboarden)
test_data = pd.concat([X_test, y_test], axis=1)
test_data.to_csv('skarp_test_data.csv', index=False)
print("✅ 'skarp_test_data.csv' skapad!")

# 5. Träna modellen (Random Forest)
# Vi begränsar djupet (max_depth) för att modellen inte ska bli för tung för din dator
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# 6. Spara modellen som .pkl
joblib.dump(model, 'student_model.pkl')
print("✅ 'student_model.pkl' sparad!")