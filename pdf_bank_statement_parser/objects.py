from collections import namedtuple

Transaction = namedtuple(
    "transaction", ["date", "description", "amount", "balance", "bank_fee"]
)
