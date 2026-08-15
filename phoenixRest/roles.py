import uuid

def role_lambda(template):
    """Helper that returns a lambda that when given an UUID returns the correct role.
    Performs some validation to stop obviously invalid values from being provided"""
    def inner(brand_uuid):
        # Final line of defense against bad programming
        # Hoping a ValueError here crashes and burns a call that may generate an invalid role
        if not isinstance(brand_uuid, uuid.UUID):
            uuid.UUID(brand_uuid)
        return template % brand_uuid
    return inner


ADMIN = lambda: "role:admin" # Site administrator. Full access to PII and everything.

BRAND_ADMIN = role_lambda("role:brand:%s") # Admin for a brand
CHIEF = role_lambda("role:brand:%s:chief") # Chief for a crew
MEMBER = role_lambda("role:brand:%s:member") # Crew member

TICKET_ADMIN = role_lambda("role:brand:%s:ticket_admin") # Admin for the ticket part of the site
TICKET_CHECKIN = role_lambda("role:brand:%s:ticket_checkin") # Neccesary for checking in users
INFO_ADMIN = role_lambda("role:brand:%s:info_admin") # Access to publish information(agenda + infoscreen later)
COMPO_ADMIN = role_lambda("role:brand:%s:compo_admin") # Admin for compos
NFC_ADMIN = role_lambda("role:brand:%s:nfc_admin") # Admin for the NFC system
HR_ADMIN = role_lambda("role:brand:%s:hr_admin") # Admin for the HR component of the webiste
CREW_CARD_PRINTER = role_lambda("role:brand:%s:crew_card_printer") # Can print crew cards

TICKET_WHOLESALE = role_lambda("role:brand:%s:ticket_wholesale") # Bypasses the max ticket purchase limit
TICKET_BYPASS_TICKETSALE_START_RESTRICTION = role_lambda("role:brand:%s:ticket_bypass_ticketsale_start_restriction") # Allows you to buy a ticket any time
