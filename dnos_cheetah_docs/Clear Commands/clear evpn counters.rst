clear evpn counters
-------------------

**Minimum user role:** operator

To reset the evpn service instance counters:

**Command syntax: clear evpn counters** {instance [instance-name]}

**Command mode:** operation

.. **Hierarchies**

**Note**

- The Attachment Circuit (AC) counters are not reset.

**Parameter table**

+---------------+-------------------------------+------------+---------+
| Parameter     | Description                   | Range      | Default |
+===============+===============================+============+=========+
| instance-name | The configured evpn instance. | String     | \-      |
|               |                               | 1..255     |         |
+---------------+-------------------------------+------------+---------+

**Example**
::

	dnRouter# clear evpn counters instance evpn1


.. **Help line:**

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 18.2    | Command introduced                                |
+---------+---------------------------------------------------+
