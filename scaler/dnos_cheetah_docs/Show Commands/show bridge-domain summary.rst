show bridge-domain summary
--------------------------

**Minimum user role:** viewer

Display the Bridge-Domain service status for all Bridge-Domain instances.

**Command syntax: show bridge-domain summary**

**Command mode:** operational


**Example**
::

    show bridge-domain summary

 Global Bridge-Domain parameters
    mac-learning: enabled
    mac-table-limit: 100000 entries
    mac-table-aging-time: 320 seconds

 Number of Bridge-Domain Instances: 5
 Total learned MAC Addresses: 707
 Total Number of Interfaces/Up: 163/127

 Name   | Interfaces/Up |  Number of MACs |
 -------+---------------+-----------------+
 bd1    |    5  /  5    |       231       |
 bd2    |    50 / 40    |        50       |
 bd3    |    22 / 12    |        22       |
 bd4    |    76 / 60    |        76       |
 bd5    |    10 / 10    |        10       |


.. **Help line:** show bridge-domain summary

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
