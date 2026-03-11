show system nsr - supported in v11.1
------------------------------------

**Command syntax: show system nsr**

**Description:** show stanby NCC Redis DB synchronization state

**CLI example (for cluster mode):**
::

	dnRouter# show system nsr
	NSR Synch State: NSR-Not-Ready
	
	dnRouter# show system nsr
	NSR Synch State: NSR-Ready
	
	dnRouter# show system nsr
	NSR Synch State: Synching
	
	CLI example (for standalone mode): 
	dnRouter# show system nsr
	NSR Synch State: Stand alone  N/A
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:** show system Non Stop Routing synchronization state. Syncchronisation between the the Active NCC router engine (RE) REDIS DB and the Standby NCC RE REDIS database is precondition to NSR

**Parameter table:**

+-----------------+----------------------------------------------+--------------------------------------------+
| Parameter       | Values                                       | Default value                              |
+=================+==============================================+============================================+
| NSR Synch State | **NSR-Not-Ready \| NSR-Ready \| Syncing**    | N/A should reflect the current real state. |
|                 |                                              |                                            |
|                 | In case of stand alone the output should be: |                                            |
|                 |                                              |                                            |
|                 | **Stand alone - N/A**                        |                                            |
+-----------------+----------------------------------------------+--------------------------------------------+
