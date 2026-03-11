system ncp model
----------------

**Minimum user role:** operator

To configure the model of the NCP:

**Command syntax: ncp [ncp-id] model [model]**

**Command mode:** config

**Hierarchies**

- system ncp


**Note**

- You cannot remove the configuration of NCP 0.

.. - "model" is a mandatory parameter for NCPs.

	- For **standalone cluster**, NCP 0 is configured by system. You cannot remove ncp-0 configuration.

**Parameter table**

+-----------+--------------------------+--------------+---------+
| Parameter | Description              | Range        | Default |
+===========+==========================+==============+=========+
| model     | The DriveNets NCP model. | NCP-40C      | \-      |
|           |                          | NCP-10CD     |         |
|           |                          | NCP-36CD-S   |         |
|           |                          | NCP-64X12C-S |         |
+-----------+--------------------------+--------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncp 7 
	dnRouter(cfg-system-ncp-7)# model NCP-40C
	

**Removing Configuration**

To revert the NCP configuration to default: 
::

	dnRouter(cfg-system)# no ncp 7

.. **Help line:** configure NCP model

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 11.0    | Command introduced                 |
+---------+------------------------------------+
| 16.1    | Added support for NCP-36CD-S model |
+---------+------------------------------------+
