from fastapi import APIRouter
import sqlalchemy
from src import database as db


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT potion_inv.id, potion_inv.sku, potion_inv.cost, potion_inv.potion_type, SUM(potion_ledger.amount) AS amount
                                                    FROM potion_inv
                                                    JOIN potion_ledger ON potion_ledger.potion_id = potion_inv.id
                                                    GROUP BY potion_inv.id, potion_ledger.amount, potion_inv.sku, potion_inv.cost, potion_inv.potion_type
                                                    """))

    print(result)
    catalog = []

    for potion in result :
        if potion.amount > 0:
            catalog.append ( {
                "sku": potion.sku,
                "quantity": potion.amount,
                "price": potion.cost,
                "potion_type": potion.potion_type
                })
            
    return catalog


