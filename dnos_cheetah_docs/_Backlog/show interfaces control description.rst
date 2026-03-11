show interfaces control description - not supported
---------------------------------------------------

**Command syntax: show interfaces control description** [interface-name]

**Description:** show control interfaces description

**CLI example:**
::

	dnRouter# show interfaces control description
	
	| Interface       | Admin    | Operational | Description                         | 		
	+-----------------+----------+-------------+-------------------------------------+
	| ctrl-ncp-0/0    | enabled  | up  	  | My First control Interface          |
	| ctrl-ncp-0/1    | enabled  | up 	  | My Second control Interface         | 
	| ctrl-ncp-1/0    | enabled  | up   	  | My Third control Interface          |
	| ctrl-ncp-1/1    | enabled  | down 	  | My Best control Interface           |
	
	
	dnRouter# show interfaces description ctrl-ncp-0/0    
	
	| Interface       | Admin    | Operational | Description                         | 		
	+-----------------+----------+-------------+-------------------------------------+
	| ctrl-ncp-0/0    | enabled  | up          | My First control Interface          | 
	
**Command mode:** operational

**TACACS role:** viewer

**Note:** When a user selects a specific interface, it will filter the output according to it

**Help line:** show interfaces description

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
