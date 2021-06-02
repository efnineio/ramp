import requests
import urllib.parse as urlparse
from urllib.parse import urlencode, parse_qs

class RampClient(object):
    base_url = 'https://api.ramp.com'
    base_resource_path = '/v1/public/customer/resources'
    auth_url = "https://app.ramp.com/v1/authorize"
    token_url = 'https://api.ramp.com/v1/public/customer/token'
    scopes = "transactions"

    def get_auth_url(self):

        # auth request # just go to it in a browser

        params = {'response_type': 'code',
                  'scope': self.scopes,
                  'client_id': self.client_id,
                  'redirect_uri': self.redirect_uri
                  }

        url_parts = list(urlparse.urlparse(self.auth_url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update(params)

        url_parts[4] = urlencode(query)
        full_auth_url = urlparse.urlunparse(url_parts)

        return full_auth_url

    def exchange_token(self, url=None, code=None):

        if url is not None:
            parsed = urlparse.urlparse(url)
            code = parse_qs(parsed.query)['code'][0]

        data = {'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri
                }
        # print(data)
        res_2 = requests.post(self.token_url, data=data, auth=(self.client_id, self.client_secret))
        res_2.raise_for_status()

        self.token = res_2.json()['access_token']

        return self.token

    def manual_auth_flow(self):
        #todo
        pass

    def get_session(self):
        if self.s:
            return self.s
        else:
            if not self.token:
                print("no token - run auth flow" )
                raise ValueError
            self.build_auth()
            return self.s

    def build_auth(self):
        self.s = requests.Session()

        self.s.headers.update({
            "Authorization": "Bearer {}".format(self.token)
        })

    def hit_api(self, verb, endpoint, params=None, data=None, json=None, headers={}):
        url = "{}{}".format(self.base_url, endpoint)
        print(url)
        s = self.get_session()
        s.headers.update(headers)
        res = s.request(verb, url=url, data=data, params=params, json=json)
        return res

    def __init__(self, token=None, client_id= None, client_secret=None, redirect_uri=None):
        self.s = None
        self.token = token
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

