protocols isis instance lsp-mtu
-------------------------------

**Minimum user role:** operator

To configure the maximum size of generated LSPs:


**Command syntax: lsp-mtu [mtu]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- For isis to work properly in isis domain, lsp-mtu must be lower than any L2 MTU of any IS-IS enabled interface in that domain.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                                      | Range    | Default |
+===========+==================================================================================+==========+=========+
| mtu       | Sets the maximum size (in bytes) of LSPs. The value must be lower than the L3    | 512-9205 | 1497    |
|           | MTU-3 of any IS-IS enabled interface (3 bytes due to the LLC header).            |          |         |
+-----------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# lsp-mtu 600


**Removing Configuration**

To revert to the default MTU:
::

    dnRouter(cfg-protocols-isis-inst)# no lsp-mtu

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 6.0     | Command introduced    |
+---------+-----------------------+
| 9.0     | Command not supported |
+---------+-----------------------+
