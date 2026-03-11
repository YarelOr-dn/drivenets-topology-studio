qos global-policy-map default-mpls mpls-exp
-------------------------------------------

**Minimum user role:** operator

To configure the default QoS MPLS PHB selection:

**Command syntax: mpls-exp [mpls-exp] qos-tag [gos-tag]** drop-tag [drop-tag]

**Command mode:** config

**Hierarchies**

- qos global-policy-map default-ip

**Parameter table**

+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| Parameter     | Description           | Range     | Default     |
+===============+=======================+===========+=============+
|               |                       |           |             |
| mpls-exp      | The MPLS exp value    | 0..7      | \-          |
+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| qos-tag       | The QoS-tag value     | 0..7      | \-          |
+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| drop-tag      | The drop-tag value    | green     | green       |
|               |                       |           |             |
|               |                       | yellow    |             |
+---------------+-----------------------+-----------+-------------+

**Example**
::

  dnRouter# configure
  dnRouter(cfg)# qos
  dnRouter(cfg-qos)# global-policy-map default-mpls
  dnRouter(cfg-qos-default-mpls)#
  dnRouter(cfg-qos-default-mpls)# mpls-exp 2 qos-tag 3
  dnRouter(cfg-qos-default-mpls)# mpls-exp 2 qos-tag 3 drop-tag yellow


**Removing Configuration**

To revert the default-mpls entry to its default value:
::

  dnRouter(cfg-qos-default-mpls)# no mpls-exp 2

.. **Help line:** configure qos MPLS default phb selection

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+