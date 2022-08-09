
from phoenixRest.models import get_postgresql_url

def initTestingDB():
    from sqlalchemy import create_engine
    from phoenixRest.models import (
        db,
        Base
        )

    username = os.environ['POSTGRES_USER']
    password = os.environ['POSTGRES_PASSWORD']
    host = os.environ['DB_HOST']

    engine = create_engine(get_postgresql_url(username, password, host, "phoenix"))
    db.configure(bind=engine)
    Base.metadata.bind = engine
    #with transaction.manager:
        #model = Page(title='FrontPage', body='This is the front page')
        #DBSession.add(model)
    return db

def authenticate(app, username, password):
    res = app.post_json('/oauth/auth', dict({
        'login': username,
        'password': password
        }), status=200)
    code = res.json_body['code']
    print("Authenticated, got code: %s" % code)

    # Now try getting a token and refresh token
    res = app.post_json('/oauth/token', dict({
        'grant_type': 'code',
        'code': code
        }), status=200)

    refresh_token = res.json_body['refresh_token']
    
    return res.json_body['token'], res.json_body['refresh_token']
