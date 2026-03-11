system grpc vrf client-list type
--------------------------------

**Minimum user role:** operator

This command defines whether the configured client-list (see \"system grpc vrf client-list\" is a white list or a black list. This will determine if the listed clients will be granted access to the gRPC server.

**Command syntax: client-list type [list-type]**

**Command mode:** config

**Hierarchies**

- system grpc vrf

**Note**

- If the client-list type is set to "allow", the client-list must not be empty.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter | Description                                                                      | Range     | Default |
+===========+==================================================================================+===========+=========+
| list-type | Configure black or white list type of incoming IP-addresses for gNMI/gRPC        | | allow   | deny    |
|           | service                                                                          | | deny    |         |
+-----------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc vrf default
    dnRouter(cfg-system-grpc-vrf)# client-list type allow


**Removing Configuration**

To revert the list type to default:
::

    dnRouter(cfg-system-grpc-vrf)# no client-list type

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
