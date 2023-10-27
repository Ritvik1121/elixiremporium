from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
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

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


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
            num_available = connection.execute(sqlalchemy.text("""SELECT COALESCE(SUM(amount), 0) FROM potion_ledger WHERE  potion_id = :id"""), [{"id": potion.potion_id}]).first()[0]
            if num_available < potion.quantity:
                raise HTTPException(500, detail="Not enough potions of this type")

            result1 = connection.execute(sqlalchemy.text("""SELECT * FROM potion_inv WHERE id = :id"""), [{"id": potion.potion_id}])
            connection.execute(sqlalchemy.text("""INSERT INTO potion_ledger (transaction_id, amount, potion_id) 
                                               VALUES (:transaction_id, :amount, :potion_id)"""), 
                                               [{"transaction_id": transaction_id, "amount": (potion.quantity * -1), "potion_id": potion.potion_id}])
        gold_paid += (result1.first().cost * potion.quantity)
    
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (transaction_id, amount) VALUES (:transaction_id, :amount) """), [{"transaction_id": transaction_id, "amount": gold_paid}])
    



    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}