protocols isis instance lsp-flood-reduction
-------------------------------------------

**Minimum user role:** operator

When utilizing high scale IS-IS deployment with a multitude of redundant links, reducing the amount of IS-IS flooding is sometimes required (in highly meshed environments).

When entering lsp-flood-reduction configuration level with lsp flood reduction enabled, the lsp flooding will be minimized when there are parallel interfaces to the same adjacent neighbor. LSP will be sent only over a subset of these interfaces.

To enter lsp-flood-reduction level:


**Command syntax: lsp-flood-reduction**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis)# lsp-flood-reduction
    dnRouter(cfg-isis-inst-lspfr)#


**Removing Configuration**

To remove all lsp-flood-reduction configuration:
::

    dnRouter(cfg-protocols-isis)# no lsp-flood-reduction

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
