commit and-exit
---------------

**Minimum user role:** operator

To commit the configuration and, if the configuration contains no errors and the commit succeeds, exit configuration mode:

**Command syntax: commit and-exit**

**Command mode:** operational

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interface bundle-1 mac-address 00:00:00:00:00:01
	dnRouter(cfg)# commit and-exit
	Commit succeeded by ADMIN at 27-Jan-2017 22:11:00 UTC
	dnRouter#

.. **Help line:** Commit the configuration and exit from configuration mode

**Command History**

+-------------+----------------------------------------------------------+
|             |                                                          |
| Release     | Modification                                             |
+=============+==========================================================+
|             |                                                          |
| 6.0         | Command introduced                                       |
+-------------+----------------------------------------------------------+
|             |                                                          |
| 11.0        | Command syntax: replaced "and-quit"   with "and-exit"    |
+-------------+----------------------------------------------------------+