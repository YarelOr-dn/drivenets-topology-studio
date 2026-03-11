protocols segment-routing mpls policy seamless-bfd
--------------------------------------------------

**Minimum user role:** operator

To configure the seamless-BFD session that will be applied on the path(s) of the policy.

**Command syntax: seamless-bfd**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# seamless-bfd
    dnRouter(cfg-mpls-policy-sbfd)#


**Removing Configuration**

To remove the seamless-bfd sessions on the SR policy:
::

    dnRouter(cfg-sr-mpls-policy)# no seamless-bfd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
