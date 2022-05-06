# Copyright (c) 2017-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import getpass
import logging
import platform
import smtplib

from email.mime.text import MIMEText

import keyring

from ..config import config_get_object
from .event_listener import EventListener

logger = logging.getLogger(__name__)


class EmailListener(EventListener):
    """
    EventListener subclass that can be used to send e-mail notification about
    various events.
    """

    def __init__(self, config, event, param_name, from_address, to_address, smtp_host, smtp_port, smtp_timeout=5):
        """
        :param config: ConfigParser object containing information about the fuzz session.
        :param event: The name of the event to send notification about.
        :param param_name: The name of the event's parameter containing the information to send.
        :param from_address: E-mail address to send notifications from.
        :param to_address: Target e-mail address to send the notification to.
        :param smtp_host: Host of the smtp server to send e-mails from.
        :param smtp_port: Port of the smtp server to send e-mails from.
        :param smtp_timeout: Timeout in seconds for blocking SMTP operations like the connection attempt.
        (Optional, default: 5)
        """
        super().__init__(config)
        self.param_name = param_name
        self.from_address = from_address
        self.to_address = to_address
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_timeout = smtp_timeout

        # Initialize connection to the smtp server.
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.smtp_timeout) as server:
            server.starttls()

            pwd = keyring.get_password('fuzzinator', self.from_address)
            while not pwd:
                pwd = getpass.getpass(prompt='Password of {mail}: '.format(mail=self.from_address))
                try:
                    server.login(self.from_address, pwd)
                except Exception as e:
                    logger.warning('Authentication failed.', exc_info=e)
                    pwd = None
            keyring.set_password('fuzzinator', self.from_address, pwd)
            self.pwd = pwd if platform.system() == 'Darwin' else None

        setattr(self, event, lambda *args, **kwargs: self.send_mail(kwargs[param_name]))

    def send_mail(self, data):
        """
        Send e-mail with the provided data.

        :param data: Information to fill subject and content fields with.
        """
        if not isinstance(data, dict):
            data = dict((self.param_name, data.decode('utf-8', 'ignore')))
        data = dict((name, raw.decode('utf-8', 'ignore') if isinstance(raw, bytes) else raw) for name, raw in data.items())

        from ..formatter import JsonFormatter
        formatter = config_get_object(self.config, 'sut.' + data['sut'], ['email_formatter', 'formatter']) or JsonFormatter()

        subject = formatter.summary(issue=data)
        content = formatter(issue=data)

        msg = MIMEText(content)
        msg['From'] = self.from_address
        msg['To'] = self.to_address
        msg['Subject'] = subject

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.smtp_timeout) as server:
                server.starttls()
                server.login(self.from_address, self.pwd or keyring.get_password('fuzzinator', self.from_address))
                server.send_message(msg)
        except Exception as e:
            logger.warning('E-mail sending failed.', exc_info=e)
