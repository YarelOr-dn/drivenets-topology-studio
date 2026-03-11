protocols segment-routing mpls policy seamless-bfd multiplier
-------------------------------------------------------------

**Minimum user role:** operator

Configure a multiplier value which will be used for the S-BFD session.

**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy seamless-bfd

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
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# seamless-bfd
    dnRouter(cfg-mpls-policy-sbfd)# multiplier 5
    dnRouter(cfg-mpls-policy-sbfd)#


**Removing Configuration**

To remove the multiplier value:
::

    dnRouter(cfg-mpls-policy-sbfd) no multiplier

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
