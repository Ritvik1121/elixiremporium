from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db



router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)

    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    gold_temp = 0

    for barrel in barrels_delivered:
       gold_temp += barrel.price
       match barrel.potion_type:
          case [1,0,0,0]:
            red_ml += barrel.ml_per_barrel
          case [0,0,1,0]:
            blue_ml += barrel.ml_per_barrel
          case [0,1,0,0]:
            green_ml += barrel.ml_per_barrel
          case [0,0,0,1]:
            dark_ml+= barrel.ml_per_barrel

    total_ml = red_ml + blue_ml + green_ml + dark_ml 
               
    
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("""INSERT INTO shop_transactions (description) VALUES (:transaction_string) RETURNING id"""), [{"transaction_string": f"Shop purchased {total_ml} ml and paid {gold_temp}"}])
      transaction_id = result.first().id

      if red_ml > 0:
        connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (transaction_id, amount, barrel_type) VALUES (:transaction_id, :amount, :barrel_type)"""), [{"transaction_id": transaction_id , "amount": red_ml, "barrel_type": [1, 0, 0, 0]}])
      if green_ml > 0:
        connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (transaction_id, amount, barrel_type) VALUES (:transaction_id, :amount, :barrel_type)"""), [{"transaction_id": transaction_id , "amount": green_ml, "barrel_type": [0, 1, 0, 0]}])
      if blue_ml > 0:
        connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (transaction_id, amount, barrel_type) VALUES (:transaction_id, :amount, :barrel_type)"""), [{"transaction_id": transaction_id , "amount": blue_ml, "barrel_type": [0, 0, 1, 0]}])
      if dark_ml > 0:
        connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (transaction_id, amount, barrel_type) VALUES (:transaction_id, :amount, :barrel_type)"""), [{"transaction_id": transaction_id , "amount": dark_ml, "barrel_type": [0, 0, 0, 1]}])
      connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (transaction_id, amount) VALUES (:transaction_id, :amount)"""), [{"transaction_id": transaction_id , "amount": (gold_temp * -1)}])

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """

    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT SUM(amount) FROM gold_ledger"))
    gold_temp = result.first()[0]

    print(gold_temp)

    red_price = 0
    blue_price = 0
    green_price = 0

    red_exists = False
    blue_exists = False 
    green_exists = False
    for barrel in wholesale_catalog:
      match barrel.sku:
        case "SMALL_RED_BARREL":
          red_price = barrel.price
          red_exists = True
        case "SMALL_BLUE_BARREL":
          blue_price = barrel.price
          blue_exists = True
        case "SMALL_GREEN_BARREL":
          green_price = barrel.price
          green_exists = True

    plan = []
    if red_exists and gold_temp >= red_price:
      plan.append(
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            })
      gold_temp = gold_temp - red_price

    if blue_exists and gold_temp >= blue_price:
      plan.append (
            {
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1,
            })
      gold_temp = gold_temp - blue_price

    if green_exists and gold_temp >= green_price:
      plan.append( {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            })
      gold_temp = gold_temp - green_price
      
    return plan
    
