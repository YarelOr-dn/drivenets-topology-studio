protocols isis instance lsp-flood-reduction max-lsp-replicas
------------------------------------------------------------

**Minimum user role:** operator

To configure the maximum number of lsp replicas to be sent over parallel interfaces when lsp-flood-reduction is in use:


**Command syntax: max-lsp-replicas [replicas]**

**Command mode:** config

**Hierarchies**

- protocols isis instance lsp-flood-reduction

**Parameter table**

+-----------+------------------------------------+-------+---------+
| Parameter | Description                        | Range | Default |
+===========+====================================+=======+=========+
| replicas  | The maximum number of lsp replicas | 2-64  | 2       |
+-----------+------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# lsp-flood-reduction
    dnRouter(cfg-isis-inst-lspfr)# max-lsp-replicas 3


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-lspfr)# no max-lsp-replicas

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
