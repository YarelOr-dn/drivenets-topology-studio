protocols segment-routing mpls auto-policy template color seamless-bfd admin-state
----------------------------------------------------------------------------------

**Minimum user role:** operator

When disabled, the S-BFD session(s) will not be initiated on for auto-policies created with this template.

To enable/disable the S-BFD session(s):

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color seamless-bfd

**Parameter table**

+-------------+------------------------------+--------------+----------+
| Parameter   | Description                  | Range        | Default  |
+=============+==============================+==============+==========+
| admin-state | S-BFD Session(s) admin state | | enabled    | disabled |
|             |                              | | disabled   |          |
+-------------+------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# seamless-bfd
    dnRouter(cfg-auto-policy-color-3-sbfd)# admin-state enabled


**Removing Configuration**

To return the admin-state to its default value:
::

    dnRouter(cfg-auto-policy-color-3-sbfd) no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
