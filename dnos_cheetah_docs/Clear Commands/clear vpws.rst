clear vpws
----------

**Minimum user role:** operator

To manually reset all aspects related to the specified VPWS service, including counters:

**Command syntax: clear vpws** [instance-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table**

+---------------+-------------------------------+--------+---------+
| Parameter     | Description                   | Range  | Default |
+===============+===============================+========+=========+
| instance-name | The configured VPWS instance. | String | \-      |
|               |                               | 1..255 |         |
+---------------+-------------------------------+--------+---------+

**Example**
::

	dnRouter# clear vpws

    dnRouter# clear vpws R15_R16_1


.. **Help line:**

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 16.1    | Command introduced                                |
+---------+---------------------------------------------------+
