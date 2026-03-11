clear nat session
----------------------

**Minimum user role:** operator

To clear active dynamic nat44 sessions per specific NAT instance

**Command syntax: clear nat session** [instance-name]

**Command mode:** operation

.. **Hierarchies**

**Parameter table:**

+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+
|               |                                                                                                                 |                                                                   |             |
| Parameter     | Description                                                                                                     | Range                                                             | Default     |
+===============+=================================================================================================================+===================================================================+=============+
|               |                                                                                                                 | Any configured nat instance                                       |             |
| instance-name | Enter name of the specific NAT instance                                                                         |                                                                   | \-          |
+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+


**Example**
::

	dnRouter# clear nat sessions CUSTOMER_1
	Dynamic NAT sessions where deleted for NAT instance CUSTOMER_1


.. **Help line:** Clear active dynamic nat44 sessions per specific NAT instance

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 18.2        | Command introduced    |
+-------------+-----------------------+