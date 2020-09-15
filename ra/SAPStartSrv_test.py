"""
Unitary tests for SAPStartSrv resource agent.

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2020-09-15
"""

# pylint:disable=C0103,C0111,W0212,W0611

import os
import sys
import imp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import unittest
import filecmp
import shutil

try:
    from unittest import mock
except ImportError:
    import mock

sys.modules['ocf'] = mock.Mock()
SAPStartSrv = imp.load_source(
    'SAPStartSrv',
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'SAPStartSrv.in')))


class TestSAPStartSrv(unittest.TestCase):
    """
    Unitary tests for SAPStartSrv.in
    """

    @classmethod
    def setUpClass(cls):
        """
        Global setUp.
        """

        logging.basicConfig(level=logging.INFO)

    def setUp(self):
        """
        Test setUp.
        """
        self._sid = 'PRD'
        self._instance_name = 'ASCS'
        self._instance_number = '00'
        self._virtualhost = 'virthost'
        self._agent = SAPStartSrv.SapStartSrv(
            '{}_{}{}_{}'.format(
                self._sid, self._instance_name, self._instance_number, self._virtualhost))

    def tearDown(self):
        """
        Test tearDown.
        """

    @classmethod
    def tearDownClass(cls):
        """
        Global tearDown.
        """

    @mock.patch('ocf.logger.info')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('SAPStartSrv.run_command')
    def test_start_success(self, mock_run_command, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.instance_name = 'ASCS00'
        self._agent.instance_number = '00'
        self._agent.saptstartsrv_path = '/mock/sapstartsrv'
        self._agent.sap_instance_profile = 'my_profile'
        self._agent.sid = 'PRD'
        self._agent.sidadm = 'prdadm'

        start_mock = mock.Mock(output='output', err='error')
        mock_run_command.side_effect = [None, None, start_mock]

        get_status_result_mock = mock.Mock(returncode=0)
        get_status_mock = mock.Mock(return_value=get_status_result_mock)
        self._agent._get_status = get_status_mock

        ocf_returncode = self._agent.start()
        assert ocf_returncode == 0

        mock_run_command.assert_has_calls([
            mock.call('rm -f /tmp/.sapstream50013'),
            mock.call('rm -f /tmp/.sapstream50014'),
            mock.call('/mock/sapstartsrv pf=my_profile -D -u prdadm')
        ])

        mock_logger.assert_called_once_with(
            'sapstartsrv for SAP Instance PRD-ASCS00 started: output')

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_NOT_RUNNING', 1)
    @mock.patch('SAPStartSrv.run_command')
    def test_start_error(self, mock_run_command, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.instance_name = 'ASCS00'
        self._agent.instance_number = '00'
        self._agent.saptstartsrv_path = '/mock/sapstartsrv'
        self._agent.sap_instance_profile = 'my_profile'
        self._agent.sid = 'PRD'
        self._agent.sidadm = 'prdadm'

        start_mock = mock.Mock(output='output', err='error')
        mock_run_command.side_effect = [None, None, start_mock]

        get_status_result_mock = mock.Mock(returncode=1)
        get_status_mock = mock.Mock(return_value=get_status_result_mock)
        self._agent._get_status = get_status_mock

        ocf_returncode = self._agent.start()
        assert ocf_returncode == 1

        mock_run_command.assert_has_calls([
            mock.call('rm -f /tmp/.sapstream50013'),
            mock.call('rm -f /tmp/.sapstream50014'),
            mock.call('/mock/sapstartsrv pf=my_profile -D -u prdadm')
        ])

        mock_logger.assert_called_once_with(
            'sapstartsrv for SAP Instance PRD-ASCS00 start failed: error')

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_start_validate(self):
        self._agent._inititialize = mock.Mock()
        self._agent.sid = 'PRD'
        self._agent.instance_number = '00'
        self._agent.instance_name = 'ASCS00'
        self._agent.virtual_host = 'virt'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 0

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_ERR_ARGS', 1)
    def test_start_validate_invalid_sid(self, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.sid = 'PRDD'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid system ID!' % self._agent.sid)

        mock_logger.reset_mock()
        self._agent.sid = 'PR'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid system ID!' % self._agent.sid)

        mock_logger.reset_mock()
        self._agent.sid = 'prd'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid system ID!' % self._agent.sid)

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_ERR_ARGS', 1)
    def test_start_validate_invalid_instance_name(self, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.sid = 'PRD'
        self._agent.instance_name = 'ASCS'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid instance name!' %
            self._agent.instance_name)

        mock_logger.reset_mock()
        self._agent.instance_name = 'ASCS0'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid instance name!' %
            self._agent.instance_name)

        mock_logger.reset_mock()
        self._agent.instance_name = 'ASCS000'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid instance name!' %
            self._agent.instance_name)

        mock_logger.reset_mock()
        self._agent.instance_name = '00AS'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid instance name!' %
            self._agent.instance_name)
