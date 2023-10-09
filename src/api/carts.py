from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from fastapi import FastAPI, HTTPException

#with db.engine.begin() as connection:
#        result = connection.execute(sqlalchemy.text(sql_to_execute))

carts = {}
g_cart_id = 0

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global g_cart_id
    g_cart_id += 1

    carts[g_cart_id] = {"customer": new_cart.customer}
    return {"cart_id": g_cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """

    return carts[cart_id]


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    
    
    carts[cart_id][item_sku] = cart_item.quantity
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    print(cart_checkout.payment)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result.first()

    red_bought = 0
    blue_bought = 0
    green_bought = 0
    if "RED_POTION_0" in carts[cart_id].keys():
        red_bought = carts[cart_id]["RED_POTION_0"] 
    if "BLUE_POTION_0" in carts[cart_id].keys():
        blue_bought = carts[cart_id]["BLUE_POTION_0"]
    if "GREEN_POTION_0" in carts[cart_id].keys():
        green_bought = carts[cart_id]["GREEN_POTION_0"]

    potions_bought = red_bought + blue_bought + green_bought
    gold_paid = potions_bought * 50

    #Updating potion values to put back into database
    red_final = first_row.num_red_potions - red_bought
    green_final = first_row.num_green_potions - green_bought
    blue_final = first_row.num_blue_potions - blue_bought
    
    #updating gold 
    gold_final = first_row.gold + gold_paid

    #case if potions in cart are more than potions in db
    #if red_bought > first_row.num_red_potions or blue_bought > first_row.num_blue_potions or green_bought > first_row.num_green_potions:
    #    raise HTTPException(status_code = 500, detail ="too many potions in shop")


    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {red_final},  num_green_potions = {green_final}, num_blue_potions = {blue_final}, gold = {gold_final} WHERE id= 1"))


    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}