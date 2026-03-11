network-services multihoming interface esi value
------------------------------------------------

**Minimum user role:** operator

Sets the ESI of the interface.

**Command syntax: esi [esi-type] value [esi-value]**

**Command mode:** config

**Hierarchies**

- network-services multihoming interface

**Note**

- Only the Arbitrary Type requires a Value.

**Parameter table**

+-----------+-----------------------------------------+-----------+---------+
| Parameter | Description                             | Range     | Default |
+===========+=========================================+===========+=========+
| esi-type  | the ESI                                 | arbitrary | \-      |
+-----------+-----------------------------------------+-----------+---------+
| esi-value | Define the value for the Arbitrary Type | \-        | \-      |
+-----------+-----------------------------------------+-----------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# multihoming
    dnRouter(cfg-netsrv-mh)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-mh-int)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-netsrv-mh-int)# no esi

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
