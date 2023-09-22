from re import template
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from phoenixRest.models.core.user import User
from phoenixRest.models.core.consent_withdrawal_code import ConsentWithdrawalCode
from phoenixRest.models.core.user_consent import UserConsent, ConsentType
from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_voucher import TicketVoucher
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.models.crew.application import Application
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.crew.position import Position

from phoenixRest.views.ticket_voucher.instance import TicketVoucherInstanceResource

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, TICKET_ADMIN, INFO_ADMIN

from sqlalchemy import and_, or_, extract, and_

from enum import Enum, auto

from datetime import datetime, timedelta

import mistune

import logging
log = logging.getLogger(__name__)

class MailType(Enum):
    event_notification = auto()
    participant_info = auto()
    crew_info = auto()
    competition_info = auto()

def get_recipients_by_category(request, category, argument):
    current_event = get_current_event(request)
    db = request.db
    current_user_uuid = request.user.uuid

    match category:
        case MailType.event_notification:
            consenting_users = db.query(UserConsent.user_uuid).subquery()
            query = db.query(User)

            # We don't want to send e-mails to people that already have tickets or are crew
            ticket_owner_uuids = db.query(Ticket.owner_uuid) \
                .filter(Ticket.event_uuid == current_event.uuid).subquery()

            applicant_uuids = db.query(Application.user_uuid) \
                .filter(Application.event_uuid == current_event.uuid).subquery()

            # Same for crews
            positions_with_crew_membership = db.query(Position.uuid) \
                .filter(Position.crew != None).subquery()

            # Fetch all position mappings for current event that are connected to a crew
            current_crew_list = db.query(PositionMapping.user_uuid) \
                .filter(and_(
                    or_(
                        PositionMapping.event_uuid == current_event.uuid,
                        PositionMapping.event_uuid == None)
                    ),
                    PositionMapping.position_uuid.in_(positions_with_crew_membership)
                ).subquery()

            # Even if people over the participant age limit could apply for crew,
            # we generally only want new crew members who are under the participant age limit.
            # No reason to send them an e-mail(?)
            if current_event.participant_age_limit_inclusive != -1:
                # Calculate what date you need to be born after to not be too old
                # on the day of the event start
                calculated_age_limit = current_event.start_time - timedelta(days=365*(current_event.participant_age_limit_inclusive+1))

                query = query.filter(User.birthdate >= calculated_age_limit)
            
            return query.filter(or_(
                    and_(
                        User.uuid.in_(consenting_users),
                        User.uuid.not_in(ticket_owner_uuids),
                        User.uuid.not_in(current_crew_list),
                        User.uuid.not_in(applicant_uuids)
                    ),
                    User.uuid == current_user_uuid)
                ).all()
        case MailType.participant_info:
            # Get all user UUIDs that have tickets for this event
            ticket_owner_uuids = db.query(Ticket.owner_uuid) \
                .filter(Ticket.event_uuid == current_event.uuid).subquery()
            
            return db.query(User) \
                .filter(or_(
                    User.uuid.in_(ticket_owner_uuids),
                    User.uuid == current_user_uuid
                )).all()
        case MailType.crew_info:
            # Fetch all positions with crew bindings
            # It is technically possible to have a position but not be in a crew
            # (For example, in order to give someone access to buying more tickets than usual)
            positions_with_crew_membership = db.query(Position.uuid) \
                .filter(Position.crew != None).subquery()

            # Fetch all position mappings for current event that are connected to a crew
            current_crew_list = db.query(PositionMapping.user_uuid) \
                .filter(and_(
                    or_(
                        PositionMapping.event_uuid == current_event.uuid,
                        PositionMapping.event_uuid == None)
                    ),
                    PositionMapping.position_uuid.in_(positions_with_crew_membership)
                ).subquery()
            
            # And then fetch all users that are in this list
            return db.query(User) \
                .filter(or_(
                    User.uuid.in_(current_crew_list),
                    User.uuid == current_user_uuid
                )).all()
        case _:
            raise RuntimeError("Invalid category: %s" % category)

