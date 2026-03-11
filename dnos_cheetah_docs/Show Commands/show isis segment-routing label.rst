show isis segment-routing label definition
----------------------------------------------

**Minimum user role:** viewer

To display a table with all the labels and the associated IP prefixes, for all algorithms.

**Command syntax: show isis** instance [isis-instance-name] **segment-routing label**

**Command mode:** operational

.. **Note**

	- use "instance [isis-instance-name]" to display information from a specific ISIS instance, when not specified, display information from all isis instances

**Parameter table**

+--------------------+--------------------------------------------------------------------------------------------------------------------------+
| Parameter          | Description                                                                                                              |
+====================+==========================================================================================================================+
| isis-instance-name | Filters the displayed information to the specified instance                                                              |
+--------------------+--------------------------------------------------------------------------------------------------------------------------+

**Example**
::

  e2e_R1_1# show isis segment-routing label
   Instance one
    Label   Prefix           Local
  ------------------------------------
   8000                     vdev_66
   8004                     vdev_66
   8001                     vdev_16
   8005                     vdev_16
   8002                     vdev_13
   8006                     vdev_13
   8003                     vdev_12
   8007                     vdev_12
   16001   1.1.1.1/32       lo0
   16201   1.1.1.1/32       lo0
   17301   1.1.1.1/32       lo0
   17401   1.1.1.1/32       lo0
   16002   2.2.2.2/32
   16202   2.2.2.2/32
   17302   2.2.2.2/32
   16003   3.3.3.3/32
   16203   3.3.3.3/32
   17403   3.3.3.3/32
   16004   4.4.4.4/32
   16204   4.4.4.4/32
   17304   4.4.4.4/32
   16111   1010::1010/128
   16311   1010::1010/128
   16111   1010::1010/128
   16311   1010::1010/128
   16011   1111::1111/128   lo0
   16211   1111::1111/128   lo0
   18301   1111::1111/128   lo0
   18401   1111::1111/128   lo0
   16012   2222::2222/128
   16212   2222::2222/128
   18302   2222::2222/128
   16013   3333::3333/128
   16213   3333::3333/128
   18403   3333::3333/128
   16014   4444::4444/128
   16214   4444::4444/128
   18304   4444::4444/128

.. **Help line:**

**Command History**

+---------+-----------------------------------------------------------+
| Release | Modification                                              |
+=========+===========================================================+
| 18.3    | Command introduced                                        |
+---------+-----------------------------------------------------------+