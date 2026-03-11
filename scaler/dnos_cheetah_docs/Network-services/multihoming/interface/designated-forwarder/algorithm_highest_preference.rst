network-services multihoming interface designated-forwarder algorithm highest-preference value
----------------------------------------------------------------------------------------------

**Minimum user role:** operator

Defines the highest-preference algorithm as the algorithm that the user would like to use to choose the Designated Forwarder.
The actual algorithm used will depend on agreement between all the PE devices attached to the same ES.

**Command syntax: algorithm highest-preference value [preference-value]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface designated-forwarder

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
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)# designated-forwarder
    dnRouter(cfg-mh-int-df)# algorithm highest-preference value 10000
    dnRouter(cfg-mh-int-df)#


**Removing Configuration**

To restore the algorithm to its default value.
::

    dnRouter(cfg-mh-int-df)# no algorithm

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
