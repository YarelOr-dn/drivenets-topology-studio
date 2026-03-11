show system management interfaces - deprecated
----------------------------------------------

**Command syntax: show system management interfaces** [host-name]

**Description:** show system management interfaces of mgmt0

**CLI example:**
::

	dnRouter# show system management interfaces
	
	| Id | Type              | Name          | Interface   | Operational   | IPv4 Address   | IPv6 Address        | MTU  |
	+----+-------------------+---------------+-------------+---------------+----------------+---------------------+------|
	| 0  | ncc               | vm-host-re-A  | ncc-mgmt-0/0| up            | 30.4.4.1/30    | 1006:abcd:12::2/128 | 1514 |
	| 1  | ncc               | vm-host-re-B  | ncc-mgmt-0/0| down          | 30.2.2.1/30    | 1001:abcd:12::2/128 | 1514 |
	| 0  | ncp               | vm-host-fe-1  | ncp-mgmt-0/0| up            | 30.3.3.1/30    | 1002:abcd:12::2/128 | 1514 |
	
	dnRouter# show system management interfaces vm-host-re-A
	
	| Id | Type              | Name          | Interface   | Operational   | IPv4 Address   | IPv6 Address        | MTU  |
	+----+-------------------+---------------+-------------+---------------+----------------+---------------------+------|
	| 0  | ncc               | vm-host-re-A  | ncc-mgmt-0/0| up            | 30.4.4.1/30    | 1006:abcd:12::2/128 | 1514 |
	
**Command mode:** operational

**TACACS role:** viewer

**Note:** device is always displayed with id and name (routing-engine: A (my-re-name) / forwarding-engine: 1 (my-fe-name-1)

**Help line:** show system backplane

**Parameter table:**

+--------------+----------------------+---------------+
| Parameter    | Values               | Default value |
+==============+======================+===============+
| Operational  | up/down              |               |
+--------------+----------------------+---------------+
| ipv4-address | A.B.C.D/x            |               |
+--------------+----------------------+---------------+
| ipv6-addres  | {ipv6-addres format} |               |
+--------------+----------------------+---------------+
| mtu          | 1514-9300            | 1514          |
+--------------+----------------------+---------------+
