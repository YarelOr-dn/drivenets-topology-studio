services l2-cross-connect interfaces
------------------------------------

**Minimum user role:** operator

To configure the endpoint members of the xConnect service:

**Command syntax: interfaces [first-interface] [second-interface]**

**Command mode:** config

**Hierarchies**

- services l2-cross-connect

**Note**

- The command is applicable to the following interface types:

	- Physical vlan

	- Bundle vlan

- Only sub-interfaces that are defined as L2-service can be defined as L2-cross-connect member interfaces.

- The same interface cannot be configured twice in the same l2-cross-connect service.

- The same interface cannot be configured twice in two different l2-cross-connect services.

- Replacing a configured l2-interface requires configuring both interfaces again.

- Up to 32 cross connects can be configured on the system collectively.

**Parameter table**

+------------------+--------------------------------+------------------+---------+
| Parameter        | Description                    | Range            | Default |
+==================+================================+==================+=========+
| first-interface  | Cross connect first interface  | | string         | \-      |
|                  |                                | | length 1-255   |         |
+------------------+--------------------------------+------------------+---------+
| second-interface | Cross connect second interface | | string         | \-      |
|                  |                                | | length 1-255   |         |
+------------------+--------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# l2-cross-connect XC-To-Boston-CRS
    dnRouter(cfg-srv-l2xc)# interfaces bundle-100.2 bundle-200.3

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# l2-cross-connect XC-To-LA-NVP
    dnRouter(cfg-srv-l2xc)# interfaces ge100-0/0/2.32 ge400-0/0/23.93


**Removing Configuration**

To remove the interface endpoints (both interfaces are removed):
::

    dnRouter(cfg-srv-l2xc)# no interfaces

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
