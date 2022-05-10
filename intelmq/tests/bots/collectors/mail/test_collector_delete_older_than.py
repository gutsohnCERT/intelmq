# SPDX-FileCopyrightText: 2022 gutsohnCERT
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# -*- coding: utf-8 -*-
"""
Test deleting Mails before specific date
"""
import unittest.mock as mock
import unittest
import os
import requests_mock
import intelmq.lib.test as test

from intelmq.bots.collectors.mail.collector_mail_url import MailURLCollectorBot
from intelmq.tests.bots.collectors.http.test_collector import prepare_mocker

if os.getenv('INTELMQ_TEST_EXOTIC'):
    from .lib import MockedTxtDeleteOlderThanImbox


REPORT_TXT_DELETE_OLDER_THAN = {'__type': 'Report',
                                'extra.email_from': 'gutsohn@cert.at',
                                'extra.email_message_id': '<ffds45304-f44g-23d7-dkjaz53jk4554kjfds8@cert.at>',
                                'extra.email_subject': 'foobar txt',
                                'extra.email_date': 'Tue, 3 Sep 2005 16:57:40 +0200',
                                'feed.accuracy': 100.0,
                                'feed.name': 'IMAP Feed',
                                'extra.file_name': 'foobar.txt',
                                'feed.url': 'http://localhost/foobar.txt',
                                'raw': 'YmFyIHRleHQK',
                                }


@test.skip_exotic()
class TestMailDeleteOlderThanCollectorBot(test.BotTestCase, unittest.TestCase):
    """
    Test deleting mails before specific date
    """
    @classmethod
    def set_bot(cls):
        cls.bot_reference = MailURLCollectorBot
        cls.sysconfig = {'mail_host': None,
                         'mail_user': None,
                         'mail_password': None,
                         'mail_ssl': None,
                         'folder': None,
                         'subject_regex': None,
                         'url_regex': r'http://localhost/.*\.txt',
                         'name': 'IMAP Feed',
                         }

    @requests_mock.Mocker()
    def test_fetch(self, mocker):
        prepare_mocker(mocker)
        with mock.patch('imbox.Imbox', new=MockedTxtDeleteOlderThanImbox):
            self.run_bot()
            self.assertMessageEqual(0, REPORT_TXT_DELETE_OLDER_THAN)
