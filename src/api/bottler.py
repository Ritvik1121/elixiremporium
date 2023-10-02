from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

#with db.engine.begin() as connection:
 #       result = connection.execute(sqlalchemy.text(sql_to_execute))

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print(potions_delivered)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result.first()
    red_ml_used = 0
    red_count = 0
    
    for potion in potions_delivered:
        match potion.potion_type:
            case [100, 0, 0, 0]:
                red_ml_used += (100 * potion.quantity)
                red_count += potion.quantity
    
    new_red_ml = first_row.num_red_ml - red_ml_used

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {new_red_ml},  num_red_potions = {red_count} WHERE id= 1"))
    

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result.first()

    potions_possible = first_row.num_red_ml // 100

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": potions_possible,
            }
        ]

