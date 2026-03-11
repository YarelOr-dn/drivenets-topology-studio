load override
-------------

**Minimum user role:** operator

To replace the candidate configuration with the file content:

**Command syntax: load override {** user-specific **[file-name] \| factory-default }**

**Command mode:** configuration

**Note**

- You must perform commit after the load override operation for the candidate configuration to take effect.

.. - User should perform "commit" command after load override operation for the candidate configuration to be committed.

	- If user-specific is set, the configuration is loaded from the config directory of the current user. This directory can be accessed by this user only

	- Loaded file can be only config file.

	- NCC config located at:

	- config - /config/

	- user-specific config - /home/[user]/config/

	- rollback - /rollback

	- Configuration files are saved and loaded from the active NCC.

**Parameter table**

+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| Parameter       | Description                                                                                                                                                      | Range             | Default |
+=================+==================================================================================================================================================================+===================+=========+
| file-name       | The name of the file with which to replace the configuration. Only configuration files.                                                                          | 1..255 characters | \-      |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| factory-default | Replaces the candidate configuration with the default configuration.                                                                                             | \-                | \-      |
|                 | This option removes all configuration, including all users, passwords, and cluster NCPs. Removing the cluster NCPs will cause the network interfaces to go down. |                   |         |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| user-specific   | When specified, the configuration is loaded from the config directory of the current user. This directory is accessible to this user only.                       | \-                | \-      |
+-----------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+

Configuration files are saved and loaded from the active NCC at:

- config - /config/

- rollback - /rollback/

- user-specific config - /home/[user]/config/

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# load override MyConfig.txt
	configuration load complete

	dnRouter(cfg)# load override user-specific MyConfig.txt
	configuration load complete

	dnRouter# configure
	dnRouter(cfg)# load override factory-default
	configuration load complete


.. **Help line:** replace the candidate configuration with the file content

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 6.0     | Command introduced                               |
+---------+--------------------------------------------------+
| 11.0    | Added option to load from "user-specific" folder |
+---------+--------------------------------------------------+


