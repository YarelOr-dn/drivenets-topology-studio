protocols bgp fast-external-failover
------------------------------------

**Minimum user role:** operator

This command instructs the BGP process to immediately terminate external BGP peering sessions of directly adjacent neighbors if the link used to reach these neighbors goes down, without waiting for the hold-down timer to expire:

**Command syntax: fast-external-failover [fast-external-failover]**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- This option is enabled by default.

**Parameter table**

+------------------------+---------------------------------------------+--------------+---------+
| Parameter              | Description                                 | Range        | Default |
+========================+=============================================+==============+=========+
| fast-external-failover | fast peer termination for unreachable peers | | enabled    | enabled |
|                        |                                             | | disabled   |         |
+------------------------+---------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# fast-external-failover disabled
    dnRouter(cfg-protocols-bgp)# fast-external-failover enabled


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-protocols-bgp)# no fast-external-failover

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
