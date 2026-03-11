protocols isis instance address-family ipv6-unicast microloop-avoidance admin-state
-----------------------------------------------------------------------------------

**Minimum user role:** operator

To enable microloop avoidance:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast microloop-avoidance

**Note**
- Microloop avoidance works per address-family and not per topology.
- In the event of a single-topology, the microloop-avoidance is required to be enabled for the ipv6-unicast address-family to provide avoidance for the ipv6 prefixes.

**Parameter table**

+-------------+----------------------------+--------------+----------+
| Parameter   | Description                | Range        | Default  |
+=============+============================+==============+==========+
| admin-state | Enable microloop avoidance | | enabled    | disabled |
|             |                            | | disabled   |          |
+-------------+----------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)# admin-state enabled
    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# microloop-avoidance
    dnRouter(cfg-inst-afi-uloop)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-inst-afi-uloop)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
