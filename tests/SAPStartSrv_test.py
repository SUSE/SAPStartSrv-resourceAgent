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
import unittest
import subprocess
import logging

try:
    import imp
    load_source = imp.load_source
except ImportError:
    # Python >= 3.12
    # https://docs.python.org/3/whatsnew/3.12.html#whatsnew312-removed-imp
    import importlib.util
    import importlib.machinery

    def load_source(modname, filename):
        loader = importlib.machinery.SourceFileLoader(modname, filename)
        spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
        module = importlib.util.module_from_spec(spec)
        # The module is always executed and not cached in sys.modules.
        # Uncomment the following line to cache the module.
        sys.modules[module.__name__] = module
        loader.exec_module(module)
        return module

try:
    from unittest import mock
except ImportError:
    import mock

sys.modules['ocf'] = mock.Mock()
SAPStartSrv = load_source(
    'SAPStartSrv',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../ra/SAPStartSrv.in')))


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
        self._systemd_unit_name = 'SAPPRD_00.service'
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

    def test_process_result(self):
        result = SAPStartSrv.ProcessResult('cmd', 0, b'output', b'error')
        assert result.cmd == 'cmd'
        assert result.returncode == 0
        assert result.output == 'output'
        assert result.err == 'error'

    @mock.patch('SAPStartSrv.ProcessResult')
    @mock.patch('subprocess.Popen')
    def test_run_command(self, mock_popen, mock_process_result):
        mock_process = mock.Mock(returncode=0)
        mock_process.communicate.return_value = ['output', 'error']
        mock_popen.return_value = mock_process

        mock_process_result.return_value = 'result'

        result = SAPStartSrv.run_command('cmd')
        assert result == 'result'

        mock_popen.assert_called_once_with(
            ['cmd'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        mock_process.communicate.assert_called_once_with()
        mock_process_result.assert_called_once_with('cmd', 0, 'output', 'error')

    @mock.patch('SAPStartSrv.run_command')
    def test_is_unit_active(self, mock_run_command):
        mock_result = mock.Mock(output='output', returncode=0)
        mock_run_command.return_value = mock_result
        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        result = self._agent._is_unit_active()
        assert result is True
        mock_run_command.assert_called_once_with(
            '/usr/bin/systemctl is-active SAPPRD_00.service')

    @mock.patch('SAPStartSrv.run_command')
    def test_is_unit_not_active(self, mock_run_command):
        mock_result = mock.Mock(output='output', returncode=1)
        mock_run_command.return_value = mock_result
        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        result = self._agent._is_unit_active()
        assert result is False
        mock_run_command.assert_called_once_with(
            '/usr/bin/systemctl is-active SAPPRD_00.service')

    @mock.patch('SAPStartSrv.run_command')
    def test_get_systemd_unit_success(self, mock_run_command):
        mock_result = mock.Mock(output='UNIT FILE    STATE  \nSAPPRD_00.service\n\n1 unit files listed.\n', returncode=0)
        mock_run_command.return_value = mock_result
        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        result = self._agent._get_systemd_unit()
        assert result is True
        mock_run_command.assert_called_once_with(
            '/usr/bin/systemctl list-unit-files SAPPRD_00.service')

    @mock.patch('SAPStartSrv.run_command')
    def test_get_systemd_unit_error(self, mock_run_command):
        mock_result = mock.Mock(output='output', returncode=1)
        mock_run_command.return_value = mock_result
        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        result = self._agent._get_systemd_unit()
        assert result is False
        mock_run_command.assert_called_once_with(
            '/usr/bin/systemctl list-unit-files SAPPRD_00.service')

    @mock.patch('ocf.have_binary')
    @mock.patch('os.path.exists')
    def test_chk_systemd_support_binary_success(
            self, mock_exists, mock_have_binary):

        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        mock_have_binary.return_value = True
        mock_exists.return_value = False

        get_systemd_unit_mock = mock.Mock(return_value=False)
        self._agent._get_systemd_unit = get_systemd_unit_mock

        result = self._agent._chk_systemd_support()
        assert result is False

        mock_have_binary.assert_called_once_with(
            '/usr/bin/systemctl'
        )

    @mock.patch('ocf.have_binary')
    def test_chk_systemd_support_binary_error(
            self, mock_have_binary):

        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        mock_have_binary.return_value = False

        result = self._agent._chk_systemd_support()
        assert result is False

        mock_have_binary.assert_called_once_with(
            '/usr/bin/systemctl'
        )

    @mock.patch('ocf.have_binary')
    @mock.patch('os.path.exists')
    def test_chk_systemd_support_binary_success_exists_success(
            self, mock_exists, mock_have_binary):

        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        mock_have_binary.return_value = True
        mock_exists.return_value = True

        result = self._agent._chk_systemd_support()
        assert result is True

        mock_have_binary.assert_called_once_with(
            '/usr/bin/systemctl'
        )
        mock_exists.assert_called_once_with(
            '/etc/systemd/system/SAPPRD_00.service'
        )

    @mock.patch('ocf.have_binary')
    @mock.patch('os.path.exists')
    def test_chk_systemd_support_binary_success_exists_error(
            self, mock_exists, mock_have_binary):

        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        mock_have_binary.return_value = True
        mock_exists.return_value = False

        get_systemd_unit_mock = mock.Mock(return_value=False)
        self._agent._get_systemd_unit = get_systemd_unit_mock

        result = self._agent._chk_systemd_support()
        assert result is False

        mock_have_binary.assert_called_once_with(
            '/usr/bin/systemctl'
        )
        mock_exists.assert_called_once_with(
            '/etc/systemd/system/SAPPRD_00.service'
        )

    @mock.patch('ocf.have_binary')
    @mock.patch('os.path.exists')
    def test_chk_systemd_support_binary_success_exists_error_get_unit(
            self, mock_exists, mock_have_binary):

        self._agent.systemd_unit_name = 'SAPPRD_00.service'

        mock_have_binary.return_value = True
        mock_exists.return_value = False

        get_systemd_unit_mock = mock.Mock(return_value=True)
        self._agent._get_systemd_unit = get_systemd_unit_mock

        result = self._agent._chk_systemd_support()
        assert result is True

        mock_have_binary.assert_called_once_with(
            '/usr/bin/systemctl'
        )
        mock_exists.assert_called_once_with(
            '/etc/systemd/system/SAPPRD_00.service'
        )

    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('ocf.have_binary')
    @mock.patch('ocf.get_parameter')
    def test_find_executables_dir_executable(self, mock_get_parameter, mock_have_binary):

        mock_get_parameter.return_value = '/mydir'
        mock_have_binary.side_effect = [True, True]

        ocf_returncode = self._agent._find_executables()
        assert ocf_returncode == 0

        assert self._agent.dir_executable == '/mydir'
        assert self._agent.saptstartsrv_path == '/mydir/sapstartsrv'
        assert self._agent.sapcontrol_path == '/mydir/sapcontrol'

        mock_have_binary.assert_has_calls([
            mock.call('/mydir/sapstartsrv'),
            mock.call('/mydir/sapcontrol')
        ])

    @mock.patch('ocf.OCF_ERR_ARGS', 1)
    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.have_binary')
    @mock.patch('ocf.get_parameter')
    def test_find_executables_dir_executable_error(
            self, mock_get_parameter, mock_have_binary, mock_logger):

        mock_get_parameter.return_value = '/mydir'
        mock_have_binary.side_effect = [False, True]

        ocf_returncode = self._agent._find_executables()
        assert ocf_returncode == 1

        mock_have_binary.assert_has_calls([
            mock.call('/mydir/sapstartsrv')
        ])

        mock_logger.assert_called_once_with(
            'Cannot find sapstartsrv and sapcontrol executable in /mydir')

        mock_have_binary.reset_mock()
        mock_logger.reset_mock()
        mock_have_binary.side_effect = [True, False]

        ocf_returncode = self._agent._find_executables()
        assert ocf_returncode == 1

        mock_have_binary.assert_has_calls([
            mock.call('/mydir/sapstartsrv'),
            mock.call('/mydir/sapcontrol')
        ])

        mock_logger.assert_called_once_with(
            'Cannot find sapstartsrv and sapcontrol executable in /mydir')

    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('ocf.have_binary')
    @mock.patch('ocf.get_parameter')
    def test_find_executables_exe(self, mock_get_parameter, mock_have_binary):

        mock_get_parameter.return_value = None
        mock_have_binary.side_effect = [True, True]

        self._agent.sid = 'PRD'
        self._agent.instance_name = 'ASCS00'
        ocf_returncode = self._agent._find_executables()
        assert ocf_returncode == 0

        assert self._agent.dir_executable == '/usr/sap/PRD/ASCS00/exe'
        assert self._agent.saptstartsrv_path == '/usr/sap/PRD/ASCS00/exe/sapstartsrv'
        assert self._agent.sapcontrol_path == '/usr/sap/PRD/ASCS00/exe/sapcontrol'

        mock_have_binary.assert_has_calls([
            mock.call('/usr/sap/PRD/ASCS00/exe/sapstartsrv'),
            mock.call('/usr/sap/PRD/ASCS00/exe/sapcontrol')
        ])

    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.have_binary')
    @mock.patch('ocf.get_parameter')
    def test_find_executables_run(self, mock_get_parameter, mock_have_binary, mock_logger):

        mock_get_parameter.return_value = None
        mock_have_binary.side_effect = [True, False, True, True]

        self._agent.sid = 'PRD'
        self._agent.instance_name = 'ASCS00'
        ocf_returncode = self._agent._find_executables()
        assert ocf_returncode == 0

        assert self._agent.dir_executable == '/usr/sap/PRD/ASCS00/exe/run'
        assert self._agent.saptstartsrv_path == '/usr/sap/PRD/ASCS00/exe/run/sapstartsrv'
        assert self._agent.sapcontrol_path == '/usr/sap/PRD/ASCS00/exe/run/sapcontrol'

        mock_have_binary.assert_has_calls([
            mock.call('/usr/sap/PRD/ASCS00/exe/sapstartsrv'),
            mock.call('/usr/sap/PRD/ASCS00/exe/sapcontrol'),
            mock.call('/usr/sap/PRD/ASCS00/exe/run/sapstartsrv'),
            mock.call('/usr/sap/PRD/ASCS00/exe/run/sapcontrol')
        ])

        mock_logger.assert_called_once_with(
            'Cannot find sapstartsrv and sapcontrol executable in /usr/sap/PRD/ASCS00/exe')

    @mock.patch('ocf.OCF_ERR_ARGS', 1)
    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.have_binary')
    @mock.patch('ocf.get_parameter')
    def test_find_executables_error(self, mock_get_parameter, mock_have_binary, mock_logger):

        mock_get_parameter.return_value = None
        mock_have_binary.side_effect = [False, True, False]

        self._agent.sid = 'PRD'
        self._agent.instance_name = 'ASCS00'
        ocf_returncode = self._agent._find_executables()
        assert ocf_returncode == 1

        mock_have_binary.assert_has_calls([
            mock.call('/usr/sap/PRD/ASCS00/exe/sapstartsrv'),
            mock.call('/usr/sap/PRD/ASCS00/exe/run/sapstartsrv'),
            mock.call('/usr/sap/PRD/ASCS00/exe/run/sapcontrol')
        ])

        mock_logger.assert_has_calls([
            mock.call(
                'Cannot find sapstartsrv and sapcontrol executable in /usr/sap/PRD/ASCS00/exe'),
            mock.call(
                'Cannot find sapstartsrv and sapcontrol executable in /usr/sap/PRD/ASCS00/exe/run')
        ])

    @mock.patch('ocf.get_parameter')
    def test_export_variables(self, mock_get_parameter):

        test_dict = {
            'OCF_RESKEY_START_WAITTIME': '1234',
            'OCF_RESKEY_MONITOR_SERVICES': 'services',
            'LD_LIBRARY_PATH': ''
        }

        self._agent.dir_executable = '/mydir'

        with mock.patch.dict(os.environ, test_dict):
            self._agent._export_variables()

            assert os.environ['OCF_RESKEY_START_WAITTIME'] == '1234'
            assert os.environ['OCF_RESKEY_MONITOR_SERVICES'] == 'services'
            assert os.environ['LD_LIBRARY_PATH'] == '/mydir'

        assert mock_get_parameter.call_count == 0

    @mock.patch('ocf.get_parameter')
    def test_export_variables_set(self, mock_get_parameter):

        test_dict = {
            'OCF_RESKEY_START_WAITTIME': '',
            'OCF_RESKEY_MONITOR_SERVICES': '',
            'LD_LIBRARY_PATH': '/folder1:/folder2:/folder3'
        }

        self._agent.dir_executable = '/mydir'
        mock_get_parameter.side_effect = ['1234', 'new-services']

        with mock.patch.dict(os.environ, test_dict):
            self._agent._export_variables()

            assert os.environ['OCF_RESKEY_START_WAITTIME'] == '1234'
            assert os.environ['OCF_RESKEY_MONITOR_SERVICES'] == 'new-services'
            assert os.environ['LD_LIBRARY_PATH'] == '/folder1:/folder2:/folder3:/mydir'

        mock_get_parameter.assert_has_calls([
            mock.call('START_WAITTIME', '3600'),
            mock.call('MONITOR_SERVICES', SAPStartSrv.MONITOR_SERVICES_DEFAULT)
        ])

    @mock.patch('ocf.get_parameter')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_initialize_success(self, mock_get_parameter):
        sid = 'PRD'
        instance_name = 'ASCS'
        instance_number = '00'
        virtualhost = 'virthost'
        self._agent = SAPStartSrv.SapStartSrv('{}_{}{}_{}'.format(
            sid, instance_name, instance_number, virtualhost))

        self._agent._find_executables = mock.Mock(return_value=0)
        self._agent._export_variables = mock.Mock()

        dir_profile = 'dir_profile'
        mock_param2 = 'myprofile'
        mock_get_parameter.side_effect = [dir_profile, mock_param2]

        ocf_returncode = self._agent._inititialize()
        assert ocf_returncode == 0

        assert self._agent.sid == sid
        assert self._agent.instance_name == '{}{}'.format(instance_name, instance_number)
        assert self._agent.instance_number == instance_number
        assert self._agent.virtual_host == virtualhost
        assert self._agent.sidadm == '{}adm'.format(sid.lower())
        assert self._agent.sap_instance_profile == 'myprofile'

        mock_get_parameter.assert_has_calls([
            mock.call('DIR_PROFILE', '/usr/sap/{}/SYS/profile'.format(sid)),
            mock.call('SAP_INSTANCE_PROFILE', '{}/{}_{}{}_{}'.format(
                dir_profile, sid, instance_name, instance_number, virtualhost))
        ])

        self._agent._find_executables.assert_called_once_with()
        self._agent._export_variables.assert_called_once_with()

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_initialize_error(self):
        sid = 'PRD'
        instance_name = 'ASCS'
        instance_number = '00'
        virtualhost = 'virthost'
        self._agent = SAPStartSrv.SapStartSrv('{}_{}{}_{}'.format(
            sid, instance_name, instance_number, virtualhost))

        self._agent._find_executables = mock.Mock(return_value=1)

        ocf_returncode = self._agent._inititialize()
        assert ocf_returncode == 1

        assert self._agent.sid == sid
        assert self._agent.instance_name == '{}{}'.format(instance_name, instance_number)
        assert self._agent.instance_number == instance_number
        assert self._agent.virtual_host == virtualhost
        assert self._agent.sidadm == '{}adm'.format(sid.lower())

        self._agent._find_executables.assert_called_once_with()

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_ERR_ARGS', 1)
    def test_initialize_validation_error(self, mock_logger):
        self._agent = SAPStartSrv.SapStartSrv('ASCS')

        ocf_returncode = self._agent._inititialize()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'InstanceName parsing error. It must follow SID_NAME00_VIRTHOST syntax')

        mock_logger.reset_mock()
        self._agent = SAPStartSrv.SapStartSrv('PRD_ASCS')

        ocf_returncode = self._agent._inititialize()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'InstanceName parsing error. It must follow SID_NAME00_VIRTHOST syntax')

        mock_logger.reset_mock()
        self._agent = SAPStartSrv.SapStartSrv('PRD_ASCS00')

        ocf_returncode = self._agent._inititialize()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'InstanceName parsing error. It must follow SID_NAME00_VIRTHOST syntax')

        mock_logger.reset_mock()
        self._agent = SAPStartSrv.SapStartSrv('PRD_ASCS_virthost')

        ocf_returncode = self._agent._inititialize()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'InstanceName parsing error. It must follow SID_NAME00_VIRTHOST syntax')

        mock_logger.reset_mock()
        self._agent = SAPStartSrv.SapStartSrv('PRD_ASCS_')

        ocf_returncode = self._agent._inititialize()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'InstanceName parsing error. It must follow SID_NAME00_VIRTHOST syntax')

    @mock.patch('ocf.logger.info')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('SAPStartSrv.run_command')
    def test_start_sys5_style_success(self, mock_run_command, mock_logger):
        self._agent.instance_name = 'ASCS00'
        self._agent.instance_number = '00'
        self._agent.saptstartsrv_path = '/mock/sapstartsrv'
        self._agent.sap_instance_profile = 'my_profile'
        self._agent.sid = 'PRD'
        self._agent.sidadm = 'prdadm'

        start_mock = mock.Mock(output='output', err='error')
        mock_run_command.side_effect = [None, None, start_mock]

        get_status_mock = mock.Mock(return_value=0)
        self._agent._get_status = get_status_mock

        ocf_returncode = self._agent._start_sys5_style()
        assert ocf_returncode == 0

        mock_run_command.assert_has_calls([
            mock.call('rm -f /tmp/.sapstream50013'),
            mock.call('rm -f /tmp/.sapstream50014'),
            mock.call('/mock/sapstartsrv pf=my_profile -D -u prdadm')
        ])

        mock_logger.assert_called_once_with(
            'sapstartsrv for SAP Instance PRD_ASCS00 started: output')

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_NOT_RUNNING', 1)
    @mock.patch('SAPStartSrv.run_command')
    def test_start_sys5_style_error(self, mock_run_command, mock_logger):
        self._agent.instance_name = 'ASCS00'
        self._agent.instance_number = '00'
        self._agent.saptstartsrv_path = '/mock/sapstartsrv'
        self._agent.sap_instance_profile = 'my_profile'
        self._agent.sid = 'PRD'
        self._agent.sidadm = 'prdadm'

        start_sys5_style_mock = mock.Mock(output='output', err='error')
        mock_run_command.side_effect = [None, None, start_sys5_style_mock]

        get_status_mock = mock.Mock(return_value=1)
        self._agent._get_status = get_status_mock

        ocf_returncode = self._agent._start_sys5_style()
        assert ocf_returncode == 1

        mock_run_command.assert_has_calls([
            mock.call('rm -f /tmp/.sapstream50013'),
            mock.call('rm -f /tmp/.sapstream50014'),
            mock.call('/mock/sapstartsrv pf=my_profile -D -u prdadm')
        ])

        mock_logger.assert_called_once_with(
            'sapstartsrv for SAP Instance PRD_ASCS00 start failed: error')

    @mock.patch('ocf.logger.info')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_start_systemd_style_success_running(self, mock_logger):
        self._agent.systemd_unit_name = 'SAPPRD_00.service'
        is_unit_active_mock = mock.Mock(return_value=True)
        self._agent._is_unit_active = is_unit_active_mock

        result = self._agent._start_systemd_style()
        assert result == 0

        mock_logger.assert_called_once_with(
            'systemd service SAPPRD_00.service is active')

    @mock.patch('ocf.logger.warn')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('SAPStartSrv.run_command')
    def test_start_systemd_style_success_not_running(self, mock_run_command, mock_logger):
        self._agent.systemd_unit_name = 'SAPPRD_00.service'
        is_unit_active_mock = mock.Mock(return_value=False)
        self._agent._is_unit_active = is_unit_active_mock

        start_mock = mock.Mock(output='output', err='error', returncode=0)
        mock_run_command.return_value = start_mock

        result = self._agent._start_systemd_style()
        assert result == 0

        mock_run_command.assert_called_once_with(
            '/usr/bin/systemctl start SAPPRD_00.service')

        mock_logger.assert_called_once_with(
            'systemd service SAPPRD_00.service is not active, it will be started using systemd')

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('ocf.OCF_NOT_RUNNING', 7)
    @mock.patch('ocf.is_probe')
    @mock.patch('SAPStartSrv.run_command')
    def test_start_systemd_style_error_probe(self, mock_run_command, mock_is_probe, mock_logger):
        self._agent.systemd_unit_name = 'SAPPRD_00.service'
        is_unit_active_mock = mock.Mock(return_value=False)
        self._agent._is_unit_active = is_unit_active_mock

        start_mock = mock.Mock(output='output', err='error', returncode=1)
        mock_run_command.return_value = start_mock
        mock_is_probe.return_value = True

        result = self._agent._start_systemd_style()
        assert result == 7

        mock_run_command.assert_called_once_with(
            '/usr/bin/systemctl start SAPPRD_00.service')

        mock_logger.assert_called_once_with(
            'error during start of systemd unit SAPPRD_00.service!')

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('ocf.OCF_ERR_GENERIC', 1)
    @mock.patch('ocf.is_probe')
    @mock.patch('SAPStartSrv.run_command')
    def test_start_systemd_style_error_not_probe(
        self, mock_run_command, mock_is_probe, mock_logger):
        self._agent.systemd_unit_name = 'SAPPRD_00.service'
        is_unit_active_mock = mock.Mock(return_value=False)
        self._agent._is_unit_active = is_unit_active_mock

        start_mock = mock.Mock(output='output', err='error', returncode=1)
        mock_run_command.return_value = start_mock
        mock_is_probe.return_value = False

        result = self._agent._start_systemd_style()
        assert result == 1

        mock_run_command.assert_called_once_with(
            '/usr/bin/systemctl start SAPPRD_00.service')

        mock_logger.assert_called_once_with(
            'error during start of systemd unit SAPPRD_00.service!')

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_start_systemd_style_success(self):
        self._agent._inititialize = mock.Mock()

        chk_systemd_support_mock = mock.Mock(return_value=True)
        self._agent._chk_systemd_support = chk_systemd_support_mock
        start_systemd_style_mock = mock.Mock(return_value=0)
        self._agent._start_systemd_style = start_systemd_style_mock

        result = self._agent.start()
        assert result == 0

        self._agent._inititialize.assert_called_once_with()

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_start_success_sys5_style(self):
        self._agent._inititialize = mock.Mock()

        chk_systemd_support_mock = mock.Mock(return_value=False)
        self._agent._chk_systemd_support = chk_systemd_support_mock
        start_sys5_style_mock = mock.Mock(return_value=0)
        self._agent._start_sys5_style = start_sys5_style_mock

        result = self._agent.start()
        assert result == 0

        self._agent._inititialize.assert_called_once_with()

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_start_error_sys5_style(self):
        self._agent._inititialize = mock.Mock()

        chk_systemd_support_mock = mock.Mock(return_value=False)
        self._agent._chk_systemd_support = chk_systemd_support_mock
        start_sys5_style_mock = mock.Mock(return_value=1)
        self._agent._start_sys5_style = start_sys5_style_mock

        result = self._agent.start()
        assert result == 1

        self._agent._inititialize.assert_called_once_with()

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_start_success_systemd_style(self):
        self._agent._inititialize = mock.Mock()

        chk_systemd_support_mock = mock.Mock(return_value=True)
        self._agent._chk_systemd_support = chk_systemd_support_mock
        start_systemd_style_mock = mock.Mock(return_value=0)
        self._agent._start_systemd_style = start_systemd_style_mock

        result = self._agent.start()
        assert result == 0

        self._agent._inititialize.assert_called_once_with()

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_start_error_systemd_style(self):
        self._agent._inititialize = mock.Mock()

        chk_systemd_support_mock = mock.Mock(return_value=True)
        self._agent._chk_systemd_support = chk_systemd_support_mock
        start_systemd_style_mock = mock.Mock(return_value=1)
        self._agent._start_systemd_style = start_systemd_style_mock

        result = self._agent.start()
        assert result == 1

        self._agent._inititialize.assert_called_once_with()

    @mock.patch('ocf.logger.info')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('SAPStartSrv.run_command')
    def test_stop_success(self, mock_run_command, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.instance_name = 'ASCS00'
        self._agent.instance_number = '00'
        self._agent.sapcontrol_path = '/mock/sapcontrol'
        self._agent.sid = 'PRD'

        mock_command = mock.Mock(output='output', err='error', returncode=0)
        mock_run_command.return_value = mock_command

        self._agent._get_status = mock.Mock(return_value=0)

        ocf_returncode = self._agent.stop()
        assert ocf_returncode == 0

        self._agent._inititialize.assert_called_once_with()
        self._agent._get_status.assert_called_once_with()

        mock_run_command.assert_called_once_with('/mock/sapcontrol -nr 00 -function StopService')

        mock_logger.assert_called_once_with(
            'Stopping sapstartsrv of SAP Instance PRD_ASCS00: output')

    @mock.patch('ocf.logger.info')
    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('SAPStartSrv.run_command')
    def test_stop_already_stopped(self, mock_run_command, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.instance_name = 'ASCS00'
        self._agent.sid = 'PRD'

        self._agent._get_status = mock.Mock(return_value=1)

        ocf_returncode = self._agent.stop()
        assert ocf_returncode == 0

        self._agent._inititialize.assert_called_once_with()
        self._agent._get_status.assert_called_once_with()

        assert mock_run_command.call_count == 0

        mock_logger.assert_called_once_with(
            'SAP Instance PRD_ASCS00 already stopped')

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_ERR_GENERIC', 1)
    @mock.patch('SAPStartSrv.run_command')
    def test_stop_error(self, mock_run_command, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.instance_name = 'ASCS00'
        self._agent.instance_number = '00'
        self._agent.sapcontrol_path = '/mock/sapcontrol'
        self._agent.sid = 'PRD'

        mock_command = mock.Mock(output='output', err='error', returncode=1)
        mock_run_command.return_value = mock_command

        self._agent._get_status = mock.Mock(return_value=0)

        ocf_returncode = self._agent.stop()
        assert ocf_returncode == 1

        self._agent._inititialize.assert_called_once_with()
        self._agent._get_status.assert_called_once_with()

        mock_run_command.assert_called_once_with('/mock/sapcontrol -nr 00 -function StopService')

        mock_logger.assert_called_once_with(
            'SAP Instance PRD_ASCS00 stop failed: error')

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_status_success(self):
        self._agent._inititialize = mock.Mock()
        get_status_mock = mock.Mock(return_value=0)
        self._agent._get_status = get_status_mock

        ocf_returncode = self._agent.status()
        assert ocf_returncode == 0

        self._agent._inititialize.assert_called_once_with()
        self._agent._get_status.assert_called_once_with()

    @mock.patch('ocf.OCF_NOT_RUNNING', 1)
    def test_status_error(self):
        self._agent._inititialize = mock.Mock()
        self._agent._get_status = mock.Mock(return_value=mock.Mock(returncode=1))

        ocf_returncode = self._agent.status()
        assert ocf_returncode == 1

        self._agent._inititialize.assert_called_once_with()
        self._agent._get_status.assert_called_once_with()

    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('ocf.is_probe')
    def test_monitor_success(self, mock_is_probe):
        self._agent._inititialize = mock.Mock()
        get_status_mock = mock.Mock(return_value=0)
        self._agent._get_status = get_status_mock
        mock_is_probe.return_value = True

        ocf_returncode = self._agent.monitor()
        assert ocf_returncode == 0

        self._agent._inititialize.assert_called_once_with()
        self._agent._get_status.assert_called_once_with()

    @mock.patch('ocf.OCF_SUCCESS', 0)
    @mock.patch('ocf.is_probe')
    def test_monitor_error(self, mock_is_probe):
        self._agent._inititialize = mock.Mock()
        self._agent._get_status = mock.Mock()
        mock_is_probe.return_value = False

        ocf_returncode = self._agent.monitor()
        assert ocf_returncode == 0

        self._agent._inititialize.assert_called_once_with()
        assert self._agent._get_status.call_count == 0

    @mock.patch('ocf.OCF_SUCCESS', 0)
    def test_validate(self):
        self._agent._inititialize = mock.Mock()
        self._agent.sid = 'PRD'
        self._agent.instance_number = '00'
        self._agent.instance_name = 'ASCS00'
        self._agent.virtual_host = 'virt'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 0

        self._agent._inititialize.assert_called_once_with()

        self._agent.sid = 'H1A'
        self._agent.instance_number = '99'
        self._agent.instance_name = 'ERS99'
        self._agent.virtual_host = 'virt_host'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 0

        self._agent.sid = 'HA1'
        self._agent.instance_number = '55'
        self._agent.instance_name = 'PAS55'
        self._agent.virtual_host = 'v'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 0

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_ERR_ARGS', 1)
    def test_validate_invalid_sid(self, mock_logger):
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
    def test_validate_invalid_instance_name(self, mock_logger):
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

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_ERR_ARGS', 1)
    def test_validate_invalid_instance_number(self, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.sid = 'PRD'
        self._agent.instance_name = 'ASCS00'
        self._agent.instance_number = '0'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid instance number!' %
            self._agent.instance_number)

        mock_logger.reset_mock()
        self._agent.instance_number = '000'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid instance number!' %
            self._agent.instance_number)

        mock_logger.reset_mock()
        self._agent.instance_number = '0A'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid instance number!' %
            self._agent.instance_number)

        mock_logger.reset_mock()
        self._agent.instance_number = 'a0'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid instance number!' %
            self._agent.instance_number)

    @mock.patch('ocf.logger.error')
    @mock.patch('ocf.OCF_ERR_ARGS', 1)
    def test_validate_invalid_virthost(self, mock_logger):
        self._agent._inititialize = mock.Mock()
        self._agent.sid = 'PRD'
        self._agent.instance_name = 'ASCS00'
        self._agent.instance_number = '00'
        self._agent.virtual_host = '0virtual'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid virtual host name!' %
            self._agent.virtual_host)

        mock_logger.reset_mock()
        self._agent.virtual_host = 'A.'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid virtual host name!' %
            self._agent.virtual_host)

        mock_logger.reset_mock()
        self._agent.virtual_host = 'virtu*'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid virtual host name!' %
            self._agent.virtual_host)

        mock_logger.reset_mock()
        self._agent.virtual_host = 'virutal+'

        ocf_returncode = self._agent.validate()
        assert ocf_returncode == 1

        mock_logger.assert_called_once_with(
            'Parsing instance profile name: %s is not a valid virtual host name!' %
            self._agent.virtual_host)

    @mock.patch('SAPStartSrv.SapStartSrv')
    @mock.patch('ocf.Agent')
    @mock.patch('ocf.get_parameter')
    def test_main(self, mock_get_parameter, mock_ocf_agent, mock_sapstartsrv):

        agent = mock.Mock()
        mock_ocf_agent.return_value = agent

        mock_sapstartrv_intance = mock.Mock()
        mock_sapstartsrv.return_value = mock_sapstartrv_intance
        mock_get_parameter.side_effect = ['PRD_ASCS00_virthost', None]

        SAPStartSrv.main()

        mock_ocf_agent.assert_called_once_with(
            'SAPStartSrv', SAPStartSrv.SHORT_DESC, SAPStartSrv.LONG_DESC)

        agent.add_parameter.assert_has_calls([
            mock.call(
                name='InstanceName',
                shortdesc='Instance name: SID_INSTANCE_VIR-HOSTNAME',
                longdesc='The full qualified SAP instance name. e.g. HA1_ASCS00_sapha1as. '\
                    'Usually this is the name of the SAP instance profile.',
                content_type='string',
                required=True,
                unique=True,
                default=''),
            mock.call(
                name='START_PROFILE',
                shortdesc='Start profile name',
                longdesc='The name of the SAP Instance profile. Specify this parameter, if you '\
                    'have changed the name of the SAP Instance profile after the default SAP '\
                    'installation.',
                content_type='string',
                unique=True,
                default=''),
        ])
        mock_get_parameter.assert_has_calls([
            mock.call('InstanceName'),
            mock.call('START_PROFILE')
        ])
        mock_sapstartsrv.assert_called_once_with('PRD_ASCS00_virthost')

        agent.add_action.assert_has_calls([
            mock.call(name='start', timeout=60, handler=mock_sapstartrv_intance.start),
            mock.call(name='stop', timeout=60, handler=mock_sapstartrv_intance.stop),
            mock.call(name='status', timeout=60, handler=mock_sapstartrv_intance.status),
            mock.call(
                name='monitor', timeout=20, interval=120, handler=mock_sapstartrv_intance.monitor),
            mock.call(name='validate-all', timeout=5, handler=mock_sapstartrv_intance.validate),
        ])

        agent.run.assert_called_once_with()
