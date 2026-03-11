request interface management description
-------------------------------------------------------------------

**Minimum user role:** operator


To set a textual interface description for the management physical interfaces:


**Command syntax: request interfaces management [interface-name] description [description]**

**Command mode:** GI

.. **Note:**


**Parameter table:**

+------------------+----------------------------------------------------------------------------------+---------------+---------+
| Parameter        | Values                                                                           | Range         | Default |
+==================+==================================================================================+===============+=========+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1, mgmt-ncc-0/0, mgmt-ncc-0/1, mgmt-ncc-1/0, mgmt-ncc-1/1   |               | \-      |
+------------------+----------------------------------------------------------------------------------+---------------+---------+


**Example:**
::

	dnRouter# request interfaces management mgmt-ncc-0 description MyInterfaceDescription


.. **Help line:** Set interface  description for management physical or management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
