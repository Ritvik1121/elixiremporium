from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    
    """

    with db.engine.begin() as connection:
            num_available = connection.execute(sqlalchemy.text("""TRUNCATE shop_transactions CASCADE"""))
            id = connection.execute(sqlalchemy.text("""INSERT INTO shop_transactions (description) VALUES (:desc) RETURNING id"""), [{"desc": "Starting shop with 100 gold :)"}]).first().id
            connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (transaction_id, amount) VALUES (:transaction_id, :amount)"""), [{"transaction_id": id, "amount": 100}])

    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    # TODO: Change me!
    return {
        "shop_name": "Potion Shop",
        "shop_owner": "Potion Seller",
    }

