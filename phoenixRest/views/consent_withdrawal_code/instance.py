from operator import and_
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPBadRequest
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.tickets.ticket_voucher import TicketVoucher
from phoenixRest.models.core.consent_withdrawal_code import ConsentWithdrawalCode
from phoenixRest.models.core.user_consent import UserConsent

from phoenixRest.roles import ADMIN, TICKET_ADMIN

from phoenixRest.utils import validateUuidAndQuery

from datetime import datetime

import logging
log = logging.getLogger(__name__)

class ConsentWithdrawalCodeInstanceResource(object):
    def __acl__(self):
        acl = [
            # The UUID is supposed to act as a secret that you can use to stop further mail
            # without having to log in
            (Allow, Everyone, 'get'),
            (Allow, Everyone, 'use'),
        ]
        return acl

    def __init__(self, request, uuid):
        self.request = request

        self.consent_withdrawal_code_instance = validateUuidAndQuery(request, ConsentWithdrawalCode, ConsentWithdrawalCode.uuid, uuid)

        if self.consent_withdrawal_code_instance is None:
            raise HTTPNotFound("Consent withdrawal code not found")


@view_config(context=ConsentWithdrawalCodeInstanceResource, name='', request_method='GET', renderer='json', permission='get')
def get_consent_withdrawal_code(context, request):
    return context.consent_withdrawal_code_instance

@view_config(context=ConsentWithdrawalCodeInstanceResource, name='use', request_method='POST', renderer='json', permission='use')
def use_consent_withdrawal_code(context, request):
    existing_consent = request.db.query(UserConsent) \
        .filter(UserConsent.user == context.consent_withdrawal_code_instance.user) \
        .filter(UserConsent.consent_type == context.consent_withdrawal_code_instance.consent_type) \
        .all()
    
    if len(existing_consent) > 1:
        raise RuntimeError("Multiple consents exist, something is wrong")
    elif len(existing_consent) == 1:
        consent = existing_consent[0]

        request.db.delete(consent)
        request.db.delete(context.consent_withdrawal_code_instance)
        return {
            "message": "Consent withdrawn."
        }
    elif len(existing_consent) == 0:
        request.response.status = 400
        request.db.delete(context.consent_withdrawal_code_instance)
        return {
            "message": "No consent exists - already removed?"
        }
    