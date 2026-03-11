routing-policy flowspec-local-policies ipv6
-------------------------------------------

**Minimum user role:** operator

Defines the ipv6 address family MCs and rules.

**Command syntax: ipv6**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv6
    dnRouter(cfg-rpl-flp-ipv6)#


**Removing Configuration**

To remove the ipv6 configurations:
::

    dnRouter(cfg-rpl-flp)# no ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
