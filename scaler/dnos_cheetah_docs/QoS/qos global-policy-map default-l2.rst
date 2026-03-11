qos global-policy-map default-l2
--------------------------------

**Minimum user role:** operator

To configure a default qos-tag and drop-tag tuple for L2 traffic:

**Command syntax: qos-tag [gos-tag]** drop-tag [drop-tag]

**Command mode:** config

**Hierarchies**

- qos global-policy-map default-l2 

**Parameter table**

+---------------+-----------------------+-----------+-------------+
|               |                       |           |             |
| Parameter     | Description           | Range     | Default     |
+===============+=======================+===========+=============+
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
  dnRouter(cfg-qos)# global-policy-map default-l2
  dnRouter(cfg-qos-default-l2)#
  dnRouter(cfg-qos-default-l2)# qos-tag 6
  dnRouter(cfg-qos-default-l2)# qos-tag 6 drop-tag green

**Removing Configuration**

To revert the map configuration to default:
::

  dnRouter(cfg-qos-default-l2)#no qos-tag

.. **Help line:** configure qos layer 2 default-class map entry

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+