protocols isis instance address-family ipv4-unicast microloop-avoidance maximum-labels
--------------------------------------------------------------------------------------

**Minimum user role:** operator

Sets the maximum allowed number of labels on the SR-TE microloop-avoidance constructed label stack. 
If the calculated path exceed the allowed maximum, than a microloop-avoidance path will not be provided by ISIS.
To set the maximum-labels:

**Command syntax: maximum-labels [maximum-labels]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast microloop-avoidance

**Note**

- Microloop avoidance maximum-labels parameter is per IS-IS topology.

- In the event of single-topology, maximum-labels of ipv4-unicast address-family will define the maximum label stack of the microloop path for ipv6 prefixes as well.

**Parameter table**

+----------------+-----------------------------------------------------------+-------+---------+
| Parameter      | Description                                               | Range | Default |
+================+===========================================================+=======+=========+
| maximum-labels | Maximum allowed labels to be added for the microloop path | 1-3   | 3       |
+----------------+-----------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)# maximum-labels 1
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)# maximum-labels 1


**Removing Configuration**

To revert maximum-labels to the default value:
::

    dnRouter(cfg-inst-afi-uloop)# no maximum-labels

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.3    | Command introduced |
+---------+--------------------+
