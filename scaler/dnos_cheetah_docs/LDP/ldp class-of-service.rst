ldp class-of-service
--------------------

**Minimum user role:** operator

To set the DSCP value for outgoing LDP packets:

**Command syntax: class-of-service [dscp-value]**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Note**

- IPP is set accordingly, i.e. a DSCP value of 48 is mapped to 6.

**Parameter table**

+---------------+--------------------------------------------+-----------+-------------+
|               |                                            |           |             |
| Parameter     | Description                                | Range     | Default     |
+===============+============================================+===========+=============+
|               |                                            |           |             |
| dscp-value    | The DSCP value for outgoing LDP packets    | 0..56     | 48          |
+---------------+--------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# class-of-service 50

**Removing Configuration**

To revert the dscp-value to the default value:
::

	dnRouter(cfg-protocols-ldp)# no class-of-service

.. **Help line:** Set DSCP for LDP packets.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 13.0      | Command introduced    |
+-----------+-----------------------+