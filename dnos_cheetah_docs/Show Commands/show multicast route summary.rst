show multicast route summary
----------------------------

**Minimum user role:** viewer

You can use this command to display the multicast route table summary information.



**Command syntax: show multicast route summary**

**Command mode:** operational




**Example**
::

	dnRouter# show multicast route summary

  	Multicast Route Table Summary
    	Number of (*,G/n) internal routes : 9
    	Number of (*,G) routes : 3462
    	Number of (S,G) routes : 23454
    	Number of MoFRR protected routes : 0
    	Number of failed route installs : 0
    	Number of failed MoFRR standby interface installs : 0

.. **Help line:** Show Multicast route summary

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 12.0    | Command introduced        |
+---------+---------------------------+
| 19.1    | Added additional counters |
+---------+---------------------------+