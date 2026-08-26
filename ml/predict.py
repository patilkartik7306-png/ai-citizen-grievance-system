from pathlib import Path
import joblib
m=joblib.load(Path(__file__).resolve().parent/'models'/'priority_model.pkl')
MAP={'Waste Management':'Waste Management','Road':'Public Works','Water Supply':'Water Supply','Street Lighting':'Street Lighting','Drainage and Sewerage':'Drainage and Sewerage','Other Municipal Issue':'General Administration'}
def predict_priority(text): return m.predict([text])[0]
def get_department(category): return MAP.get(category,'General Administration')
