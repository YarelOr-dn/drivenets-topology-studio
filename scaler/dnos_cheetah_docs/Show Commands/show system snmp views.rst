show system snmp views
----------------------

**Minimum user role:** viewer

The following command displays a list of the configured SNMP views, including the default view.

**Command syntax: show system snmp views**

**Command mode:** operational



**Example**
::

	dnRouter# show system snmp views
	
	View: viewdefault
	Include: iso.
	Exclude: snmp.1
	 snmp.2
	 1.2.3.4.5.7
	 1.1.6.3.1.2.5
	 internet.2
	
	View: viewall
	Include: iso.
		 snmp.3
		 snmp.4
	Exclude: snmp.1
	 snmp.2
	 1.2.3.4.5.7
	 1.1.6.3.1.2.5
	 internet.2
	
	View: MySnmpView
	Include: iso.1
	Exclude: 
				
	View: MySnmpView2
	Include: 	
	Exclude: 1.6.3.1.2.4.6
			 1.4.6.7.8.9
	
	

.. **Help line:** show system snmp views

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 5.1.0   | Command introduced |
+---------+--------------------+


