from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ServiceListing


app = FastAPI(title="SkillSwap")
db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/listings")
def read_listings(db: db_dependency):
    return db.query(ServiceListing).all()


@app.get("/listings/{listing_id}")
def read_listing(db: db_dependency, listing_id: int):
    listing = db.query(ServiceListing).filter(ServiceListing.id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
