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
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result.first()
    num_red = first_row.num_red_potions
    num_green = first_row.num_green_potions
    num_blue = first_row.num_blue_potions

    if num_red > 0 and num_green > 0 and num_blue > 0:
        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": num_red,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                },
                 {
                    "sku": "BLUE_POTION_0",
                    "name": "blue potion",
                    "quantity": num_blue,
                    "price": 50,
                    "potion_type": [0, 0, 100, 0],
                },
                 {
                    "sku": "GREEN_POTION_0",
                    "name": "gren potion",
                    "quantity": num_green,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                }
            ]
    elif num_red > 0:
        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": num_red,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
    else :
        return []


