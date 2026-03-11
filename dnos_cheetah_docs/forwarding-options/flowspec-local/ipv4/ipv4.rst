forwarding-options flowspec-local ipv4
--------------------------------------

**Minimum user role:** operator

Install the ipv4 flowspec-local policy.

**Command syntax: ipv4**

**Command mode:** config

**Hierarchies**

- forwarding-options flowspec-local

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# ipv4
    dnRouter(cfg-fwd_opts-ipv4)#


**Removing Configuration**

To remove the ipv4 flowspec-local configuration:
::

    dnRouter(cfg-fwd_opts)# no ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
