interfaces description
----------------------

**Minimum user role:** operator

To provide a textual interface description for the interface, use the following command:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan
  - Loopback
  - Control
  - gre-tunnel
  - IRB
  - Logical Management
  - ICE

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| description | Provide a description for the interface. Enter free-text description with spaces | | string         | \-      |
|             | in between quotation marks.  If you do not use quotation marks, do not use       | | length 1-255   |         |
|             | spaces.                                                                          |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces

    dnRouter(cfg-if)# ge10-2/1/1
    dnRouter(cfg-if-ge10-2/1/1)# description MyInterfaceDescription

    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# description "The First Bundle Port"

    dnRouter(cfg-if)# bundle-1.100
    dnRouter(cfg-if-bundle-1.100)# description ThisIsMyVlanInterface

    dnRouter(cfg-if)# lo1
    dnRouter(cfg-if-lo1)# description RouterIdLoopback

    dnRouter(cfg-if)# gre-tunnel-0
    dnRouter(cfg-if-gre-0)# description ISISregion0_to_remote_HOST

    dnRouter(cfg-if)# ctrl-ncp-0/0
    dnRouter(cfg-if-ctrl-ncp-0/0)# description MyControlNCPInterfaceDescription


**Removing Configuration**

To remove the interface description:
::

    dnRouter(cfg-if-ge10-2/1/1)# no description

::

    dnRouter(cfg-if-bundle-1.100)# no description

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces, applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 11.4    | Added support for GRE-tunnels                                      |
+---------+--------------------------------------------------------------------+
| 16.2    | Management bond interface removed                                  |
+---------+--------------------------------------------------------------------+
| 17.0    | Added support for NCM control ports                                |
+---------+--------------------------------------------------------------------+
| 19.10   | Added support for ICE interface                                    |
+---------+--------------------------------------------------------------------+
