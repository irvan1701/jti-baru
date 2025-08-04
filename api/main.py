from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Chiller, ChillerData

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

# Endpoint untuk mendapatkan data historis chiller
@app.get("/chiller_datas/{chiller_id}")
def get_chiller_datas(chiller_id: str, db: Session = Depends(get_db)):
    datas = db.query(ChillerData).filter(ChillerData.chiller_id == chiller_id).all()
    if not datas:
        raise HTTPException(status_code=404, detail="Chiller data not found for this ID")
    return datas