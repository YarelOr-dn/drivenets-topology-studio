protocols isis instance interface hello-padding
-----------------------------------------------

**Minimum user role:** operator

By default, hello PDUs are padded to the lsp-MTU size of the interface. This is in order to ensure there is no MTU mismatch before the adjacency is established, avoiding the risk of LSP packet loss due to exceeded packet size.

To enable/disable padding:

**Command syntax: hello-padding [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface

**Parameter table**

+-------------+---------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                         | Range        | Default |
+=============+=====================================================================+==============+=========+
| admin-state | The administrative state of the padding option of IS-IS hello PDUs. | | enabled    | enabled |
|             |                                                                     | | disabled   |         |
+-------------+---------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-2
    dnRouter(cfg-isis-inst-if)# hello-padding enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-isis-inst-if)# no hello-padding

**Command History**

+---------+----------------------+
| Release | Modification         |
+=========+======================+
| 6.0     | Command introduced   |
+---------+----------------------+
| 9.0     | Command removed      |
+---------+----------------------+
| 10.0    | Command reintroduced |
+---------+----------------------+
