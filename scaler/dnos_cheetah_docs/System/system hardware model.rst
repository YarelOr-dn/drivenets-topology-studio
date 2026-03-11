system hardware model
---------------------

**Minimum user role:** operator

To enter the hardware model configuration hierarchy per DNOS cluster mode:

**Command syntax: system [node-name] [node-id] hardware model [hardware-model]**

**Command mode:** config

**Hierarchies**

- system

**Note**

- The no command removes the model configuration.

- There are no validations on hardware model type per node.

-  agcxd40s is DNI NCP 40C platform

**Parameter table**

+----------------+-----------------------------------+--------+---------+
| Parameter      | Description                       | Range  | Default |
+----------------+-----------------------------------+--------+---------+
| ncp-id         | The ID number of the specific ncp | 0..191 | \-      |
+----------------+-----------------------------------+--------+---------+
| hardware-model | The ODM hardware model            | 1..20  | \-      |
+----------------+-----------------------------------+--------+---------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncp 0
	dnRouter(cfg-system-ncp-0)# hardware model agcxd40s
	dnRouter(cfg-ncp-0-hardware-model)#

**Removing Configuration**

To remove the model configuration:
::

	dnRouter(cfg-system-ncp-0-hardware)#no model


.. **Help line:** configure hardware model for DNOS cluster nodes.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
