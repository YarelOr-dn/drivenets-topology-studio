system ncf
----------

**Minimum user role:** operator

To configure an NCF:

**Command syntax: ncf [ncf-id] model [model]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- Notice the change in prompt.

- While the NCP model is not required to identify a provisioned NCP, you nevertheless need to specify it as the same command is used to configure NCPs in a pre-provisioning scenario.

.. - no command deletes the ncf entity from the database.

	- For **standalone cluster**, NCF is not configured.

**Parameter table**

+-----------+-----------------------------------------------------------------+----------+---------+
| Parameter | Description                                                     | Range    | Default |
+===========+=================================================================+==========+=========+
| ncf-id    | The identifier of the NCF. The ID is unique within the cluster. | 0..12    | \-      |
+-----------+-----------------------------------------------------------------+----------+---------+
| model     | The NCF hardware model                                          | NCF-48CD | \-      |
+-----------+-----------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncf 7 model NCF-48CD
	dnRouter(cfg-system-ncf-7)# 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no ncf 7

.. **Help line:** configure an ncf for DNOS cluster

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+


