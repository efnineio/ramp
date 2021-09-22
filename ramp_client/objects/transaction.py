from .base import RampBaseObject

from .base import RampBaseObject

class CardHolder(RampBaseObject):
    _doc_type = "card_holder"
    class_dict = {}
    list_dict = {}

    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __init__(self):
        super(CardHolder, self).__init__()

class Transaction(RampBaseObject):
    _doc_type = "transaction"
    class_dict = {"card_holder":CardHolder}
    list_dict = {}

    def __init__(self):
        super(Transaction, self).__init__()