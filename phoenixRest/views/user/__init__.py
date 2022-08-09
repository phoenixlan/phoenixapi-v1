from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from sqlalchemy import or_

from phoenixRest.mappers.user import map_user_no_positions

from phoenixRest.models import db
from phoenixRest.models.core.user import Gender, User
from phoenixRest.models.core.activation_code import ActivationCode

from phoenixRest.mappers.user import map_user_simple_with_secret_fields

from phoenixRest.utils import validate
from phoenixRest.resource import resource
from phoenixRest.views.user.instance import UserInstanceResource

from phoenixRest.roles import ADMIN, HR_ADMIN, TICKET_ADMIN

from datetime import datetime, date

import logging
log = logging.getLogger(__name__)


@resource(name='user')
class UserViews(object):
    __acl__ = [
        (Allow, Authenticated, 'current_get'),
        (Allow, ADMIN, 'all_get'),
        (Allow, HR_ADMIN, 'all_get'),

        (Allow, ADMIN, 'search'),
        (Allow, HR_ADMIN, 'search'),
        (Allow, TICKET_ADMIN, 'search'),

        (Allow, Everyone, 'register'),
        (Allow, Everyone, 'activate_user')

        # Authenticated pages
        #(Allow, Authenticated, Authenticated),
        #(Deny, Everyone, Authenticated),
    ]
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        if key in ['current', 'register', 'activate', 'search']:
            raise KeyError('')
        node = UserInstanceResource(self.request, key)
        
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=UserViews, name='current', request_method='GET', renderer='json', permission='current_get')
def get_current(context, request):
    return request.user

@view_config(context=UserViews, name='search', request_method='GET', renderer='json', permission='search')
def search_users(context, request):
    if 'query' not in request.GET:
        raise HTTPBadRequest("Missing query")

    query = request.GET['query']
    users = db.query(User).filter(or_(
        User.firstname.contains(query),
        User.lastname.contains(query),
        User.username.contains(query),
        User.email.contains(query)
    )).all()
    return [ map_user_simple_with_secret_fields(user) for user in users ]

@view_config(context=UserViews, name='', request_method='GET', renderer='json', permission='all_get')
def all_users(context, request):
    users = db.query(User).order_by(User.created).all()
    return [map_user_no_positions(user) for user in users]

def age(dob):
    today = date.today()
    years = today.year - dob.year
    if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
        years -= 1
    return years

@view_config(context=UserViews, name='register', request_method="POST", renderer='json', permission="register")
@validate(json_body={'username': str, 'firstname': str, 'surname': str, 'password': str, 'passwordRepeat': str, 'email': str, 'gender': str, "dateOfBirth": str, 'phone': str, 'address': str, 'zip': str, 'guardianPhone': str})
def register_user(context, request):
    if request.json_body["gender"] not in ['male', 'female']:
            raise HTTPBadRequest("Invalid gender") # Hi, foone
    
    if request.json_body["password"] != request.json_body["passwordRepeat"]:
        raise HTTPBadRequest("Password and repeat password does not match")

    existingUsername = db.query(User).filter(User.username == request.json_body["username"]).first()
    existingEmail = db.query(User).filter(User.email == request.json_body["email"]).first()
    existingPhone = db.query(User).filter(User.phone == request.json_body["phone"]).first()

    if existingUsername is not None or existingEmail is not None or existingPhone is not None:
        raise HTTPBadRequest("An user by this username, phone number, or e-mail already exists")

    birthdate = date.fromisoformat(request.json_body["dateOfBirth"])
    if request.json_body["gender"] == "male":
        gender = Gender.male
    elif request.json_body["gender"] == "female":
        gender = Gender.female
    else:
        raise HTTPBadRequest("Invalid gender")

    user = User(request.json_body["username"], request.json_body["email"], request.json_body["password"], request.json_body["firstname"], request.json_body["surname"], birthdate, gender, request.json_body["phone"], request.json_body["address"], request.json_body["zip"])
    if "guardianPhone" in request.json_body and len(request.json_body["guardianPhone"]) > 0:
        user.guardian_phone = request.json_body["guardianPhone"]
    elif age(birthdate) < 18:
        raise HTTPBadRequest("You need to provide a guardian phone number")

    # Create the activation code
    clientId = request.json_body.get("clientId")
    user.activation_code = ActivationCode(user, clientId)
    db.add(user)
    db.flush()

    # Now send activation e-mail
    request.mail_service.send_mail(request.json_body["email"], "Registrert konto", "registration.jinja2", {
        "mail": request.registry.settings["api.contact"],
        "activationUrl": "%s/user/activate?code=%s" % (request.registry.settings["api.root"], user.activation_code.code),
        "name": request.registry.settings["api.name"]
    })

    log.info("Registered new user with UUID %s" % user.uuid)

    return {
        'message': "An e-mail has been sent"
    }


@view_config(context=UserViews, name='activate', request_method='GET', renderer='templates/activation.jinja2', permission='activate_user')
@validate(get={"code": str})
def activate_account(context, request):
    code = request.GET["code"]
    activationCode = db.query(ActivationCode).filter(ActivationCode.code == code).first()

    if activationCode is None:
        log.info("Unable to find activation code %s" % code)
        return {
            'success': False,
            'mail': request.registry.settings["api.contact"],
            'name': request.registry.settings["api.name"]
        }
    else:
        db.delete(activationCode)
        redirectUrl = None
        if activationCode.client_id is not None:
            redirectUrl = request.registry.settings["oauth.%s.redirect_url" % activationCode.client_id]
        return {
            'success': True,
            'url': redirectUrl,
            'mail': request.registry.settings["api.contact"],
            'name': request.registry.settings["api.name"]
        }