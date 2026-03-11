interfaces port-pair
--------------------

**Minimum user role:** operator

To attach a port-pair to a virtual L2 interface:

**Command syntax: port-pair [port-pair]** [, port-pair, port-pair]

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to all virtual L2 interfaces.

- Multiple port pairs can be attached to a virtual L2 interface.

- When multiple port pairs are attached, the interface will use them as a bundle.

**Parameter table**

+-----------+---------------------------------------------------------------+----------------+---------+
| Parameter | Description                                                   | Range          | Default |
+===========+===============================================================+================+=========+
| port-pair | List of port-pairs used to implement the virtual L2 interface | | string       | \-      |
|           |                                                               | | length 1-8   |         |
+-----------+---------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# nat-0
    dnRouter(cfg-if-nat-0)# port-pair pp0
    dnRouter(cfg-if-nat-0)# port-pair pp1

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ipsec-0
    dnRouter(cfg-if-ipsec-0)# port-pair pp2


**Removing Configuration**

To remove the attachment of a port-pair from a virtual L2 interface:
::

    dnRouter(cfg-if-nat-0)# no port-pair

**Command History**

+----------+--------------------+
| Release  | Modification       |
+==========+====================+
| 18.0.11  | Command introduced |
+----------+--------------------+
