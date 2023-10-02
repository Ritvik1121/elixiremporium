from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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
    """ """
    carts[cart_id][item_sku] = cart_item.quantity
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result.first()

    potions_bought = carts[cart_id]["RED_POTION_0"]
    gold_paid = potions_bought * 50

    potions_final = first_row.num_red_potions - potions_bought
    gold_final = first_row.gold + gold_paid

    if potions_bought > first_row.num_red_potions:
        potions_final = first_row.num_red_potions
        gold_final = first_row.gold

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = {potions_final},  gold = {gold_final} WHERE id= 1"))


    return {"total_potions_bought": potions_final, "total_gold_paid": gold_final}