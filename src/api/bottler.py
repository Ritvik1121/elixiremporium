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
    blue_ml_used = 0
    green_ml_used = 0
    
    dark_ml_used = 0
    

    for potion in potions_delivered:
        p_type = potion.potion_type
        red_ml_used += (p_type[0] * potion.quantity)
        green_ml_used += (p_type[1] * potion.quantity)
        blue_ml_used += (p_type[2] * potion.quantity)
        dark_ml_used += (p_type[3] * potion.quantity)

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("""UPDATE potion_inv 
                                               SET inventory = inventory + :potion_quantity 
                                               WHERE potion_type = :p_type"""), [{"potion_quantity": potion.quantity, "p_type": p_type}])
    
    new_red_ml = first_row.num_red_ml - red_ml_used
    new_green_ml = first_row.num_green_ml - green_ml_used
    new_blue_ml = first_row.num_blue_ml - blue_ml_used
    new_blue_ml = first_row.num_dark_ml - dark_ml_used

   
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {new_red_ml}, num_green_ml = {new_green_ml}, num_blue_ml = {new_blue_ml} WHERE id= 1"))
    

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
        result = connection.execute(sqlalchemy.text("SELECT * FROM potion_inv")).all()
    
    with db.engine.begin() as connection:
        result2 = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result2.first()
    red_temp = first_row.num_red_ml
    blue_temp = first_row.num_blue_ml
    green_temp = first_row.num_green_ml
    dark_temp = first_row.num_dark_ml
    potions_possible = []
    
    while red_temp > 0 or green_temp > 0 or blue_temp > 0 or dark_temp > 0:
        for potion in result:
            p_type = potion.potion_type
            if red_temp >= p_type[0] and green_temp >= p_type[1] and blue_temp >= p_type[2] and dark_temp >= p_type[3]:
                potions_possible.append({
                    "potion_type": potion.potion_type,
                    "quantity": 1,
                })
                red_temp = red_temp - p_type[0]
                green_temp = green_temp - p_type[1]
                blue_temp = blue_temp - p_type[2]
                dark_temp = dark_temp - p_type[3]

    return potions_possible

