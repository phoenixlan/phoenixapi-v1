import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'pyramid',
    'pyramid_chameleon',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'pyramid_jinja2',
    'pyramid-jwt',
    'sqlalchemy',
    'gunicorn',
    'zope.sqlalchemy',
    'alembic',
    'sqlalchemy_utils',
    'passlib',
    'argon2_cffi',
    'webtest',
    'pycodestyle',
    'pytest',
    'pytest-cov',
    'qrcode',
    'requests',
    'uuid',
    'sentry-sdk',
    'Pillow',
    'stripe',
    'mistune'
]

setup(name='phoenixRest',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = phoenixRest:main
      """,
)