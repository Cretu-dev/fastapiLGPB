# Creeaza server fast api si parseaza datele

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Security
import os
from fastapi.staticfiles import StaticFiles
import uuid
from fastapi.security.api_key import APIKeyHeader
import mimetypes
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import telebot
from contextlib import asynccontextmanager
import time

load_dotenv('keys.env')
token = os.getenv('notifbot')
chatid = int(os.getenv('technical_group_id', '0'))

import bot

notif_bot = telebot.TeleBot(token)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(purge, 'interval', hours = 0.25)
    scheduler.start()

    notif_bot.send_message(chatid, 'A pornit serverul, sunt pe standby')

    yield
    scheduler.shutdown(wait=False)

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    title = 'LGAPI',
    lifespan=lifespan
)

#ALLOWED_TYPES = {'image/jpeg','image/png', 'image/webp'}
MAX_BYTES = 20 * 1024 * 1024
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

@app.get("/")
def health():
    return {"status": "running"}

API_KEY = os.getenv('key')
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)): # api key verification
    if not API_KEY:
        raise RuntimeError('API KEY is not in environment')
    
    if not api_key:
        raise HTTPException(status_code=403, detail="API Key missing")
    
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    return api_key

@app.post('/upload') # Inregistreaza ruta, cand te duci pe /upload se ruleaza functia de mai jos
async def upload1(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
 # Functia ruleaza in mod async, e un event loop si poate face I/0 fara sa blocheze serverul
 #   if file.content_type not in ALLOWED_TYPES:
  #      raise HTTPException(
   #         status_code = 415,
    #        detail=f'Unsupported type: {file.content_type}' #Unsupported file
     #   )
    
    data = await file.read() # Functia se poate opri aici cat isi da read 

    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=413, # File too large
            detail=f'File too large!'
        )
    
    extension = mimetypes.guess_extension(file.content_type).lstrip('.')
    filename = f'{uuid.uuid4().hex}.{extension}' # genereaza un identificator random pentru numele fisierului, extension concateneaza numele asta cu extensia (.jpg, .png)
    filepath = os.path.join(UPLOAD_DIR, filename) # creeaza pathul catre fisier

    with open(filepath, 'wb') as f: # deschide fisierul in write binary si inchide automat 
        f.write(data) # scrie bytesii in fisier

    public_url = f"https://anymore-called-surfing-complications.trycloudflare.com/files/{filename}"
    
    return {
        "ok": True,
        "public_url": public_url,
        "filename": filename,
        "content_type": file.content_type,
        "bytes": len(data),
    }

def purge():
    deleted = 0
    timelimit = time.time() - 20
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            filepath = os.path.join(UPLOAD_DIR, filename)
            try:
                if os.path.isfile(filepath) or os.path.islink(filepath):
                    if os.path.getmtime(filepath) < timelimit:
                        os.remove(filepath)
                        notif_bot.send_message(chatid, f'Deleted file: {filepath}', parse_mode='Markdown')
                        deleted += 1
            except Exception as e:
                print(f'Eroare la stergere {e}')
            

