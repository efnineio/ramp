import os
from urllib.parse import urljoin, urlencode
from flask import Flask, url_for, session, request
from flask import redirect
from authlib.integrations.flask_client import OAuth

## Globals
# Replace RAMP_CLIENT_ID and RAMP_CLIENT_SECRET with your app's
# corresponding values
RAMP_CLIENT_ID = os.getenv('RAMP_CLIENT_ID')
RAMP_CLIENT_SECRET = os.getenv('RAMP_CLIENT_SECRET')

RAMP_BASE_URL = 'https://app.ramp.com'
RAMP_API_BASE_URL = 'https://api.ramp.com'

RESOURCES_BASE_URL = urljoin(RAMP_API_BASE_URL,
               'v1/public/customer/resources/')
ACCESS_TOKEN_URL = urljoin(RAMP_API_BASE_URL, 'v1/public/customer/token')
AUTHORIZE_URL = urljoin(RAMP_BASE_URL, 'v1/authorize')
SCOPE = 'transactions'

app = Flask(__name__)
app.secret_key = '!secret'
app.config.update(
  RAMP_CLIENT_ID=RAMP_CLIENT_ID,
  RAMP_CLIENT_SECRET=RAMP_CLIENT_SECRET,
)

oauth = OAuth(app)
oauth.register(
  name='ramp',
  api_base_url=RESOURCES_BASE_URL,
  access_token_url=ACCESS_TOKEN_URL,
  authorize_url=AUTHORIZE_URL,
  client_kwargs={
    'scope': SCOPE,
  }
)


@app.route('/')
def homepage():
  token = session.get('token')
  if token:
    return f"""
      Token: {token}
      <form action="/get/transactions/pagination">
        Page: <input type="text" name="page" value=1><br>
        Page size: <input type="text" name="page_size" value=10><br>
        <input type="submit" value="Get transactions">
      </form>
      <br><a href="/logout">logout</a>
    """
  else:
    return """
      <a href="/login">login</a>
    """


@app.route('/login')
def login():
  redirect_uri = url_for('auth', _external=True)
  return oauth.ramp.authorize_redirect(redirect_uri)


@app.route('/auth')
def auth():
  # Note: it is NOT recommended to store your access token
  # in the session. Instead, it should be securely stored
  # somewhere outside of the browser.
  token = oauth.ramp.authorize_access_token()
  session['token'] = token
  return redirect('/')


@app.route('/logout')
def logout():
  session.pop('token', None)
  return redirect('/')


@app.route('/get/transactions/pagination')
def get_transactions_pagination():
  token = session['token']
  response = oauth.ramp.get(
      f'transactions/pagination?{urlencode(request.args)}', token=token)
  return f"""
    transactions: {response.json()}
  """