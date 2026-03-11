request system generate golden-config
-------------------------------------

**Minimum user role:** admin

Create a golden configuration file based on current system configuration.

**Command syntax: request system generate golden-config**

**Command mode:** operational

**Note**
	- The golden-config file allows the user to revert the system to the saved configuration.
	- Existing golden-config file will be overwritten by this command.

..
	**Internal Note**
	- Yes/no validation should be added
	- Command should fail with proper indication in CLI on all non NCP6 Ufispace Q2C+ (Emux) platforms

**Example**
::

	dnRouter# request system generate golden-config
	Warning: Existing golden-config file will be overwritten. Are you sure you want to proceed? (Yes/No) [No]?

	dnRouter# request system generate golden-config
	Command not supported on platform

.. **Help line:** Retry software/firmware installation on a failed node.

**Command History**

+-------------+-----------------------+
| Release     | Modification          |
+=============+=======================+
| 19.1        | Command introduced    |
+-------------+-----------------------+
