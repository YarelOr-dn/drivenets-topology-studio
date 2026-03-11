show rsvp refresh-reduction
---------------------------

**Minimum user role:** viewer

To display refresh message status:



**Command syntax: show rsvp refresh-reduction {send \| receive}**

**Command mode:** operational




**Example**
::

	dnRouter# show rsvp refresh-reduction send
	Interface                 MessageId   Message   Nexthop         Refresh[s]   ACK[s]  Type      Size[B]   LSP-local-id
	---------------------------------------------------------------------------------------------------------------------
	Bundle-1                  2           PATH      1.0.0.20        2                    SREFRESH  164       2
	Bundle-2                  4           PATH      1.0.0.20        1                    SREFRESH  164       100
	Bundle-3                  6           PATH      1.0.0.20        3                    SREFRESH  164       3
	
	dnRouter# show rsvp refresh-reduction receive
	Interface                 MessageId   Message   Nexthop         Refresh[s]   ACK[s]  Type      Size[B]   LSP-local-id
	---------------------------------------------------------------------------------------------------------------------
	Bundle-1                  2           PATH      1.0.0.20        2                    SREFRESH  164       2
	Bundle-2                  4           PATH      1.0.0.20        1                    SREFRESH  164       100
	Bundle-3                  6           PATH      1.0.0.20        3                    SREFRESH  164       3
	


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+


