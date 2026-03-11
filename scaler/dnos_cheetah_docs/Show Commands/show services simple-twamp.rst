show services simple-twamp
--------------------------

**Minimum user role:** viewer

To display the Simple TWAMP configuration:

**Command syntax: show services simple-twamp**

**Command mode:** operational



..
	**Internal Note**

	- Simple TWAMP current global configuration for both client and reflector


**Example**
::

	dnRouter# show services simple-twamp

	Simple-TWAMP Reflector:
		Admin-state: enabled
		Mode: Stateless, Unauthenticated
		Reflector port (UDP): 862

		Statistics:
			Reflected Simple-TWAMP probes:     0


	Simple-TWAMP Client:
		Admin-state: enabled
		Mode: Stateless, Unauthenticated
		Destination port: 862
		Source ports range: 40000-50000


.. **Help line:** Displays Simple TWAMP global configuration

**Command History**

+---------+------------------------------------+
| Release | Modification                       |
+=========+====================================+
| 17.2    | Command introduced                 |
+---------+------------------------------------+
