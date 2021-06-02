from .mixins import FromJsonMixin, ToJsonMixin, ToDictMixin
from datetime import datetime, date

class RampBaseObject(FromJsonMixin, ToJsonMixin, ToDictMixin):
    class_dict = {}
    list_dict = {}
    _required_fields = []
    _doc_type = None
    @classmethod
    def get_endpoint(cls, client):
        return "{}/{}s".format(client.base_resource_path, cls._doc_type)  # no trailing slash

    @classmethod
    def filter(cls, client, pagination=False, **kwargs):

        params = {}

        for key, value in kwargs.items():
            if isinstance(value, date):
                value = datetime.combine(value, datetime.min.time()).isoformat()
            elif isinstance(value, date):
                value = value.isoformat()

            if value is not None:
                params.update({key: value})

        #print(params)
        ep = cls.get_endpoint(client)

        res = client.hit_api(verb='GET', endpoint=ep, params=params)

        # print(res.status_code)
        res.raise_for_status()
        json_data = res.json()
        from pprint import pprint

        objs = []
        for obj_data in json_data:
            objs.append(cls.from_json(obj_data))

        return objs

