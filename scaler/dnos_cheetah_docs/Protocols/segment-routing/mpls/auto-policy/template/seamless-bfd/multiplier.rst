protocols segment-routing mpls auto-policy template color seamless-bfd multiplier
---------------------------------------------------------------------------------

**Minimum user role:** operator

Configure a Multiplier value which will be used for the S-BFD session.

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color seamless-bfd

**Parameter table**

+------------+----------------------------+-------+---------+
| Parameter  | Description                | Range | Default |
+============+============================+=======+=========+
| multiplier | set local S-BFD multiplier | 2-16  | 3       |
+------------+----------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# seamless-bfd
    dnRouter(cfg-auto-policy-color-3-sbfd)# multiplier 5


**Removing Configuration**

To remove the multiplier value:
::

    dnRouter(cfg-auto-policy-color-3-sbfd) no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
