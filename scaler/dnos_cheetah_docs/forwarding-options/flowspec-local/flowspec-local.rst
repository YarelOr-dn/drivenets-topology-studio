forwarding-options flowspec-local
---------------------------------

**Minimum user role:** operator

To install a flowspec local policy.

**Command syntax: flowspec-local**

**Command mode:** config

**Hierarchies**

- forwarding-options

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# flowspec-local
    dnRouter(cfg-rpl-fl)#


**Removing Configuration**

To remove the installed flowspec-local policy:
::

    dnRouter(cfg-fwd_opts)# no flowspec-local

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
