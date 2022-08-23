from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPBadRequest
)
from pyramid.security import Authenticated, Everyone, Deny, Allow

from sqlalchemy import or_

from phoenixRest.models import db
from phoenixRest.models.core.user import Gender, User, calculate_age
from phoenixRest.models.core.activation_code import ActivationCode
from phoenixRest.models.core.password_reset_code import PasswordResetCode

from phoenixRest.mappers.user import map_user_simple_with_secret_fields, map_user_with_secret_fields

from phoenixRest.utils import validate
from phoenixRest.resource import resource
from phoenixRest.views.user.instance import UserInstanceResource

from phoenixRest.roles import ADMIN, HR_ADMIN, TICKET_ADMIN

from datetime import datetime, date

import re

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
        if key in ['current', 'register', 'activate', 'search', 'forgot']:
            raise KeyError('')
        node = UserInstanceResource(self.request, key)
        
        node.__parent__ = self
        node.__name__ = key
        return node

@view_config(context=UserViews, name='current', request_method='GET', renderer='json', permission='current_get')
def get_current(context, request):
    return map_user_with_secret_fields(request.user, request)

@view_config(context=UserViews, name='search', request_method='GET', renderer='json', permission='search')
def search_users(context, request):
    if 'query' not in request.GET:
        request.response.status = 400
        return {
            "error": "Missing query"
        }

    query = request.GET['query']
    users = db.query(User).filter(or_(
        User.firstname.contains(query),
        User.lastname.contains(query),
        User.username.contains(query),
        User.email.contains(query)
    )).all()
    return [ map_user_simple_with_secret_fields(user, request) for user in users ]

@view_config(context=UserViews, name='', request_method='GET', renderer='json', permission='all_get')
def all_users(context, request):
    users = db.query(User).order_by(User.created).all()
    return [map_user_simple_with_secret_fields(user, request) for user in users]

email_regex = re.compile('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$')

@view_config(context=UserViews, name='register', request_method="POST", renderer='json', permission="register")
@validate(json_body={'username': str, 'firstname': str, 'surname': str, 'password': str, 'passwordRepeat': str, 'email': str, 'gender': str, "dateOfBirth": str, 'phone': str, 'address': str, 'zip': str, 'guardianPhone': str})
def register_user(context, request):
    if request.json_body["password"] != request.json_body["passwordRepeat"]:
        request.response.status = 400
        return {
            "error": "Password and repeat password does not match"
        }
    
    if len(request.json_body["password"]) < 6:
        request.response.status = 400
        return {
            "error": "Password is too short. Use at least 6 characters"
        }

    existingUsername = db.query(User).filter(User.username == request.json_body["username"]).first()
    existingEmail = db.query(User).filter(User.email == request.json_body["email"]).first()
    existingPhone = db.query(User).filter(User.phone == request.json_body["phone"]).first()

    if existingUsername is not None or existingEmail is not None or existingPhone is not None:
        request.response.status = 400
        return {
            "error": "An user by this username, phone number, or e-mail already exists"
        }
    
    email = request.json_body['email']
    if email_regex.match(email) is None:
        request.response.status = 400
        return {
            "error": "You must enter a valid e-mail address"
        }
    username = request.json_body['username']
    if len(username) < 1:
        request.response.status = 400
        return {
            "error": "An username is required"
        }
    
    firstname = request.json_body['firstname']
    surname = request.json_body['surname']

    if len(firstname) < 1 or len(surname) < 1:
        request.response.status = 400
        return {
            "error": "A name is required"
        }

    birthdate = date.fromisoformat(request.json_body["dateOfBirth"])
    if request.json_body["gender"] == "male":
        gender = Gender.male
    elif request.json_body["gender"] == "female":
        gender = Gender.female
    else:
        request.response.status = 400
        return {
            "error": "Invalid gender"
        }

    user = User(username, email, request.json_body["password"], firstname, surname, birthdate, gender, request.json_body["phone"], request.json_body["address"], request.json_body["zip"])
    if "guardianPhone" in request.json_body and len(request.json_body["guardianPhone"]) > 0:
        user.guardian_phone = request.json_body["guardianPhone"]
    elif calculate_age(birthdate) < 18:
        request.response.status = 400
        return {
            "error": "You need to provide a guardian phone number"
        }

    # Create the activation code
    client_id = request.json_body.get("clientId")
    if client_id not in request.registry.settings["oauth.valid_client_ids"].split(","):
        request.response.status = 400
        return {
            "error": "Invalid OAuth client ID"
        }
    user.activation_code = ActivationCode(user, client_id)
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

@view_config(context=UserViews, name='forgot', request_method="POST", renderer='json', permission="register")
@validate(json_body={'login': str, 'client_id': str})
def forgot_password(context, request):
    log.info("Processing forgot password request for %s" % request.json_body['login'])
    client_id = request.json_body.get("client_id")
    if client_id not in request.registry.settings["oauth.valid_client_ids"].split(","):
        request.response.status = 400
        return {
            "error": "Invalid OAuth client ID"
        }
    url = request.registry.settings["oauth.%s.redirect_url" % client_id]

    user = db.query(User).filter(or_(User.username == request.json_body['login'], User.email == request.json_body['login'])).first()
    if not user:
        log.warn("Got a forgot password request for an account that doesn't exist")
    else:
        resetCode = PasswordResetCode(user, client_id)
        db.add(resetCode)
        db.flush()
        request.mail_service.send_mail(user.email, "Glemt passord", "forgotten.jinja2", {
            "mail": request.registry.settings["api.contact"],
            "resetUrl": "%s/static/forgot_reset.html?code=%s&client_id=%s&redirect_uri=%s" % (request.registry.settings["api.root"], resetCode.code, client_id, url),
            "name": request.registry.settings["api.name"],
            "domain": request.registry.settings["api.mainpage"]
        })