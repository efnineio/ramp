import requests
import backoff
import urllib.parse as urlparse
from urllib.parse import urlencode, parse_qs
import json
from pprint import pprint
from enum import Enum

class GrantType(Enum):
    """Represents an OAuth grant type supported by Ramp"""

    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"

class RampClient(object):
    base_url = 'https://api.ramp.com'
    #base_resource_path = '/v1/public/customer/resources'
    base_resource_path = "/developer/v1"
    base_frontend_url = 'https://app.ramp.com'

    auth_url = "https://app.ramp.com/v1/authorize"
    #token_url = 'https://api.ramp.com/v1/public/customer/token'
    token_url = 'https://api.ramp.com/developer/v1/token'
    #scopes = ["transactions:read"]

    def get_auth_url(self):

        # auth request # just go to it in a browser

        if self.client_id is None:
            raise ValueError("Need to define a client secret to auth")
        params = {'response_type': 'code',
                  'scope': " ".join(self.scopes),
                  'client_id': self.client_id,
                  'redirect_uri': self.redirect_uri
                  }

        url_parts = list(urlparse.urlparse(self.auth_url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update(params)

        url_parts[4] = urlencode(query)
        full_auth_url = urlparse.urlunparse(url_parts)

        return full_auth_url






    # def is_authed(self):
    #     test_url = "{}/transactions/c7f4c7fb-488e-471f-92d3-f352fcf2d464".format(self.base_resource_path)#todo temp
    #     res = self.hit_api('GET',test_url)
    #     if res.status_code == 401:
    #         return False
    #     elif res.status_code == 200:
    #         return True
    #     else:
    #         raise ValueError("Can't determine if auth'd")


    def load_creds_file(self):

        with open(self.creds_file, 'r') as f:
            strConfig = f.read()

        creds_data = json.loads(strConfig)
        # print(creds_data)
        self.refresh_token = creds_data.get('refresh_token')
        self.client_secret = creds_data.get('client_secret')
        self.redirect_uri = creds_data.get('redirect_uri')
        self.client_id = creds_data.get('client_id')
        self.scopes = creds_data.get('scopes')
        # print("LOADING CREDS FILE", self.refresh_token)

    def get_session(self):
        if self.s:
            return self.s
        else:
            self.build_auth()
            # print(self.refresh_token)
            return self.s

    def save_creds_file(self):
        creds = {"client_id": self.client_id,
                 "client_secret": self.client_secret,
                 "redirect_uri": self.redirect_uri,
                 "refresh_token": self.refresh_token,
                 "scopes":self.scopes

                 }

        with open(self.creds_file, 'w') as f:
            f.write(json.dumps(creds, indent=4))

    def exchange_token(self, url=None, code=None):

        if url is not None:
            parsed = urlparse.urlparse(url)
            code = parse_qs(parsed.query)['code'][0]

        if self.grant_type is GrantType.CLIENT_CREDENTIALS:
            data = {
                "grant_type": "client_credentials",
                "scope": " ".join(self.scopes) if isinstance(self.scopes, (list, tuple)) else self.scopes,
            }
        elif self.grant_type is GrantType.AUTHORIZATION_CODE and code:
            data = {'grant_type': "authorization_code",
                    'code': code,
                    'redirect_uri': self.redirect_uri
                    }
        elif self.refresh_token:
            data = {'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token
                    }

        res_2 = requests.post(self.token_url, data=data, auth=(self.client_id, self.client_secret))
        res_2.raise_for_status()

        #pprint(res_2.json())
        json_response = res_2.json()
        self.access_token = json_response['access_token']

        new_refresh_token = json_response.get('refresh_token')
        if new_refresh_token and new_refresh_token != self.refresh_token:
            self.refresh_token = new_refresh_token
            self.save_creds_file()

        return self.access_token

    def build_auth(self):
        self.s = requests.Session()
        # print(self.refresh_token, "refresh token")
        # print(self.access_token, "access_token")

        if self.grant_type is GrantType.CLIENT_CREDENTIALS or (self.refresh_token and not self.access_token):
            # print("REFRESHING")
            try:
                self.exchange_token()
            except Exception as e:
                # print("ERROR exchanging token")
                raise e
        else:
            pass
            # print("NOT REFRESHING")

        self.s.headers.update({
            "Authorization": "Bearer {}".format(self.access_token)
        })

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_tries=8,
        max_time=120,
        giveup=lambda err: (
            getattr(err, "response", None) is None or err.response.status_code != 429
        ),
    )
    def hit_api(
        self, 
        verb, 
        endpoint, 
        params=None, 
        data=None, 
        json=None, 
        headers=None, 
        retry: bool = True, 
        **kwargs,
    ):
        url = "{}{}".format(self.base_url, endpoint)
        # print(url)
        s = self.get_session()

        if headers is not None:
            s.headers.update(headers)

        default_timeout = kwargs.pop("timeout", 60)

        #print (s.headers)
        res = s.request(
            verb, 
            url=url, 
            data=data, 
            params=params, 
            json=json,
            timeout=default_timeout,
            **kwargs,
        )
        # print(res.status_code)
        if res.status_code == 401:
            # print("need to re auth")
            self.access_token = None
            self.build_auth()
            s = self.get_session()
            res = s.request(
                verb, 
                url=url, 
                data=data, 
                params=params, 
                json=json,
                timeout=default_timeout,
                **kwargs,
            )
            # print("second status code", res.status_code)
        # TODO: Not sure if they send the `Retry-After` header.
        # Something to consider in the the future.
        if retry and res.status_code == 429:
            # To allow users to decide if they
            # want to retry, we need to ensure 429-exceptions
            # aren't thrown so it never makes through `backoff`.
            res.raise_for_status()

        return res

    def __init__(self, access_token=None,
                 client_id=None,
                 client_secret=None,
                 redirect_uri=None,
                 creds_file=None, scopes=None, grant_type: GrantType = GrantType.AUTHORIZATION_CODE):

        self.s = None

        self.access_token = access_token
        self.refresh_token = None
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.creds_file = creds_file
        self.scopes = scopes
        self.grant_type = grant_type

        if creds_file:
            self.access_token = None
            self.load_creds_file()
