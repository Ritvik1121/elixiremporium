from fastapi import APIRouter
import sqlalchemy
from src import database as db


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM potion_inv")).all()

    catalog = []

    for potion in result :
        if potion.inventory > 0:
            catalog.append ( {
                "sku": potion.sku,
                "quantity": potion.inventory,
                "price": potion.cost,
                "potion_type": potion.potion_type
                })
            
    return catalog


