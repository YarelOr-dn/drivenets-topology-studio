network-services multihoming interface designated-forwarder election-time
-------------------------------------------------------------------------

**Minimum user role:** operator

Set the election time - how many seconds to wait for the Route Type 4 response from the PE devices.

**Command syntax: election-time [election-time]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface designated-forwarder

**Parameter table**

+---------------+-------------------------------------------+-------+---------+
| Parameter     | Description                               | Range | Default |
+===============+===========================================+=======+=========+
| election-time | time in seconds to wait for Type 4 routes | 0-300 | \-      |
+---------------+-------------------------------------------+-------+---------+

**Example**
::

    dev-dnRouter#
    dev-dnRouter# configure
    dev-dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# designated-forwarder
    dnRouter(cfg-mh-int-df)# election-time 5
    dnRouter(cfg-mh-int-df)#


**Removing Configuration**

To revert the election-time configuration to its default as configured under multihoming.
::

    dnRouter(cfg-mh-int-df)# no election-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
