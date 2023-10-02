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
    gold_temp = 0 

    for barrel in barrels_delivered:
       match barrel.sku:
          case "SMALL_RED_BARREL":
            red_ml += barrel.ml_per_barrel
            gold_temp += barrel.price
    
    gold_lost = first_row.gold - gold_temp
    
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = {red_ml}, gold = {gold_lost} WHERE id= 1"))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    with db.engine.begin() as connection:
      result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result.first()

    if first_row.num_red_potions < 10:
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 1,
            }
        ]
    else :
        return [
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": 0,
            }
        ]
    
