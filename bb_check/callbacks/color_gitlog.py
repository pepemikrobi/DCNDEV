# callback_plugins/color_gitlog.py
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import sys
import re

from ansible.plugins.callback import CallbackBase

DOCUMENTATION = r'''
callback: color_gitlog
type: aggregate
short_description: Print git log output with preserved ANSI colors
description:
  - Aggregate callback that prints git log stdout verbatim, so embedded
    ANSI color codes are honored by the terminal while preserving
    the normal Ansible stdout callback.
'''

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'color_gitlog'

    TARGET_TASK_NAMES = {
        'Run git log with color',
        'List DCNDEV folder contents',
        'Run git status in DCNDEV folder',
        'Header for this host (shell)'
    }
    ESCAPED_ANSI_PATTERN = re.compile(r'\\u001b|\\x1b|\\033')

    def _is_target_task(self, result):
        task_name = result._task.get_name()
        if task_name in self.TARGET_TASK_NAMES:
            return True

        cmd = result._result.get('cmd', '')
        return 'git log' in cmd

    def _display_output(self, host, header, output):
        if not output:
            return
        self._display.display(f"{host} | {header}")
        # shell output may contain escaped ANSI markers (e.g. "\\u001b").
        # Convert them to real escape bytes so terminal colors render.
        rendered = self.ESCAPED_ANSI_PATTERN.sub('\x1b', output)
        sys.stdout.write(rendered)
        if not output.endswith('\n'):
            sys.stdout.write('\n')
        sys.stdout.flush()

    def v2_runner_on_ok(self, result):
        if not self._is_target_task(result):
            return

        task_name = result._task.get_name()
        host = result._host.get_name()
        output = result._result.get('stdout', '')
        self._display_output(host, f'{task_name} output:', output)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if not self._is_target_task(result):
            return

        task_name = result._task.get_name()
        host = result._host.get_name()
        stderr = result._result.get('stderr', '')
        stdout = result._result.get('stdout', '')

        self._display_output(host, f'{task_name} failed (stderr):', stderr)
        self._display_output(host, f'{task_name} partial output (stdout):', stdout)
            