def get_mail_details_by_category(request, category, user):
    match category:
        case MailType.event_notification:
            print("CONSENTS: ")
            print(user.consents)
            consents = [ consent for consent in user.consents if consent.consent_type == ConsentType.event_notification]

            # If we are the current user we are OK with no consent existing
            # we send all mail to the person who created it to build accountability and
            # allow them to see exactly what their users will receive
            if user.uuid == request.user.uuid:
                created_time = datetime.now()
                consent_occasion = "sending av denne e-posten"
                consent_withdrawal_url = "(Ingen URL)"
            else:
                if len(consents) == 0:
                    raise RuntimeError("User has no consent, something went wrong?")

                if len(consents) > 1:
                    raise RuntimeError("User has more than one consent, something went wrong?")
                
                consent = consents[0]

                created_time = consent.created
                consent_occasion = "registrering" if consent.source == "register" else "annen annledning: %s" % consent.source,

                # Calculate the consent withdrawal url
                withdrawal_codes = request.db.query(ConsentWithdrawalCode) \
                    .filter(and_(
                        ConsentWithdrawalCode.user == user,
                        ConsentWithdrawalCode.consent_type == ConsentType.event_notification
                    )).all()
                
                if len(withdrawal_codes) > 1:
                    raise RuntimeError("User has more than one withdrawal code. This should not be possible")
                
                withdrawal_code = None
                if len(withdrawal_codes) == 0:
                    withdrawal_code = ConsentWithdrawalCode(user, ConsentType.event_notification)
                    request.db.add(withdrawal_code)
                    request.db.flush()
                else:
                    withdrawal_code = withdrawal_codes[0]
                
                consent_withdrawal_url = withdrawal_code.get_withdrawal_url(request)
            
            return "gdpr_mail.jinja2", {
                "consent_time": created_time,
                "consent_occasion": consent_occasion,
                "consent_withdrawal_url": consent_withdrawal_url
            }
        case MailType.participant_info | MailType.crew_info:
            return "necessary_mail.jinja2", {}
        case _:
            raise RuntimeError("Unable to get mail details for mail category %s" % category)

@resource(name='email')
class MarketingResource(object):
    __acl__ = [
        (Allow, ADMIN, 'send_email'),
        (Allow, TICKET_ADMIN, 'send_email'),
        (Allow, INFO_ADMIN, 'send_email'),

        (Allow, ADMIN, 'test_email'),
        (Allow, TICKET_ADMIN, 'test_email'),
        (Allow, INFO_ADMIN, 'test_email'),
    ]
    def __init__(self, request):
        self.request = request

@view_config(name='dryrun', context=MarketingResource, request_method='POST', renderer='json', permission='test_email')
@validate(json_body={'recipient_category': str, 'subject': str, 'body': str})
def test_mail(context, request):
    """Returns the amount of people who will receive the mail"""

    argument = request.json_body.get('argument')

    category_str = request.json_body['recipient_category']
    try:
        category = MailType[category_str]
    except:
        request.response.status = 400
        return {
            "error": "Invalid category"
        }


    # Parse the markdown just to ensure no exception is raised. Maybe we do more validation in the future
    mistune.html(request.json_body['body'])

    recipients = get_recipients_by_category(request, category, argument)

    # Test that all the info extraction functions also work
    for recipient in recipients:
        template_file, template_context = get_mail_details_by_category(request, category, recipient)
    return {
        "count": len(recipients),
    }

@view_config(name='send', context=MarketingResource, request_method='POST', renderer='json', permission='test_email')
@validate(json_body={'recipient_category': str, 'subject': str, 'body': str})
def send_mail(context, request):
    argument = request.json_body.get('argument')

    category_str = request.json_body['recipient_category']
    try:
        category = MailType[category_str]
    except:
        request.response.status = 400
        return {
            "error": "Invalid category"
        }

    email_subject = request.json_body['subject']
    email_body = mistune.html(request.json_body['body'])

    recipients = get_recipients_by_category(request, category, argument)

    for recipient in recipients:
        template_file, template_context = get_mail_details_by_category(request, category, recipient)

        log.info("Sending mail for recipient %s" % recipient.uuid)
        request.service_manager.get_service('email').send_mail(recipient.email, email_subject, template_file, {
            "mail": request.registry.settings["api.contact"],
            "name": request.registry.settings["api.name"],
            "domain": request.registry.settings["api.mainpage"],
            "body": email_body,
            **template_context
        })

    return {
        "sent": len(recipients)
    }



