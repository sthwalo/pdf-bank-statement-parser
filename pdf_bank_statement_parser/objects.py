from collections import namedtuple

Transaction = namedtuple(
    "Transaction", ["date", "description", "amount", "balance", "bank_fee"]
)
