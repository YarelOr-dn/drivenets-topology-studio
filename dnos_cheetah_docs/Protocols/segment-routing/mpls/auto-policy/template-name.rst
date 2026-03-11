protocols segment-routing mpls auto-policy template-name
--------------------------------------------------------

**Minimum user role:** operator

To overwrite the default prefix for the name of auto-policies created with auto-policy templates:

**Command syntax: template-name [template-name]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy

**Note**
- The default name format for policies created by the auto-policy template: Auto_c_colorValue_dest_DestIp.

- Changing the tempalte-name will not affect running auto-policies created by existing templates.

**Parameter table**

+---------------+-----------------------------------------------------------------------------+-----------------+---------+
| Parameter     | Description                                                                 | Range           | Default |
+===============+=============================================================================+=================+=========+
| template-name | The prefix for the name of auto-policies created with auto-policy templates | | string        | Auto    |
|               |                                                                             | | length 1-64   |         |
+---------------+-----------------------------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template-name auto-policy


**Removing Configuration**

To revert the SR-TE auto policy template-name to its default value:
::

    dnRouter(cfg-sr-mpls-auto-policy)# no template-name

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
