clear lfs counters
------------------

**Minimum user role:** operator

To clear the link fault signaling counters:

**Command syntax: clear lfs counters** [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - clear lfs counters** clears all LFS counters


**Parameter table:**

+-------------------+---------------------------------------------------------------+----------------------------------+-------------+
|                   |                                                               |                                  |             |
| Parameter         | Description                                                   | Range                            | Default     |
+===================+===============================================================+==================================+=============+
|                   |                                                               |                                  |             |
| interface-name    | Clears the LFS counters from the specified interface only.    | ge<interface speed>-<A>/<B>/<C>  | \-          |
+-------------------+---------------------------------------------------------------+----------------------------------+-------------+


**Example**
::

	dnRouter# clear lfs counters
	dnRouter# clear lfs counters ge400-2/0/3


.. **Help line:** Clear 100GE and 400GE and other physical interfaces link fault signaling statistics

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.2        | Command introduced    |
+-------------+-----------------------+