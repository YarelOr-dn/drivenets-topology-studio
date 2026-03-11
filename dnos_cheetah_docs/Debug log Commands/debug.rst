debug
-----

**Minimum user role:** operator

The debug commands are a set of tools that allow to perform detailed troubleshooting of the configuration and debug an element's behavior. Specifically, it allows to troubleshoot state-machine protocols running on DNOS, received and sent protocol messages, etc.

The debug commands enable protocol debug logging for specific events.

The following options are available for debug:

- Persistent: allows persistent troubleshooting configuration per system. The commands are run within configuration mode and preserve debug logging on system restart. Specifically this allow to debug a system event upon system start even before the user has access to the system.

	The following persistent debug tools are available:

	- debug <protocol>: enables the debugging of a specific category for a selected routing protocol

	- debug file: allows to modify debug file parameters, affecting the amount of information to be stored

Use the "show debugging <protocol>" command to display the categories that are enabled for debugging for the given protocol.

To enter debug configuration:

**Command syntax: debug**

**Command mode:** config

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)#

**Removing Configuration**

To revert the entire debug configuration to defaults:
::

	dnRouter(cfg-debug)# no debug

.. **Help line:** Enter debug configuration level

**Command History**

+-------------+------------------------------+
|             |                              |
| Release     | Modification                 |
+=============+==============================+
|             |                              |
| 10.0        | Command introduced           |
+-------------+------------------------------+
| 16.2        | Removed set-debug command    |
+-------------+------------------------------+
