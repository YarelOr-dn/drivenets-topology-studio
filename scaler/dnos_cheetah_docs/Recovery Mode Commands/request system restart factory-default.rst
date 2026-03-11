request system restart factory-default
--------------------------------------

**Minimum user role:** admin

By default, factory default does a new commit by applying the system default configuration.

Use the force option to wipe the configuration and operational database (management engine, forwarding engine, routing engine, and selector), including all rollback information. The system will return to first deployment state. restarts the system and clears the system database (management engine, forwarding engine, routing engine, and selector). All configuration including rollback information is deleted. Persistent files, e.g. log files, saved configuration files, etc. are not deleted.

**Command syntax: request system restart factory-default** force

**Command mode:** recovery

**Note**

- This operation removes all configuration, including users, passwords, and cluster NCPs. Removing the cluster NCPs causes the network interfaces to go down.

.. - Yes/no validation should exist for system restart factory-default operation.

	- Request system restart performs applicative containers restart across all the system.

	- Applicative containers are Management-engine, Routing-engine, Forwarding-engine and selector.

	- By default, Factory-default preform a new commit by applying the system default configuartion.

	- Factory-default force clears all database configuration. Including rollback information. Any persistent files (i.e log files, saved configuration files etc) remain not deleted.

**Example**
::

	dnRouter(RECOVERY)# request system restart factory-default
	Warning: Are you sure you want to perform restart factory-default? Operation will erase all system database (Yes/No) [No]?

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 9.0     | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 11.5    | Added option to wipe the configuration and operational database |
+---------+-----------------------------------------------------------------+


