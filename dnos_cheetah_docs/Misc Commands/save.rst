save
----

**Minimum user role:** operator

You can save the running configuration of the main CLI to a file using the following command:

**Command syntax: save [file-name]**

**Command mode:** configuration

**Note**

- "factory-default" and "golden-config" are reserved names.

- NCC config located at: ``/config/``

The saved file has a predefined structure:

- config start

- version

- last commit user

**Parameter table**

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+
| Parameter | Description                                                                                                                                                                                                                       | Range             | Default |
+===========+===================================================================================================================================================================================================================================+===================+=========+
| file-name | The file will be saved in the configuration files folder. If the file name already exists, the save will overwrite it (a warning message will be displayed). The file is saved in text format. A suffix (.txt, .cfg) is optional. | 1..255 characters | \-      |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+---------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)#
	dnRouter(cfg)# save MySavedConfig.txt

	file content:
	# dnRouter config-start [04-Jun-2024 04:27:05 UTC]

	# VERSION DNOS [19.2.0.0], Copyright 2024 DRIVENETS LTD.
	# USER admin
	configuration..


.. **Help line:** save configuration to a file

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 5.1.0   | Command introduced                 |
+---------+------------------------------------+
| 6.0     | Changed to a configuration command |
+---------+------------------------------------+


