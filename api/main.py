from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Chiller, ChillerData
from datetime import datetime
from typing import Optional

# Ganti dengan kredensial database Anda
DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/jti-new2"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency untuk mendapatkan sesi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint untuk mendapatkan semua chillers
@app.get("/chillers")
def get_chillers(db: Session = Depends(get_db)):
    return db.query(Chiller).all()

# Endpoint untuk mendapatkan satu chiller berdasarkan ID
@app.get("/chillers/{chiller_id}")
def get_chiller_by_id(chiller_id: str, db: Session = Depends(get_db)):
    chiller = db.query(Chiller).filter(Chiller.id == chiller_id).first()
    if not chiller:
        raise HTTPException(status_code=404, detail="Chiller not found")
    return chiller

# Endpoint untuk mendapatkan data real-time (terbaru) dari satu chiller
@app.get("/chillers/{chiller_id}/latest_data")
def get_chiller_latest_data(chiller_id: str, db: Session = Depends(get_db)):
    data = db.query(ChillerData).filter(ChillerData.chiller_id == chiller_id).order_by(ChillerData.timestamp.desc()).first()
    if not data:
        raise HTTPException(status_code=404, detail="Chiller data not found for this ID")
    return data

# Endpoint untuk mendapatkan data historis chiller dengan rentang waktu
@app.get("/chillers/{chiller_id}/history")
def get_chiller_history(
    chiller_id: str, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(ChillerData).filter(ChillerData.chiller_id == chiller_id)
    
    if start_date:
        query = query.filter(ChillerData.timestamp >= start_date)
    if end_date:
        query = query.filter(ChillerData.timestamp <= end_date)
        
    datas = query.order_by(ChillerData.timestamp.asc()).all()
    
    if not datas:
        raise HTTPException(status_code=404, detail="No chiller data found for this ID in the given time range")
    return datas

@app.get("/chillers/latest_data")
def get_all_chillers_latest_data(db: Session = Depends(get_db)):
    chillers = db.query(Chiller).all()
    latest_data = []
    for chiller in chillers:
        latest_entry = db.query(ChillerData).filter(ChillerData.chiller_id == chiller.id).order_by(ChillerData.timestamp.desc()).first()
        if latest_entry:
            latest_data.append(latest_entry)
    return latest_data
