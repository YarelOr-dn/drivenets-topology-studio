protocols isis instance address-family ipv4-unicast traffic-engineering level level-2
-------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure IS-IS to send an MPLS traffic engineering link information (e.g. available bandwidth):


**Command syntax: traffic-engineering level level-2 [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv4-unicast

**Note**
- This command applies to IS-IS level-2 only.
- IS-IS TE is automatically assigned according to router-id. The router-id is identical for all IS-IS instances.


**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | The administrative state of the traffic engineering feature for the IS-IS Level  | | enabled    | \-      |
|             | 2 per address-family.                                                            | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# traffic-engineering level level-2 enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-afi)# no traffic-engineering level level-2  enabled

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
