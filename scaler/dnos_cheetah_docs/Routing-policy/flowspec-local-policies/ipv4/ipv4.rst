routing-policy flowspec-local-policies ipv4
-------------------------------------------

**Minimum user role:** operator

Define the ipv4 address family MCs and rules:

**Command syntax: ipv4**

**Command mode:** config

**Hierarchies**

- routing-policy flowspec-local-policies

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# flowspec-local-policies
    dnRouter(cfg-rpl-flp)# ipv4
    dnRouter(cfg-rpl-flp-ipv4)#


**Removing Configuration**

To remove the ipv4 configurations:
::

    dnRouter(cfg-rpl-flp)# no ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
