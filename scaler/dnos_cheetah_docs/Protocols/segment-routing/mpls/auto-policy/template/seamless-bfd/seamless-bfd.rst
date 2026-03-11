protocols segment-routing mpls auto-policy template color seamless-bfd
----------------------------------------------------------------------

**Minimum user role:** operator

To configure the seamless-bfd session that will be applied on the path(s) of the policy

**Command syntax: seamless-bfd**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
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
| 19.0    | Command introduced |
+---------+--------------------+
