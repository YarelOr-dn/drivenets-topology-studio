load override golden-config
---------------------------

**Minimum user role:** admin

To replace the current configuration with the golden-config content:

**Command syntax: load override golden-config**

**Command mode:** configuration

**Note**

- Command requires a valid golden-config file saved to the system.

.. - After issuing the command the system will replace all configurations with the golden-config settings and will reboot.

	**Internal Note**
	- Yes/no validation should be added
	- Command should fail with proper indication in CLI on all non NCP6 Ufispace Q2C+ (Emux) platforms

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# load override golden-config
	Warning: Are you sure you want to remove existing configuration and reboot with golden-config settings? (Yes/No) [No]
	Commit succeeded by ADMIN at 27-Jan-2024 12:21:00 UTC


	dnRouter# configure
	dnRouter(cfg)# load override golden-config
	Command not supported on platform

.. **Help line:** replace current configuration with golden-config file content and reboot the system

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 19.1    | Command introduced                               |
+---------+--------------------------------------------------+
