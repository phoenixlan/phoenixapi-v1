from pyramid.httpexceptions import (
    HTTPBadRequest,
)

import functools
import uuid

import secrets
import string

from phoenixRest.models import db

"""
This function assumes the views have two arguments: context, request.
TODO: autodetect and compensate for views not having this
"""
def validate(get=[], json_body={}, post={}):
	def validate_inner(func):
		@functools.wraps(func)
		def inner(*args, **kwargs):
			for key in get:
				if key not in args[1].GET: #aaa
					raise HTTPBadRequest('Lacking get parameters')
			for key in json_body:
				if key not in args[1].json_body:
					raise HTTPBadRequest('Lacking json parameter: %s' % key)
				if type(args[1].json_body[key]) != json_body[key]:
					raise HTTPBadRequest('Bad type of json_body type %s' % key)
			for key in post:
				if key not in args[1].POST:
					raise HTTPBadRequest('Lacking post parameter: %s' % key)
				if type(args[1].POST[key]) != post[key]:
					raise HTTPBadRequest('Bad type')

			return func(*args, **kwargs)

		return inner
	return validate_inner

"""
Only attempt to query db for instance if the uuid is valid
"""
def validateUuidAndQuery(instanceType, field, instanceUuid: str):
	try:
		uuid.UUID(hex=instanceUuid, version=4)
		return db.query(instanceType).filter(field == instanceUuid).first()
	except:
		return None

"""
Generates a cryptographically safe random string
"""
def randomCode(length: int):
	code = ""
	for i in range(0,length):
		code += string.ascii_letters[secrets.randbelow(len(string.ascii_letters))]

	return code
