forwarding-options ipv4-verify
------------------------------

**Minimum user role:** operator

To set ipv4 packet verifications, enter ipv4-verify configuration level

**Command syntax: ipv4-verify**

**Command mode:** config

**Hierarchies**

- forwarding-options

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# ipv4-verify
    dnRouter(cfg-fwd_opts-ipv4-ver)#


**Removing Configuration**

To return all ipv4 packet verification settings to default:
::

    dnRouter(cfg-fwd_opts)# no ipv4-verify

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
