protocols isis instance address-family ipv6-unicast traffic-engineering
-----------------------------------------------------------------------

**Minimum user role:** operator

To configure IS-IS to send MPLS traffic engineering link information (e.g. available bandwidth):


**Command syntax: traffic-engineering [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Note**
- This command applies to IS-IS level-1 and level-2
- In case an explicit level in configured, the explicit configuration is imposed
- IS-IS TE is automatically assigned according to router-id. The router-id is identical for all IS-IS instances.


**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | The administrative state of the traffic engineering feature for the IS-IS Level  | | enabled    | disabled |
|             | 2 per address-family.                                                            | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# traffic-engineering enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-afi)# no traffic-engineering enabled

**Command History**

+---------+-----------------------------------------------+
| Release | Modification                                  |
+=========+===============================================+
| 9.0     | Command introduced                            |
+---------+-----------------------------------------------+
| 19.1    | Command updated to effect level-1 and level-2 |
+---------+-----------------------------------------------+
