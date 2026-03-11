clear napt session
----------------------

**Minimum user role:** operator

To clear active dynamic napt44 sessions per specific NAT instance

**Command syntax: clear napt session** [instance-name]

**Command mode:** operation

.. **Hierarchies**

**Parameter table:**

+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+
|               |                                                                                                                 |                                                                   |             |
| Parameter     | Description                                                                                                     | Range                                                             | Default     |
+===============+=================================================================================================================+===================================================================+=============+
|               |                                                                                                                 |                                                                   |             |
| instance-name | Enter name of the specific NAT instance                                                                         | Any configured nat instance	                                      | \-          |
+---------------+-----------------------------------------------------------------------------------------------------------------+-------------------------------------------------------------------+-------------+


**Example**
::

	dnRouter# clear napt sessions CUSTOMER_1
	Dynamic NAPT sessions where deleted for NAT instance CUSTOMER_1


.. **Help line:** Clear active dynamic napt44 sessions per specific NAT instance

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 18.2        | Command introduced    |
+-------------+-----------------------+