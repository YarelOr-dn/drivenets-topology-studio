system ncm
----------

**Minimum user role:** operator

NCMs interconnect clusters' NCPs.

To enter the configuration mode of an NCM:

**Command syntax: ncm [ncm-id]**

**Command mode:** config

**Hierarchies**

- system


**Note**

- NCM is not applicable to a standalone NCP.

- Notice the change in prompt.

.. - no command returns the ncm entity to its default.

	- For **standalone cluster**, ncm is not configured.

	- NCM configuration according to cluster type, i.e A0, B0 only valid for small cluster

**Parameter table**

+-----------+----------------------------------------------------------------------------------------------------------------------------------------+----------------+---------+
| Parameter | Description                                                                                                                            | Range          | Default |
+===========+========================================================================================================================================+================+=========+
| ncm-id    | The identifier of the NCM. The ID is unique within the cluster. Up to 4 NCMs can be configured per cluster, depending on cluster size. | A0, B0, A1, B1 | \-      |
+-----------+----------------------------------------------------------------------------------------------------------------------------------------+----------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncm A0 
	dnRouter(cfg-system-ncm-A0)# 
	
	
	

**Removing Configuration**

To revert the router-id to default: 
::

	dnRouter(cfg-system)# no ncm A0

.. **Help line:** configure an ncc for DNOS cluster

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.5    | Command introduced |
+---------+--------------------+


