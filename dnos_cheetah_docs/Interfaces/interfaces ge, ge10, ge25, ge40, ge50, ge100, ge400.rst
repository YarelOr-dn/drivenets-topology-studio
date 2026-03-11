interfaces ge10, ge100, ge400
---------------------------------------------------

**Minimum user role:** operator

To configure a physical interface:

**Command syntax: ge<speed>-<interface id>**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to physical interfaces.


**Parameter table**

+--------------+-------------------------------------+---------------------------------+------------+
|              |                                     |                                 |            |
| Parameter    | Description                         | Range                           | Default    |
+==============+=====================================+=================================+============+
|              |                                     |                                 |            |
| speed        | The speed of the physical port      | 10                              | \-         |
|              |                                     |                                 |            |
|              |                                     | 100                             |            |
|              |                                     |                                 |            |
|              |                                     | 400                             |            |
+--------------+-------------------------------------+---------------------------------+------------+
| id           | The ID of the specific port         | ge<interface speed>-<A>/<B>/<C> | \-         |
|              |                                     |                                 |            |
|              |                                     | <A> = ncp   id 0-255            |            |
|              |                                     |                                 |            |
|              |                                     | <B> = slot   id 0-255           |            |
|              |                                     |                                 |            |
|              |                                     | <C> = port   id                 |            |
+--------------+-------------------------------------+---------------------------------+------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# ge100-1/1/1
	dnRouter(cfg-if-ge100-1/1/1)# admin-state enabled

	dnRouter(cfg-if)# ge10-1/1/1
	dnRouter(cfg-if-ge10-1/1/1)# ipv4-address 192.168.1.1/30

	dnRouter(cfg-if)# ge-1/1/1
	dnRouter(cfg-if-ge-1/1/1)# mtu 9200

..	dnRouter(cfg-if)# ge25-1/1/1
	dnRouter(cfg-if-ge25-1/1/1)# mpls enabled

	dnRouter(cfg-if)# ge40-1/1/1
	dnRouter(cfg-if-ge40-1/1/1)# ipv6-address 2001:1234::1/122


**Removing Configuration**

To revert to the default values:
::

	dnRouter(cfg-if)# no ge100-1/1/1
	dnRouter(cfg-if)# no ge400-1/1/1

.. **Help line:** Configure interface parameters

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 5.1         | Command introduced    |
+-------------+-----------------------+
