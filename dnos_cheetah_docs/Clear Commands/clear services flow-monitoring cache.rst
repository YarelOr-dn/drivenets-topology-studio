clear services flow-monitoring cache		
------------------------------------

**Minimum user role:** operator

To clear the flow-monitoring cache:

**Command syntax: clear services flow-monitoring cache** ncp [ncp-id] export

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 -  "clear services flow-monitoring cache" without export parameter, flushes flow-cache tables on all NCPs and do not export the flushed flows.      

 -  "clear services flow-monitoring cache" with export parameter, flushes flow-cache tables on all NCPs and export the flushed flows.        
 
 -  "clear services flow-monitoring cache" without export parameter and with specific NCP-ID flushes flow-cache tables on that specific NCP and do not export the flushed flows of that NCP.     

 -  "clear services flow-monitoring cache" with export parameter and with specific NCP-ID flushes flow-cache tables on that specific NCP and export the flushed flows of that NCP.


**Parameter table:**

+-----------+-----------------------------------------------------------------------+--------+-------------+
| Parameter | Description                                                           | Range  |             |
|           |                                                                       |        | Default     |
+===========+=======================================================================+========+=============+
| ncp-id    | Clears the flow-monitoring cache counters from the specified NCP only | 0..255 | \-          |
+-----------+-----------------------------------------------------------------------+--------+-------------+
| export    | Exports the flushed flows                                             | \-     | \-          |
+-----------+-----------------------------------------------------------------------+--------+-------------+


**Example**		
::		

    dnRouter# clear services flow-monitoring cache ncp 5		
    dnRouter# clear services flow-monitoring cache ncp 2 export		

 
.. **Help line:** clear counters for exported flows by flow-monitoring.		

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.4        | Command introduced    |
+-------------+-----------------------+