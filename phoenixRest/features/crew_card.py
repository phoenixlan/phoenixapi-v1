from PIL import Image, ImageDraw, ImageFont,  ImageColor
import qrcode
import json 
import requests
import os

from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.crew.position import Position

from sqlalchemy import and_, or_

import logging
log = logging.getLogger(__name__)

#Define bacgkround size 
width = 1920
height = width*(54/86)
height = int(height)

log.info("Loading crew card assets")

fnt = ImageFont.truetype("assets/NotoSans-Medium.ttf", 60)
logo = Image.open("assets/logo_card.png")

def generate_badge(request, user, event):
    name = "%s %s" % (user.firstname, user.lastname)

    candidate_mappings = request.db.query(PositionMapping).join(Position).filter(and_( \
        PositionMapping.user == user, \
        or_( \
            PositionMapping.event == None, \
            PositionMapping.event == event \
        ) \
    )).all()

    crew_mappings = list(filter(lambda mapping: mapping.position.crew_uuid is not None, candidate_mappings))

    # Get a fallback color
    crew_farge = crew_mappings[0].position.crew.hex_color if len(crew_mappings) > 0 else "#ffffff";

    if len(candidate_mappings) == 0:
        raise RuntimeError("User has crew mappings - unable to build crew card")
    
    # Generate list of special positions and positions that traverse events. Both require vanity to be set in order to count.
    special_positions = list(filter(lambda mapping: mapping.position.name != None and mapping.position.is_vanity, candidate_mappings))
    infinite_positions = list(filter(lambda mapping: mapping.event == None and mapping.position.is_vanity, candidate_mappings))

    # Use the special positions to generate the "correct" title and color
    title = "Person"
    if len(special_positions) > 0:
        title = special_positions[0].position.name
        if special_positions[0].position.crew_uuid is not None:
            crew_farge = special_positions[0].position.crew.hex_color
    elif len(infinite_positions) > 0:
        title = infinite_positions[0].position.get_title()
        crew_farge = infinite_positions[0].position.crew.hex_color
    else:
        title = candidate_mappings[0].position.get_title()

    event_name = event.name
    age = "%s år" % user.get_age()
    
    if user.avatar is None:
        raise RuntimeError("Unable to generate crew card - no avatar")

    qrcode_data = "phoenix-crew:%s" % user.uuid
    
    photo = Image.open(os.path.join(request.registry.settings["avatar.directory_sd"], "%s.%s" % (user.avatar.uuid, user.avatar.extension)))
    qrid = qrcode.make(qrcode_data)
    background = Image.new("RGB", (height, width), '#ffffff')
    draw = ImageDraw.Draw(background)

    #bottom background
    draw.rectangle([(0,1790), (width, 1920)] , fill=(crew_farge))
    draw.text((200, 1200), name, font=fnt, fill=(0,0,0)) 
    draw.text((200, 1280), title, font=fnt, fill=(0,0,0))
    draw.text((200, 1360), age, font=fnt, fill=(0,0,0))
    draw.text((30,1670 ), event_name, font=fnt, fill=(0,0,0))
    #draw.text((530,1815 ), crew, font=fnt, fill=(0,0,0))
    back_img = background.copy() 
    back_img.paste(logo,( 302, 50))
    back_img.paste(photo,( 200, 550))
    back_img.paste(qrid, (802, 1380))

    return back_img
