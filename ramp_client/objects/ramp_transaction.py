from .base import RampBaseObject

class RampTransaction(RampBaseObject):
    _doc_type = "transaction"
    class_dict = {}
    list_dict = {}

    def __init__(self):
        super(RampTransaction, self).__init__()