from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ServiceListing, User
from router import auth
from schemas import ListingCreate, ListingUpdate


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


@app.patch("/listings/{listing_id}")
def update_listing(user: user_dependency, db: db_dependency, listing_id: int, updated_listing: ListingUpdate):
    listing = read_listing(db, listing_id)
    if listing.provider_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only update your own listings")

    update_data = updated_listing.model_dump(exclude_unset=True)
    if None in update_data.values():
        raise HTTPException(status_code=422, detail="Listing fields cannot be null")

    for key, value in update_data.items():
        setattr(listing, key, value)

    db.commit()
    return {"message": "Listing updated successfully"}


@app.delete("/listings/{listing_id}", status_code=204)
def delete_listing(user: user_dependency, db: db_dependency, listing_id: int):
    listing = read_listing(db, listing_id)
    if listing.provider_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own listings")

    db.delete(listing)
    db.commit()
