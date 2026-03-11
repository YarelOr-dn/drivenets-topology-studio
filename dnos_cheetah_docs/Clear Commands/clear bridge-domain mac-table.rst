clear bridge-domain mac-table
-----------------------------

**Minimum user role:** operator

To remove/flush the learned mac-table entries of a bridge-domain:

**Command syntax: clear bridge-domain mac-table** {instance [instance-name]}
**Command syntax: clear bridge-domain mac-table** {instance [instance-name] interface [interface-name]}
**Command syntax: clear bridge-domain mac-table** {instance [instance-name] interface [interface-name] mac [mac-address]}

**Command mode:** operation

.. **Hierarchies**

**Note**

- Removes the MAC Table entry/entries.

**Parameter table**

+----------------+-----------------------------------------------+-------------------+---------+
| Parameter      | Description                                   | Range             | Default |
+================+===============================================+===================+=========+
| instance-name  | The configured bridge-domain instance.        | String            | \-      |
|                |                                               | 1..255            |         |
+----------------+-----------------------------------------------+-------------------+---------+
| interface-name | The name of the physical or bundle interface. | String            | \-      |
+----------------+-----------------------------------------------+-------------------+---------+
| mac-address    | The mac address to be removed.                | String            | \-      |
|                |                                               | xx:xx:xx:xx:xx:xx |         |
+----------------+-----------------------------------------------+-------------------+---------+

**Example**
::

	dnRouter# clear bridge-domain mac-table

    dnRouter# clear bridge-domain mac-table instance MyBridge1

    dnRouter# clear bridge-domain mac-table instance MyBridge1 interface bundle-10

    dnRouter# clear bridge-domain mac-table instance MyBridge1 interface bundle-10 mac a1:b2:98:21:fe:07

.. **Help line:**

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 17.2    | Command introduced                                |
+---------+---------------------------------------------------+
