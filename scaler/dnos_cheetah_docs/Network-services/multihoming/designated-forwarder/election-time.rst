network-services multihoming designated-forwarder election-time
---------------------------------------------------------------

**Minimum user role:** operator

Set the default value for the election time upon configuration - how many seconds to wait for the Route Type 4 response from the PE devices.
This value can be modified per interface by using the per-interface knob.

**Command syntax: election-time [election-time]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+---------------+-------------------------------------------+-------+---------+
| Parameter     | Description                               | Range | Default |
+===============+===========================================+=======+=========+
| election-time | time in seconds to wait for Type 4 routes | 0-300 | 3       |
+---------------+-------------------------------------------+-------+---------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# election-time 5
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To revert the default election-time configuration to its default of 3 seconds.
::

    dnRouter(cfg-netsrv-mh-df)# no election-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
