request interface management access-list
-------------------------------------------------------------------

**Minimum user role:** operator

To attach the management bond interface to the access-list: 


**Command syntax: request interfaces management [interface-name] access-list [access-list-type] [access-list-name] direction [direction]**

**Command mode:** operational

**Note:**

- Description rules aren't configured to the interface 
- After configuration on BaseOS each rule will get a unique ID that can be displayed in show


**Parameter table:**

+------------------+----------------------------------------------+-------+-------+
| Parameter        | Values                                       | Range | Value |
+==================+==============================================+=======+=======+
| interface-name   | mgmt-ncc-0, mgmt-ncc-1                       |       | \-    |
+------------------+----------------------------------------------+-------+-------+
| access-list-type | ipv4/ipv6                                    |       | \-    |
+------------------+----------------------------------------------+-------+-------+
| access-list-name | string                                       |       | \-    |
+------------------+----------------------------------------------+-------+-------+
| direction        | in                                           |       | \-    |
+------------------+----------------------------------------------+-------+-------+


**Example:**
::

	dnRouter# request interfaces management mgmt-ncc-0 access-list ipv4 example-acl direction in
	
	Upon attachment of example-acl to mgmt-ncc-0, those rules going to be configured:

	| Type        | Nexthop1   | Protocol   | Src Ports   | Src IP   | Dest Ports   | Dest IP   | Dscp   | Description        |
	+-------------+------------+------------+-------------+----------+--------------+-----------+--------+--------------------|
	| description |            |            |             |          |              |           |        | BGP_TCP_ONLY       |
	| allow       |            | tcp(0x06)  | any         | any      | 179          | any       |        |                    |
	| allow       |            | tcp(0x06)  | 179         | any      | any          | any       |        |                    |
	| description |            |            |             |          |              |           |        | LPD_TCP_AND_UDP    |
	| allow       |            | tcp(0x06)  | any         | any      | 646          | any       |        |                    |
	| allow       |            | tcp(0x06)  | 646         | any      | any          | any       |        |                    |
	| allow       |            | udp(0x11)  | any         | any      | 646          | any       |        |                    |
	| allow       |            | udp(0x11)  | 646         | any      | any          | any       |        |                    |

	Note: Any change to attached ACL policy example-acl won't affect current attachment

	Are you sure you want to proceed? (Yes/No) [No]? 
	

.. **Help line:** Clear static route on management bond interface


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 16.2        | Command introduced    |
+-------------+-----------------------+
