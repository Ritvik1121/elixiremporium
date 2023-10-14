from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from fastapi import FastAPI, HTTPException

#with db.engine.begin() as connection:
#        result = connection.execute(sqlalchemy.text(sql_to_execute))


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
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""INSERT INTO carts (customer) VALUES (:customer_string) RETURNING id"""), [{"customer_string": new_cart.customer}])

    return {"cart_id": result.first().id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(""" SELECT * FROM carts WHERE id = :cart_id"""), [{"cart_id": cart_id}])
    cart = result.first()
    cart1 = {
        "id": cart.id,
        "customer": cart.customer,
        "payment": cart.payment
    }
    return cart1


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""INSERT INTO cart_items (cart_id, sku, quantity) VALUES (:id, :item_sku, :quantity) """), [{"id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity}])
    
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potions_bought = 0
    gold_paid = 0

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""UPDATE carts SET payment = :payment WHERE id = :id"""), [{"payment": cart_checkout.payment, "id": cart_id}])

  
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT * FROM cart_items WHERE cart_id = :id"""), [{"id": cart_id}])

    for potion in result :
        potions_bought += potion.quantity
        with db.engine.begin() as connection:
            result1 = connection.execute(sqlalchemy.text("""SELECT * FROM potion_inv WHERE sku = :sku"""), [{"sku": potion.sku}])
            connection.execute(sqlalchemy.text("""UPDATE potion_inv SET inventory = inventory - :quantity WHERE sku = :sku"""), [{"quantity": potion.quantity, "sku": potion.sku}])
        gold_paid += (result1.first().cost * potion.quantity)
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""UPDATE global_inventory SET gold = gold + :gold_paid WHERE id = 1"""), [{"gold_paid": gold_paid}])
    



    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}