# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import io
import json
import logging

import intelmq.lib.pipeline as pipeline
import intelmq.lib.utils as utils


class BotTestCase(object):
    """
    Provides common tests and assert methods for bot testing.
    """

    def setUp(self):
        """ Set default values. """
        self.maxDiff = None  # For unittest module, prints long diffs
        self.bot_id = None
        self.bot = None
        self.bot_reference = None
        self.config = {}
        self.input_message = ''
        self.loglines = []
        self.loglines_buffer = ''
        self.log_stream = None
        self.pipe = None

    def reset_bot(self):
        """Reconfigures the bot with the changed attributes"""

        self.log_stream = io.StringIO()

        src_name = "{}-input".format(self.bot_id)
        dst_name = "{}-output".format(self.bot_id)

        self.config["system"] = {"logging_level": "DEBUG",
                                 "http_proxy":  None,
                                 "https_proxy": None}

        self.config["runtime"] = {self.bot_id: {},
                                  "__default__": {"rate_limit": 0,
                                                  "retry_delay": 0,
                                                  "error_retry_delay": 0,
                                                  "error_max_retries": 0,
                                                  }}
        self.config["pipeline"] = {self.bot_id: {"source-queue": (src_name),
                                                 "destination-queues": [dst_name]}}

        logger = logging.getLogger(self.bot_id)
        logger.setLevel("DEBUG")
        console_formatter = logging.Formatter(utils.LOG_FORMAT)
        console_handler = logging.StreamHandler(self.log_stream)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        self.config["logger"] = logger

        class Parameters(object):
            source_queue = src_name
            destination_queues = [dst_name]
        parameters = Parameters()
        pipe = pipeline.Pythonlist(parameters)
        pipe.set_queues(parameters.source_queue, "source")
        pipe.set_queues(parameters.destination_queues, "destination")
        self.config["source_pipeline"] = pipe
        self.config["destination_pipeline"] = pipe

        self.bot = self.bot_reference(self.bot_id, config=self.config)
        self.pipe = self.config["source_pipeline"]
        self.input_queue = [self.input_message]

    def run_bot(self):
        """Call this method for actually doing a test
           run for the specified bot"""

        self.bot.start(error_on_pipeline=False,
                       source_pipeline=self.pipe,
                       destination_pipeline=self.pipe)
        self.loglines_buffer = self.log_stream.getvalue()
        self.loglines = self.loglines_buffer.splitlines()

    def get_input_queue(self):
        """Returns the input queue of this bot which can be filled
           with fixture data in setUp()"""

        return self.pipe.state["%s-input" % self.bot_id]

    def set_input_queue(self, seq):
        """Setter for the input queue of this bot"""
        self.pipe.state["%s-input" % self.bot_id] = seq

    input_queue = property(get_input_queue, set_input_queue)

    def get_output_queue(self):
        """Getter for the input queue of this bot. Use in TestCase scenarios"""
        return self.pipe.state["%s-output" % self.bot_id]

    def test_bot_start(self):
        """Tests if we can start a bot and feed data into
            it and have a reasonable output"""
        self.reset_bot()
        self.run_bot()

    def test_log_starting(self):
        """ Test if bot logs starting message. """
        self.reset_bot()
        self.run_bot()
        self.assertLoglineEqual(0, "Bot is starting", "INFO")

    def test_log_not_error(self):
        """ Test if bot does not log errors. """
        self.reset_bot()
        self.run_bot()
        self.assertNotRegexpMatches(self.loglines_buffer, "ERROR")

    def test_log_not_critical(self):
        """ Test if bot does not log critical errors. """
        self.reset_bot()
        self.run_bot()
        self.assertNotRegexpMatches(self.loglines_buffer, "CRITICAL")

    def test_pipe_names(self):
        """ Test if all pipes are created with correct names. """
        self.reset_bot()
        self.run_bot()
        pipenames = ["{}-input", "{}-input-internal", "{}-output"]
        self.assertListEqual([x.format(self.bot_id) for x in pipenames],
                             self.pipe.state.keys())

    def assertLoglineEqual(self, line_no, message, levelname="ERROR"):
        """Asserts if a logline matches a specific requirement.
           Args:
                line_no: Number of the logline which is asserted
                message: Message text which is compared
                type: Type of logline which is asserted"""

        self.assertIsNotNone(self.loglines)
        logline = self.loglines[line_no]
        fields = utils.parse_logline(logline)

        self.assertEqual(self.bot_id, fields["name"],
                         "bot_id %s didn't match %s"
                         "".format(self.bot_id, fields["name"]))

        self.assertEqual(levelname, fields["levelname"])
        self.assertEqual(message, fields["message"])

    def assertRegexpMatchesLog(self, pattern):
        """Asserts that pattern matches against log. """

        self.assertIsNotNone(self.loglines_buffer)
        self.assertRegexpMatches(self.loglines_buffer, pattern)

    def assertNotRegexpMatchesLog(self, pattern):
        """Asserts that pattern doesn't match against log"""

        self.assertIsNotNone(self.loglines_buffer)
        self.assertNotRegexpMatches(self.loglines_buffer, pattern)

    def assertEventAlmostEqual(self, queue_pos, expected_event):
        """Asserts that the given expected_event is
           contained in the generated event with
           given queue position"""

        event = self.get_output_queue()[queue_pos]
        unicode_event = {}

        for key, value in expected_event.items():
            unicode_event[unicode(key)] = unicode(value)

        self.assertIsInstance(event, unicode)
        event_dict = json.loads(event)

        self.assertDictContainsSubset(unicode_event, event_dict)
