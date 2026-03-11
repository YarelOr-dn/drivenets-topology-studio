clear evpn restore-cycles
-------------------------

**Minimum user role:** operator

To reset the evpn service instance restore-cycles:

**Command syntax: clear evpn restore-cyles** {service [instance-name] mac [mac-address]}

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

	dnRouter# clear evpn restore-cycles service evpn1 mac  a2:76:b0:08:9e:02


.. **Help line:**

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 18.3    | Command introduced                                |
+---------+---------------------------------------------------+
