load merge
----------

**Minimum user role:** operator

You can load a saved configuration file to replace the current running configuration. This command is useful for reverting to a previous configuration, transferring a configuration from one server to another, and for systematically adding or removing configurations.

To load a saved configuration, use the following command:

**Command syntax: load merge** user-specific **[file-name]**

**Command mode:** configuration

.. **Note**

	- The operation is load-merge - could be for a partial config

	- If user-specific is set, the configuration is loaded from the config directory of the current user. This directory can be accessed by this user only

	- NCC config located at:

	- config - /config/

	- user-specific config - /home/[user]/config/

	- rollback - /rollback

	- Configuration files are saved and loaded from the active NCC.

**Parameter table**

+---------------+--------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| Parameter     | Description                                                                                                                                | Range             | Default |
+===============+============================================================================================================================================+===================+=========+
| file-name     | The name of the saved file in the configuration folder. Enter the file name as it appears in the configuration folder.                     | 1..255 characters | \-      |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| user-specific | When specified, the configuration is loaded from the config directory of the current user. This directory is accessible to this user only. | \-                | \-      |
+---------------+--------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+

Configuration files are saved and loaded from the active NCC at:

- config - /config/

- rollback - /rollback/

- user-specific config - /home/[user]/config/

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# load merge MyConfig.txt

	dnRouter# configure
	dnRouter(cfg)# load merge user-specific MyConfig.txt



.. **Help line:** merge the file content with the candidate configuration

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 5.1.0   | Command introduced                               |
+---------+--------------------------------------------------+
| 6.0     | Changed to a configuration command               |
+---------+--------------------------------------------------+
| 11.0    | Added option to load from "user-specific" folder |
+---------+--------------------------------------------------+


