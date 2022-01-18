from .base import RampBaseObject
from .mixins import SaveMixin, DeferredTaskMixin, IdempotencyMixin




class Card(SaveMixin, DeferredTaskMixin, IdempotencyMixin, RampBaseObject):
    _read_only_fields = ['is_physical', 'spending_restrictions', 'last_four', 'fulfillment', 'cardholder_name', 'id',
                         'has_program_overridden']
    _doc_type = "card"
    class_dict = {}
    list_dict = {}

    def get_frontend_url(self, client=None):
        # override
        if client: self._client = client
        return "{}/cards/transactions/card/{}".format(self._client.base_frontend_url, self.id)  # no trailing slash

    def set_limit(self, amount, client=None):
        if client: self._client = client

        data = {"spending_restrictions": {
            "amount": amount
        }
        }

        ep = self.get_object_api_endpoint()
        r = self._client.hit_api(verb='PATCH', endpoint=ep, json=data)
        #r.raise_for_status()
        self.refresh()


    def suspend(self, client=None, key=None):
        if client: self._client = client

        data = {
            "idempotency_key": key or self.get_key()
        }

        ep = self.get_object_api_endpoint() + '/deferred/suspension'
        r = self._client.hit_api(verb='POST', endpoint=ep, json=data)
        # print(r.text)

    def create_virtual(self, client=None, key=None):
        if client: self._client = client

        if getattr(self, 'id', None):
            raise ValueError("Can't Create a card with existing id")

        jdata = {
            "display_name": self.display_name,
            "user_id": self.user_id,
            "spending_restrictions": self.spending_restrictions,
            "idempotency_key": key or self.get_key()
        }

        ep = self.get_endpoint(self._client) + '/deferred/virtual'
        r = self._client.hit_api(verb='POST', endpoint=ep, json=jdata)

        r.raise_for_status()

        # print(r.json())
        deferred_task_id = r.json().get('id')
        r = self.run_deferred_task(deferred_task_id, self._client)
        # print("RESPONSE",r)
        if r.get('status') == 'SUCCESS':
            self.id = r.get('data').get('card_id')

            return self.refresh(client=self._client)
        
    def delete(self, client=None, key=None):
        if client: self._client = client

        data = {
            "idempotency_key": key or self.get_key()
        }

        ep = self.get_object_api_endpoint() + '/deferred/termination'
        r = self._client.hit_api(verb='POST', endpoint=ep, json=data)
        # print(r.text)

    def unsuspend(self, client=None, key=None):
        if client: self._client = client
        if not key: key = uuid.uuid4()
        data = {
            "idempotency_key": key or self.get_key
        }

        ep = self.get_object_api_endpoint() + '/deferred/unsuspension'
        r = self._client.hit_api(verb='POST', endpoint=ep, json=data)

        # print(r.text)

    def refresh(self, client=None):
        if client: self._client = client

        obj = self.get(self.id, self._client)
        self.__dict__.update(obj.__dict__)

        return self

# #        {
#           "display_name": "string",
#           "user_id": "a169451c-8525-4352-b8ca-070dd449a1a5",
#           "spending_restrictions": {
#             "amount": 0,
#             "interval": "DAILY",
#             "lock_date": "2019-08-24T14:15:22Z",
#             "categories": [
#               0
#             ],
#             "transaction_amount_limit": 0
#           },
#           "idempotency_key": "string"
#         }

#
# {
#     "cardholder_id": "667837ba-dedd-486d-a33e-a50f143d28d9",
#     "cardholder_name": "Matt Wolf",
#     "display_name": "Matthew Wolf",
#     "fulfillment": {
#         "card_personalization": {
#             "text": {
#                 "name_line_1": {
#                     "value": "Matt Wolf"
#                 },
#                 "name_line_2": {
#                     "value": "Cover"
#                 }
#             }
#         },
#         "shipping": {
#             "method": "TWO_DAY",
#             "recipient_address": {
#                 "address1": "1219 W 135TH ST",
#                 "address2": "",
#                 "city": "GARDENA",
#                 "country": "USA",
#                 "first_name": "Matt",
#                 "last_name": "Wolf",
#                 "postal_code": "90247",
#                 "state": "CA"
#             },
#             "shipment_info": {
#                 "date": "2021-03-26",
#                 "shipping_method": "UPS Second Business Day (2 business days)",
#                 "tracking_number": "1Z9V85180216072776"
#             }
#         }
#     },
#     "has_program_overridden": false,
#     "id": "5e0db59b-d474-4ae1-a598-4015936486a7",
#     "is_physical": true,
#     "last_four": "9670",
#     "spending_restrictions": {
#         "amount": 50000,
#         "auto_lock_date": null,
#         "blocked_categories": [],
#         "categories": [],
#         "interval": "MONTHLY",
#         "suspended": false,
#         "transaction_amount_limit": null
#     }
# }