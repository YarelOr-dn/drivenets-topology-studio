interfaces urpf mode
--------------------

**Minimum user role:** operator

Set the uRPF operation mode. When set, uRPF validation applies to both IPV4 and IPv6 unicast packets:

**Command syntax: mode [mode]**

**Command mode:** config

**Hierarchies**

- interfaces urpf

**Note**

- The command is applicable to the following interface types:

  - Bundle
  - Bundle vlan
  - Physical
  - Physical vlan
  - IRB

- A forwarding table entry that results in a discard action (RTBH) will be ignored for uRPF validity check. That is, IP packet received with a Source IP that is resolved to a route with next-hop null0 will be dropped by the uRPF validity check.

**Parameter table**

+-----------+-------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                   | Range | Default |
+===========+===============================================================================+=======+=========+
| mode      | A match in the forwarding table is sufficient to pass the uRPF validity check | loose | loose   |
+-----------+-------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# urpf
    dnRouter(cfg-if-bundle-1-urpf)# mode loose


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1-urpf)# no mode

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
