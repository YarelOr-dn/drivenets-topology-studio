protocols msdp default-peer admin-state
---------------------------------------

**Minimum user role:** operator

To administratively enable/disable the MSDP default-peer, use the following command:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols msdp default-peer

**Parameter table**

+-------------+----------------------------------------+--------------+---------+
| Parameter   | Description                            | Range        | Default |
+=============+========================================+==============+=========+
| admin-state | Admin Enable/Disable MSDP default-peer | | enabled    | enabled |
|             |                                        | | disabled   |         |
+-------------+----------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 61.32.4.1
    dnRouter(cfg-protocols-msdp-default-peer)# admin-state disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# default-peer 61.32.4.1
    dnRouter(cfg-protocols-msdp-default-peer)# admin-state enabled


**Removing Configuration**

To revert the default-peer admin-state to its default configuration:
::

    dnRouter(cfg-protocols-msdp-default-peer)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
