system timing-mode 
-------------------

**Minimum user role:** operator

Set the timing mode to "NTP" to enable NTP functionality.

**Command syntax: timing-mode [mode]**

**Command mode:** config

**Hierarchies**

- system 

**Note**

- The system's timing mode must match that of DNOR. If you manually set the system's date-time value to 10 years higher or lower than date-time value on DNOR, DNOR cluster management may be lost. It will not be possible to add/remove NCC nodes from the cluster.

.. - no command returns timing-mode to default.

	- When system timing mode "NTP" is set, the system time source from remote server via NTP protocol is used. If no remote NTP server was configured as time source for the system, the system will operate in a free-running state using the time that was set during DNOS cluster creation.

	- When system timing mode "manual" is set, user may set the time & date to any value using "set system datetime" CLI command. If manually set date-time value is 10 years higher or 10 years lower than date-time value on DNOR, cluster management by DNOR may be lost. In this case, NCC add/remove from cluster functionality will not be available.

	- When system timing-mode "manual" is set, NTP functionalities are disabled.

**Parameter table**

+-----------+------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+
| Parameter | Description                  | Range                                                                                                                                                                                                                                  | Default |
+===========+==============================+========================================================================================================================================================================================================================================+=========+
| mode      | The timing mode of operation | NTP - enables the NTP functionality (see system ntp server). If no remote NTP server is configured as time source for the system, the system will operate in a free-running state using the time that was set during cluster creation. | NTP     |
|           |                              | manual - disables the NTP functionality and uses the manually set time (see set system datetime).                                                                                                                                      |         |
+-----------+------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# timing-mode ntp
	dnRouter(cfg-system)# timing-mode manual
	WARNING: System and Conductor must be in the same time domain. By setting system date and time manually, you may lose the ability to add and remove nodes to cluster!
	
	
	

**Removing Configuration**

To revert the timing-mode to default: 
::

	dnRouter(cfg-system)# no timing-mode

.. **Help line:** Configure system timing mode.

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 6.0     | Applied new hierarchy |
+---------+-----------------------+


