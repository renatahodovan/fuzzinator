# Copyright (c) 2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import getpass
import keyring
import yagmail

from .listener import EventListener


class EmailListener(EventListener):
    """
    EventListener subclass that can be used to send e-mail notification about
    various events.
    """

    def __init__(self, event, param_name, from_address, to_address, subject, content):
        """
        :param event: The name of the event to send notification about.
        :param param_name: The name of the event's parameter containing the information to send.
        :param from_address: Gmail user name that is saved in the keychain.
        :param to_address: Target e-mail address to send the notification to.
        :param subject: Subject of the e-mail (it may contain placeholders, that will be filled by parameter information).
        :param content: Content of the e-mail (it may contain placeholders, that will be filled by parameter information).
        """
        self.param_name = param_name
        self.from_address = from_address
        self.to_address = to_address
        self.subject = subject
        self.content = content
        if not keyring.get_password('yagmail', self.from_address):
            yagmail.register(self.from_address, getpass.getpass(prompt='Password of {mail}: '.format(mail=self.from_address)))
        setattr(self, event, lambda *args, **kwargs: self.send_mail(kwargs[param_name]))

    def send_mail(self, data):
        """
        Send e-mail with the provided data.

        :param data: Information to fill subject and content fields with.
        """
        if type(data) != dict:
            data = dict((self.param_name, data.decode('utf-8', 'ignore')))
        data = dict((name, raw.decode('utf-8', 'ignore') if type(raw) == bytes else raw) for name, raw in data.items())

        subject = self.subject.format(**data)
        content = self.content.format(**data)

        s = yagmail.SMTP(self.from_address)
        s.send(self.to_address,
               subject=subject,
               contents=content)
