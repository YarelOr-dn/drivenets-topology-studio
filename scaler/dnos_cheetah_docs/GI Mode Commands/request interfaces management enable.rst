request interface management enable
-------------------------------------------------------------------

**Minimum user role:** operator


To enable the management physical or management bond interface:


**Command syntax: request interfaces management [interface-name] enable**

**Command mode:** GI

.. **Note:**


**Parameter table:**

+------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter        | Values                                                                           | Range | Default |
+==================+==================================================================================+=======+=========+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1, mgmt-ncc-0/0, mgmt-ncc-0/1, mgmt-ncc-1/0, mgmt-ncc-1/1   |       | \-      |
+------------------+----------------------------------------------------------------------------------+-------+---------+


**Example:**
::

	dnRouter# request interfaces management mgmt-ncc-0 enable


.. **Help line:** Disabling management physical or management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
