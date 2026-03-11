show services ethernet-oam connectivity-fault-management maintenance-domains
----------------------------------------------------------------------------

**Minimum user role:** viewer

To display information for Connectivity Fault Management Maintenance Domains:


**Command syntax: show services ethernet-oam connectivity-fault-management maintenance-domains**

**Command mode:** operational

..
	**Internal Note**
	
	- MD column is the MD list entry key, and not the MD identifier (which could be null)

**Example**
::

	dnRouter# show services ethernet-oam connectivity-fault-management maintenanace-domains

	Connectivity Fault Management Ethernet OAM Maintenance Domains:

	+--------------------+-------------------------+-----------+----------+---------------+------------+------------+-------------+
	| Maintenance Domain | Maintenance Domain name | Type      | MD Level | Number of MAs | Local MEPs | Local MIPs | Remote MEPs |
	+====================+=========================+===========+==========+===============+============+============+=============+
	| MD1                | MyMD                    | string    | 7        | 1             | 1          | 0          | 10          |
	| MD2                | mymd.drivenets.com      | DNS       | 3        | 5             | 16         | 0          | 44          |
	+--------------------+-------------------------+-----------+----------+---------------+------------+------------+-------------+

	Total Manitenance Domains: 2
	Total Maintenance Associations: 6
	Total Local MEPs: 17
	Total Local MIPs: 0
	Total Remote MEPs: 54


.. **Help line:** Display CFM Maintenance Domains

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+