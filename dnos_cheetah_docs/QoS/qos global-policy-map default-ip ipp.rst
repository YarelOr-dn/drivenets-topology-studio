qos global-policy-map default-ip ipp
------------------------------------

**Minimum user role:** operator

This command sets all the default calss map entries corresponding to the IP precedence bits to a specified common qos-tag and drop-tag tuple.

For example, **ipp 1 qos-tag 3** will set dscp 8,9,10,11,12,13,14,15 entries in the map to qos-tag 3 and drop-tag green.

To change the default PHB selection for IP traffic based on IP precedence:

**Command syntax: ipp [ipp] qos-tag [gos-tag]** drop-tag [drop-tag]

**Command mode:** config

**Hierarchies**

- qos global-policy-map default-ip

**Parameter table**

+---------------+----------------------------+-----------+-------------+
|               |                            |           |             |
| Parameter     | Description                | Range     | Default     |
+===============+============================+===========+=============+
|               |                            |           |             |
| ipp           | The IP precedence value    | 0..7      | \-          |
+---------------+----------------------------+-----------+-------------+
|               |                            |           |             |
| qos-tag       | The QoS-tag value          | 0..7      | \-          |
+---------------+----------------------------+-----------+-------------+
|               |                            |           |             |
| drop-tag      | The drop-tag value         | green     | green       |
|               |                            |           |             |
|               |                            | yellow    |             |
+---------------+----------------------------+-----------+-------------+

**Example**
::

  dnRouter# configure
  dnRouter(cfg)# qos
  dnRouter(cfg-qos)# global-policy-map default-ip
  dnRouter(cfg-qos-default-ip)#
  dnRouter(cfg-qos-default-ip)# ipp 4 qos-tag 2 drop-tag yellow

The following example the command will set the DSCP 8, 9, 10, 11, 12, 13, 14, and 15 entries in the map to qos-tag 3 and drop-tag green:
::

  dnRouter(cfg-qos-default-ip)# ipp 5 qos-tag 3


**Removing Configuration**

To revert to the default value:
::

  dnRouter(cfg-qos-default-ip)#no ipp 4


.. **Help line:** configure qos IP default phb selection

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 13.0        | Command introduced    |
+-------------+-----------------------+