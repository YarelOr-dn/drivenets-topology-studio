forwarding-options ipv4-verify checksum
---------------------------------------

**Minimum user role:** operator

To configure whether or not the checksum in ipv4 header will be verified by the NCP for incoming traffic:

**Command syntax: checksum [admin-state]**

**Command mode:** config

**Hierarchies**

- forwarding-options ipv4-verify

**Note**
- The default is enabled, meaning, the checksum header is verified and if found invalid the packet is dropped.

**Parameter table**

+-------------+--------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                        | Range        | Default |
+=============+====================================================================+==============+=========+
| admin-state | When disabled, npu will not veify ipv4 header checksum correctness | | enabled    | enabled |
|             |                                                                    | | disabled   |         |
+-------------+--------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# forwarding-options
    dnRouter(cfg-fwd_opts)# ipv4-verify
    dnRouter(cfg-fwd_opts-ipv4-ver)# checksum enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-fwd_opts-ipv4-ver)# no checksum

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
