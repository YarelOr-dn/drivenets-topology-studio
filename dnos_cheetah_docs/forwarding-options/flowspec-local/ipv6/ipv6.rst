forwarding-options flowspec-local ipv6
--------------------------------------

**Minimum user role:** operator

Install the ipv6 flowspec-local policy.

**Command syntax: ipv6**

**Command mode:** config

**Hierarchies**

- forwarding-options flowspec-local

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# ipv6
    dnRouter(cfg-fwd_opts-ipv6)#


**Removing Configuration**

To remove the ipv6 flowspec-local configuration:
::

    dnRouter(cfg-fwd_opts)# no ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
