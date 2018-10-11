from __future__ import unicode_literals
import time
from netmiko.cisco_base_connection import CiscoSSHConnection

class AlliedTelesisAWPlusBase(CiscoSSHConnection):
    def sesion_prepation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r"[>#]")
        self.set_base_prompt()
        self.disable_paging()
        self.set_terminal_width(command="terminal width 511")
        # Clear the read buffer
        time.sleep(0.3 * self.global_delay_factor)
        self.clear_buffer()

    def disable_paging(self, command="", delay_factor=1):
        disable_command = "terminal length 0"
        output = self.send_command(disable_command)

    def set_terminal_width(self, command="", delay_factor=1):
         """No terminal width command mode on Allied Ware Plus"""
         pass

class AlliedTelesisAWPlusSSH(AlliedTelesisAWPlusBase):
    pass
