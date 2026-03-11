system snmp trap-server max-throughput
--------------------------------------

**Minimum user role:** operator

To configure the SNMP max-throughput. This is the maximum number of traps that are send to the server in one second. If the generated traps are larger then this, then the rest of the traps will be discared.

**Command syntax: max-throughput [max-throughput]**

**Command mode:** config

**Hierarchies**

- system snmp trap-server

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter      | Description                                                                      | Range  | Default |
+================+==================================================================================+========+=========+
| max-throughput | Maximum numbers of traps that can be sent to the server in one second. If there  | 1-1000 | 100     |
|                | is a larger number of traps generated then everything above the value of the     |        |         |
|                | throughput will be discarded                                                     |        |         |
+----------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# snmp
    dnRouter(cfg-system-snmp)# trap-server 1.2.3.4 vrf default
    dnRouter(cfg-system-snmp-trap-server)# max-throughput 1000
    dnRouter(cfg-system-snmp)# trap-server 1.2.3.5 vrf mgmt0
    dnRouter(cfg-system-snmp-trap-server)# max-throughput 300


**Removing Configuration**

To revert the max throughput to default
::

    dnRouter(cfg-system-snmp-trap-server)# no max-throughput

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.2.3  | Command introduced |
+---------+--------------------+
