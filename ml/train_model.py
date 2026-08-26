from pathlib import Path
import pandas as pd, joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
base=Path(__file__).resolve().parent; model_dir=base/'models'; model_dir.mkdir(exist_ok=True)
df=pd.read_csv(base/'complaints.csv').dropna(); xtr,xte,ytr,yte=train_test_split(df.text,df.priority,test_size=.25,random_state=42,stratify=df.priority)
model=Pipeline([('tfidf',TfidfVectorizer(lowercase=True,ngram_range=(1,2))),('classifier',LogisticRegression(max_iter=2000))]); model.fit(xtr,ytr); print(f'Priority accuracy: {accuracy_score(yte,model.predict(xte)):.2f}'); joblib.dump(model,model_dir/'priority_model.pkl'); print('Model saved.')
