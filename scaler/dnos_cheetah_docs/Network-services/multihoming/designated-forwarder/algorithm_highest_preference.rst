network-services multihoming designated-forwarder algorithm highest-preference value
------------------------------------------------------------------------------------

**Minimum user role:** operator

Defines the default value to be the highest-preference algorithm, for the algorithm that the user would like to use to choose the Designated Forwarder.
This value can be modified per interface by setting the per interface knob.

**Command syntax: algorithm highest-preference value [preference-value]**

**Command mode:** config

**Hierarchies**

- network-services multihoming designated-forwarder

**Parameter table**

+------------------+----------------------+---------+---------+
| Parameter        | Description          | Range   | Default |
+==================+======================+=========+=========+
| preference-value | The preference value | 0-65535 | \-      |
+------------------+----------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# designated-forwarder
    dnRouter(cfg-netsrv-mh-df)# algorithm highest-preference value 10000
    dnRouter(cfg-netsrv-mh-df)#


**Removing Configuration**

To restore the default value of the algorithm to mod.
::

    dnRouter(cfg-netsrv-mh-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
