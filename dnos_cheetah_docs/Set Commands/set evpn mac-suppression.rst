set evpn mac-suppression
------------------------

**Minimum user role:** operator

To set suppression on a mac-address of an evpn service instance:

**Command syntax: set evpn mac-suppression** service [instance-name] mac [mac-address]

**Command mode:** operation

.. **Hierarchies**


**Parameter table**

+---------------+-------------------------------+------------+---------+
| Parameter     | Description                   | Range      | Default |
+===============+===============================+============+=========+
| instance-name | The configured evpn instance. | String     | \-      |
|               |                               | 1..255     |         |
+---------------+-------------------------------+------------+---------+
| mac-address   | The specific mac-address      | String     |         |
+---------------+-------------------------------+------------+---------+

**Example**
::

	dnRouter# set evpn mac-suppression service evpn1 mac  a2:76:b0:08:9e:02


.. **Help line:**

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 18.3    | Command introduced                                |
+---------+---------------------------------------------------+
