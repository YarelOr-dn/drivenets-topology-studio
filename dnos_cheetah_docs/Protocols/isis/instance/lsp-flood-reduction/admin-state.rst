protocols isis instance lsp-flood-reduction admin-state
-------------------------------------------------------

**Minimum user role:** operator

To enable/disable lsp-flood-reduction:


**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance lsp-flood-reduction

**Parameter table**

+-------------+-------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                       | Range        | Default |
+=============+===================================================================+==============+=========+
| admin-state | The administrative state of the lsp-flood-reduction functionality | | enabled    | enabled |
|             |                                                                   | | disabled   |         |
+-------------+-------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# lsp-flood-reduction
    dnRouter(cfg-isis-inst-lspfr)# admin-state disabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-lspfr)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
