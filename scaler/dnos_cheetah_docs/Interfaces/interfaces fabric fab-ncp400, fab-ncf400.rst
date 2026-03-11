interfaces fabric fab-ncp400, fab-ncf400
----------------------------------------

**Minimum user role:** operator

The fabric interfaces are 400 Gbps interfaces interconnecting NCPs via the NCF. These interfaces are located on the NCPs and NCFs.

To configure the fabric interfaces:

**Command syntax: fab-<node-type>X-Y/Z/W**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the fabric interfaces on the NCP and NCF.

**Parameter table**

+---------------+------------------------------------------------+-----------------------------------+-------------+
|               |                                                |                                   |             |
| Parameter     | Description                                    | Range                             | Default     |
+===============+================================================+===================================+=============+
|               |                                                |                                   |             |
| Node-type     | The node where   the fabric port is located    | NCP                               | \-          |
|               |                                                |                                   |             |
|               |                                                | NCF                               |             |
+---------------+------------------------------------------------+-----------------------------------+-------------+
|               |                                                |                                   |             |
| W-X/Y/Z       | The fabric port identifier                     | X - interface speed               | \-          |
|               |                                                |                                   |             |
|               |                                                | Y - NCP/NCF id                    |             |
|               |                                                |                                   |             |
|               |                                                | Z - slot id, value 0              |             |
|               |                                                |                                   |             |
|               |                                                | W - port id as shown at the WB    |             |
+---------------+------------------------------------------------+-----------------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces 
	dnRouter(cfg-if)# fab-ncp400-0/0/0


**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-if)# no fab-ncp400-0/0/0


.. **Help line:** configures fabric interface

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+
