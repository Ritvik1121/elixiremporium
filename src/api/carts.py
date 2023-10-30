from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
from fastapi import FastAPI, HTTPException
from enum import Enum


#with db.engine.begin() as connection:
#        result = connection.execute(sqlalchemy.text(sql_to_execute))


offset = 0

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
    # stmt = """ SELECT potion_ledger.amount, potion_ledger.potion_id, carts.customer, potion_inv.sku, gold_ledger.amount, shop_transaction.id, shop_transactions.created_at FROM potion_ledger"""

    # if customer_name != "":
    #     stmt += f""" WHERE carts.customer = {customer_name}"""

    # if potion_sku != "":
    #     stmt += f""" WHERE potion_inv.sku = {potion_sku}"""

    # stmt += """ JOIN shop_transactions ON shop_transactions.id = potion_ledger.transaction_id 
    #         JOIN carts ON carts.transaction_id = potion_ledger.transaction_id
    #         JOIN potion_inv ON potion_inv.id = potion_ledger.potion_id 
    #         JOIN gold_ledger ON gold_ledger.transaction_id = potion_ledger.transaction_id
    #         ORDER BY shop_transactions.created_at """
    
    metadata_obj = sqlalchemy.MetaData()
    potions = sqlalchemy.Table("potion_ledger", metadata_obj, autoload_with=db.engine)
    pot_inv = sqlalchemy.Table("potion_inv", metadata_obj, autoload_with=db.engine)
    gold = sqlalchemy.Table("gold_ledger", metadata_obj, autoload_with=db.engine)
    transaction = sqlalchemy.Table("shop_transactions", metadata_obj, autoload_with=db.engine)
    carts = sqlalchemy.Table("carts", metadata_obj, autoload_with=db.engine)


    if sort_col == search_sort_options.timestamp:
        order_by = transaction.c.id
    elif sort_col == search_sort_options.customer_name:
        order_by = carts.c.customer
    elif sort_col == search_sort_options.item_sku:
        order_by = pot_inv.c.sku
    elif sort_col == search_sort_options.line_item_total:
        order_by = gold.c.amount
    else :
        assert False

    if sort_order == search_sort_order.desc :
        order_by = order_by.desc()
    elif sort_order == search_sort_order.asc :
        order_by = order_by.asc()

    if search_page != "":
        page = int(search_page)
    else:
        page = 0
    
    global offset
    offset += 5 * page
    
    t1 = sqlalchemy.join(transaction, potions, transaction.c.id == potions.c.transaction_id)
    t2 = sqlalchemy.join(gold, t1, gold.c.transaction_id == transaction.c.id)
    t3 = sqlalchemy.join(pot_inv, t2, pot_inv.c.id == potions.c.potion_id)
    t4 = sqlalchemy.join(carts, t3, carts.c.transaction_id == transaction.c.id)

    stmt = (
        sqlalchemy.select(
            gold.c.amount,
            carts.c.customer,
            potions.c.amount,
            transaction.c.created_at,
            transaction.c.id,
            pot_inv.c.sku
        )
        .limit(5)
        .offset(offset)
        .select_from(t4)  
        .order_by(order_by, transaction.c.created_at)
    )
    
    if customer_name != "":
        stmt = stmt.where(carts.c.customer.ilike(f"%{customer_name}%"))
    
    if potion_sku != "":
        stmt = stmt.where(pot_inv.c.sku.ilike(f"%{potion_sku}%"))

 

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
    

    print(result)

    output = []
    count = 0
    for person in result:
        count += 1
        print(person)
        output.append ({
            "line_item_id": person.id,
            "item_sku": f"{(-1 * person[2])} {person.sku.lower()} potion",
            "customer_name": person.customer,
            "line_item_total": person[0],
            "timestamp": person.created_at
        })

    prev = ""
    next = ""
    if offset >= 1:
        prev = "-1"
    if count == 5:
        next = "1"
    return {
        "previous": prev,
        "next": next,
        "results": output
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
        connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (transaction_id, amount) 
                                           VALUES (:transaction_id, :amount) """), [{"transaction_id": transaction_id, "amount": gold_paid}])
        connection.execute(sqlalchemy.text("""UPDATE carts 
                                           SET transaction_id = :transaction_id 
                                           WHERE id = :id"""), [{"transaction_id": transaction_id,  "id": cart_id}])




    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}