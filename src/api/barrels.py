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
    with db.engine.begin() as connection:
      result1 = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result1.first()
    
    red_ml = first_row.num_red_ml  
    blue_ml = first_row.num_blue_ml 
    green_ml = first_row.num_green_ml 
    dark_ml = first_row.num_dark_ml
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
               
    gold_lost = first_row.gold - gold_temp
    
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {red_ml}, num_green_ml = {green_ml}, num_blue_ml = {blue_ml}, gold = {gold_lost} WHERE id= 1"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result.first()

    red_price = 0
    blue_price = 0
    green_price = 0

    for barrel in wholesale_catalog:
      match barrel.sku:
        case "SMALL_RED_BARREL":
          red_price = barrel.price
        case "SMALL_BLUE_BARREL":
          blue_price = barrel.price
        case "SMALL_RED_BARREL":
          green_price = barrel.price

    
    gold_temp = first_row.gold

    plan = []
    if first_row.num_red_ml < 500 and gold_temp >= red_price:
      plan.append(
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            })
      gold_temp = gold_temp - red_price

    if first_row.num_blue_ml < 500 and gold_temp >= blue_price:
      plan.append (
            {
                "sku": "SMALL_BLUE_BARREL",
                "quantity": 1,
            })
      gold_temp = gold_temp - blue_price

    if first_row.num_green_ml < 500 and gold_temp >= green_price:
      plan.append( {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            })
      gold_temp = gold_temp - green_price
      
    return plan
    
