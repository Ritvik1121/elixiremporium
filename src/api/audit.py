from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(amount), 0) FROM gold_ledger")).first()[0]
        ml_barrels = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(amount), 0) FROM ml_ledger")).first()[0]
        num_potions = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(amount), 0) FROM potion_ledger")).first()[0]
    
    return {"number_of_potions": num_potions, "ml_in_barrels": ml_barrels, "gold": gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
