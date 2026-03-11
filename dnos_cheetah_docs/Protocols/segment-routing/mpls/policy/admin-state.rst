protocols segment-routing mpls policy admin-state
-------------------------------------------------

**Minimum user role:** operator

When disabled, a configured policy will not be used for traffic forwarding.

To enable/disable a segment-routing policy:


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Parameter table**

+-------------+-----------------------+--------------+---------+
| Parameter   | Description           | Range        | Default |
+=============+=======================+==============+=========+
| admin-state | SR policy admin state | | enabled    | enabled |
|             |                       | | disabled   |         |
+-------------+-----------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# admin-state disabled


**Removing Configuration**

To return the admin-state to its default value:
::

    dnRouter(cfg-sr-mpls-policy)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
