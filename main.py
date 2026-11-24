from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ServiceListing, User
from router import auth
from schemas import ListingCreate


app = FastAPI(title="SkillSwap")
app.include_router(auth.router)
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth.get_current_user)]


@app.get("/listings")
def read_listings(db: db_dependency):
    return db.query(ServiceListing).all()


@app.get("/listings/{listing_id}")
def read_listing(db: db_dependency, listing_id: int):
    listing = db.query(ServiceListing).filter(ServiceListing.id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@app.post("/listings", status_code=201)
def create_listing(user: user_dependency, db: db_dependency, new_listing: ListingCreate):
    provider = db.query(User).filter(User.id == user["user_id"]).first()
    if provider is None or provider.role != "provider":
        raise HTTPException(status_code=403, detail="Only providers can create listings")

    listing = ServiceListing(**new_listing.model_dump(), provider_id=provider.id)
    db.add(listing)
    db.commit()
    return {"id": listing.id, "message": "Listing created successfully"}
