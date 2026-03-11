system network-resources resource port-pairs
--------------------------------------------

**Minimum user role:** operator

To configure the list port-pairs assoicated with the resource

**Command syntax: port-pairs [pp]** [, pp, pp]

**Command mode:** config

**Hierarchies**

- system network-resources resource

**Note**

- only “allow” rules in the ACL will be referred with 3-tuple pattern

- src-ip/dest-ip must be /32 addresses

- protocol must be either tcp(0x06) or udp(0x17)

- other rules will not be referred

**Parameter table**

+-----------+----------------------------------------------------------------------------------+----------------+---------+
| Parameter | Description                                                                      | Range          | Default |
+===========+==================================================================================+================+=========+
| pp        | List of port-pairs (interface pool) that are owned by this network-function      | | string       | \-      |
|           | (resource) instance                                                              | | length 1-8   |         |
+-----------+----------------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# network-resources
    dnRouter(cfg-system-netres)# resource nat-resource-1
    dnRouter(cfg-system-netres-res)# port-pairs pp0 pp1


**Removing Configuration**

To remove the bypass-list from specified NAT instance
::

    dnRouter(cfg-system-netres-res)# no port-pairs

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
