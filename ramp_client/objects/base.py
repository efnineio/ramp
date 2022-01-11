from .mixins import FromJsonMixin, ToJsonMixin, ToDictMixin
from datetime import datetime, date

class RampBaseObject(FromJsonMixin, ToJsonMixin, ToDictMixin):
    class_dict = {}
    list_dict = {}
    _read_only_fields = []
    _required_fields = []
    _doc_type = None

    @classmethod
    def get_endpoint(cls, client):

        return "{}/{}s".format(client.base_resource_path, cls._doc_type)  # no trailing slash


    def get_frontend_url(self, client=None):
        if client: self._client = client
        return "{}/business-overview/{}s/{}".format(client.base_frontend_url, self._doc_type, self.id)  # no trailing slash

    def get_object_api_endpoint(self, client=None):
        if client: self._client = client
        return self.get_endpoint(self._client) + "/" + self.id

    @classmethod
    def get(cls, id, client):
        resource_ep = cls.get_endpoint(client)
        ep = "{}/{}".format(resource_ep,id)
        res = client.hit_api(verb='GET', endpoint=ep)
        res.raise_for_status()
        json_data = res.json()
        obj = cls.from_json(json_data)
        obj._client = client
        return obj


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
        #pprint(json_data)
        objs = []
        for obj_data in json_data.get('data',[]):
            new_obj = cls.from_json(obj_data)
            new_obj._client=client
            objs.append(new_obj)

        return objs

