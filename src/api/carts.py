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
        result = connection.execute(sqlalchemy.text("""INSERT INTO cart_items (cart_id, potion_id, quantity) 
                                                    SELECT :id, potion_inv.id, :quantity 
                                                    FROM potion_inv 
                                                    WHERE potion_inv.sku = :item_sku """), 
                                                    [{"id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity}])
    
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
        result = connection.execute(sqlalchemy.text("""SELECT * FROM cart_items WHERE cart_id = :id"""), [{"id": cart_id}])
        name = connection.execute(sqlalchemy.text("""SELECT customer FROM carts WHERE id = :id"""), [{"id": cart_id}]).first()[0]
        transaction_id = connection.execute(sqlalchemy.text("""INSERT INTO shop_transactions (description) VALUES (:description) RETURNING id """), [{"description": f"{name} purchased some potions"}]).first().id

    for potion in result :
        potions_bought += potion.quantity
        with db.engine.begin() as connection:
            result1 = connection.execute(sqlalchemy.text("""SELECT * FROM potion_inv WHERE id = :id"""), [{"id": potion.potion_id}])
            connection.execute(sqlalchemy.text("""INSERT INTO potion_ledger (transaction_id, amount, potion_id) 
                                               VALUES (:transaction_id, :amount, :potion_id)"""), 
                                               [{"transaction_id": transaction_id, "amount": (potion.quantity * -1), "potion_id": potion.potion_id}])
        gold_paid += (result1.first().cost * potion.quantity)
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (transaction_id, amount) VALUES (:transaction_id, :amount) """), [{"transaction_id": transaction_id, "amount": gold_paid}])
    



    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}