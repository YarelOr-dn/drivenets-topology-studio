protocols isis instance address-family ipv4-unicast segment-routing mapping-server preference
---------------------------------------------------------------------------------------------

**Minimum user role:** operator

You can change the preference value of the mapping server - the higher the value the more preferred the server.

To configure the preference value for the mapping server:

**Command syntax: preference [preference]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast segment-routing mapping-server

**Note**

- Segment-routing can be enabled for a single IS-IS instance only.

**Parameter table**

+------------+----------------------------------------------------------------------------------+----------------+---------+
| Parameter  | Description                                                                      | Range          | Default |
+============+==================================================================================+================+=========+
| preference | The new preference value to be advertised                                        | 0-255/disabled | 128     |
|            | A value of 0 indicates that advertisements from this node must not be used. The  |                |         |
|            | preference TLV will not be advertised.                                           |                |         |
+------------+----------------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)# mapping-server
    dnRouter(cfg-afi-sr-mapping)# preference 200

    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# segment-routing
    dnRouter(cfg-inst-afi-sr)# mapping-server
    dnRouter(cfg-afi-sr-mapping)# preference disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-afi-sr-mapping)# no preference

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 14.0    | Command introduced |
+---------+--------------------+
