import sys
import os
sys.path.append(os.getcwd())

print("Importing analytics...")
from app.routers.analytics import router as analytics_router
print("Importing meta...")
from app.routers.meta import router as meta_router
print("Importing predict...")
from app.routers.predict import router as predict_router
print("Importing batch...")
from app.routers.batch import router as batch_router
print("Importing chat...")
from app.routers.chat import router as chat_router
print("Success!")
