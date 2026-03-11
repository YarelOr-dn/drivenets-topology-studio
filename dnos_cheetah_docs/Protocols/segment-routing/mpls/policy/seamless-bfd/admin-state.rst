protocols segment-routing mpls policy seamless-bfd admin-state
--------------------------------------------------------------

**Minimum user role:** operator

When disabled, the S-BFD session(s) is not initiated on the paths of the Segment Routing Policy.

To enable/disable the S-BFD session(s):

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy seamless-bfd

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
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# seamless-bfd
    dnRouter(cfg-mpls-policy-sbfd)# admin-state enabled
    dnRouter(cfg-mpls-policy-sbfd)#


**Removing Configuration**

To return the admin-state to its default value:
::

    dnRouter(cfg-mpls-policy-sbfd) no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
