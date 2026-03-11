protocols segment-routing mpls auto-policy template color admin-state
---------------------------------------------------------------------

**Minimum user role:** operator

When disabled, a policy created by this auto-policy template will not be used for traffic forwarding.

To enable/disable policies created by a specific SR-TE auto policy template:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color

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
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# admin-state enabled


**Removing Configuration**

To return the admin-state to its default value:
::

    dnRouter(cfg-mpls-auto-policy-color-3)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
