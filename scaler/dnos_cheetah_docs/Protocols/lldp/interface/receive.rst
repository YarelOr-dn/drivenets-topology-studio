protocols lldp interface receive
--------------------------------

**Minimum user role:** operator

To configure lldp interface receive capability.

By default, reception of LLDP messages is available.

**Command syntax: receive [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols lldp interface

**Parameter table**

+-------------+----------------------------------------------+--------------+---------+
| Parameter   | Description                                  | Range        | Default |
+=============+==============================================+==============+=========+
| admin-state | Configures ability to receive LLDP messages. | | enabled    | enabled |
|             |                                              | | disabled   |         |
+-------------+----------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# interface ge100-2/4/1
    dnRouter(cfg-protocols-lldp-if)# receive enabled

    dnRouter(cfg-protocols-lldp)# interface ge100-4/2/1
    dnRouter(cfg-protocols-lldp-if)# receive disabled


**Removing Configuration**

To revert the receive capability to the default value:
::

    dnRouter(cfg-protocols-lldp-if)# no receive

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 7.0     | Command introduced                                         |
+---------+------------------------------------------------------------+
| 9.0     | Not supported in this version                              |
+---------+------------------------------------------------------------+
| 10.0    | Command reintroduced with admin-state "enabled" by default |
+---------+------------------------------------------------------------+
