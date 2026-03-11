show interfaces control ip - N/A for this version
-------------------------------------------------

**Command syntax: show interfaces control ip** [interface-name]

**Description:** show interfaces ip

**CLI example:**
::

	dnRouter# show interfaces control ip
	NCM-A0 management address: 10.1.2.120
	NCM-B0 management address: 10.1.2.121
	NCM-A1 management address: 10.1.2.122
	NCM-B1 management address: 10.1.2.123
	
	
	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------+
	| ctrl-ncp-0/0    | enabled  | up          | 30.1.1.1/28    |                                | 
	| ctrl-ncp-0/1    | enabled  | up          | 30.1.1.2/28    |                                |
	| ctrl-ncp-1/0    | enabled  | up          | 30.1.1.3/28    |                                |
	| ctrl-ncp-1/1    | enabled  | up          | 30.1.1.4/28    |                                |
	
	
	dnRouter# show interfaces ip ctrl-ncp-0/0     
	
	| Interface       | Admin    | Operational | IPv4 Address   | IPv6 Address                   |
	+-----------------+----------+-------------+----------------+--------------------------------|
	| ctrl-ncp-0/0    | enabled  | up          | 30.1.1.1/28    |                                |
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:** When a user selects a specific interface, it will filter the output according to it

**Help line:** show interfaces ip

**Parameter table:**

+----------------+----------------------------+---------------+
| Parameter      | Values                     | Default value |
+================+============================+===============+
| interface_name | ctrl-ncp-X/Y               |               |
|                |                            |               |
|                | ctrl-ncf-X/Y               |               |
|                |                            |               |
|                | ctrl-ncc-X/Y               |               |
|                |                            |               |
|                | X - NCP/NCF/NCC id         |               |
|                |                            |               |
|                | Y - port id, values 0 or 1 |               |
|                |                            |               |
|                | Z - NCM port id            |               |
+----------------+----------------------------+---------------+
