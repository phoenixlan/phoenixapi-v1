import logging
log = logging.getLogger(__name__)

from jinja2 import Environment, PackageLoader, select_autoescape


class MailProvider:
    def __init__(self) -> None:
        self.env = Environment(
            loader=PackageLoader("phoenixRest", "mailTemplates"),
            autoescape=select_autoescape()
        )
    def send_mail(self, to: str, subject: str, bodyFile: str, variables: dict):
        template = self.env.get_template(bodyFile)
        self._send_mail_impl(to, subject, template.render(variables))

    def _send_mail_impl(self, to: str, subject: str, body: str):
        log.info("Mail to %s(%s) not sent due to dummy implementation" % (to, subject))

