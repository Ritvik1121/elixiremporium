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
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO shop_transactions (description) VALUES (:description) RETURNING id"), [{"description": "Potions have been bought"}]).first().id

    red_ml_used = 0
    blue_ml_used = 0
    green_ml_used = 0
    
    dark_ml_used = 0
    
    count = 0
    for potion in potions_delivered:
        count += potion.quantity
        p_type = potion.potion_type
        red_ml_used += (p_type[0] * potion.quantity)
        green_ml_used += (p_type[1] * potion.quantity)
        blue_ml_used += (p_type[2] * potion.quantity)
        dark_ml_used += (p_type[3] * potion.quantity)

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("""INSERT INTO potion_ledger (transaction_id, potion_id, amount)
                                               SELECT :transaction_id, potion_inv.id, :amount
                                               FROM potion_inv
                                               WHERE potion_inv.potion_type = :potion_type
                                               """), [{"transaction_id": transaction_id, "potion_type": p_type, "amount": potion.quantity}])

    with db.engine.begin() as connection:   
        if red_ml_used > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (transaction_id, amount, barrel_type)
                                                VALUES (:transaction_id, :amount, :barrel_type )
                                               """), [{"transaction_id": transaction_id, "amount": (red_ml_used * -1), "barrel_type": [1,0,0,0]}])
        if green_ml_used > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (transaction_id, amount, barrel_type)
                                                VALUES (:transaction_id, :amount, :barrel_type )
                                               """), [{"transaction_id": transaction_id, "amount": (green_ml_used * -1), "barrel_type": [0,1,0,0]}])
        if blue_ml_used > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (transaction_id, amount, barrel_type)
                                                VALUES (:transaction_id, :amount, :barrel_type )
                                               """), [{"transaction_id": transaction_id, "amount": (blue_ml_used * -1), "barrel_type": [0,0,1,0]}])
        if dark_ml_used > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (transaction_id, amount, barrel_type)
                                                VALUES (:transaction_id, :amount, :barrel_type )
                                               """), [{"transaction_id": transaction_id, "amount": (dark_ml_used * -1), "barrel_type": [0,0,0,1]}])
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
        result2 = connection.execute(sqlalchemy.text("SELECT barrel_type, COALESCE(SUM(amount), 0) FROM ml_ledger GROUP BY barrel_type"))

    print(result2)

    red_temp = 0
    green_temp = 0
    blue_temp = 0
    dark_temp = 0
    for barrel in result2:
        match barrel[0]:
            case [1, 0, 0, 0]:
                red_temp = barrel[1]
            case [0, 1, 0, 0]:
                green_temp = barrel[1]
            case [0, 0, 1, 0]:
                blue_temp = barrel[1]
            case [0, 0, 0, 1]:
                dark_temp = barrel[1]
   

    print(red_temp)
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

