Table sorting
-------------

-  In general, all tables in DNOS show commands shall be sorted per key values in ascending matter from low to high values

-  If not mentioned and specified otherwise, the key value should be the key in the data model (yang)

-  For a case with multiple keys (e.g. node name and node ID), the second key will be sorted after the first key and so on for multiple keys unless there is an explicit desired sorting that must be specified.

- Output effecive also on routing show commands

- The specifaction can have unique sorting for specific commands beyond the general guideline. i.e in "show system", the node name shall be sorted manually (NCC -> NCF -> NCP -> NCM) due to importance or any other product/system matter. In addition, the sorting may be different than the key in the data model (specified explicitly)

- Raw data which arranged in type of list which not presented in table, should also be ordered according the table sorting rules

Examples for syntax sorting:

* lexicographically: a -> z, A -> Z, 0 -> 1 (per ASCII definition)

* numbers:  0 -> 1

* ip addresses: 1.1.1.1 -> 1.1.1.2 -> 1.1.2.1

**CLI example:**
::

	dnRouter# show system

	...

	# Type customized first key
	# ID numbered second key

	| Type | Id | Admin    | Operational  | Model      | Uptime           | Description | Serial Number      |
	+------+----+----------+--------------+------------+------------------+-------------+--------------------+
	| NCC  | 0  |          | active-up    | X86        | 0 days, 22:50:07 | dn-ncc-0    | CZ293105J0         |
	| NCC  | 1  |          | standby-up   | X86        | 0 days, 2:10:24  | dn-ncc-1    | CZ293105HZ         |
	| NCF  | 0  | enabled  | up           | NCF-48CD   | 0 days, 22:40:57 | dn-ncf-0    | WEB1947D0003C      |
	| NCF  | 1  | enabled  | up           | NCF-48CD   | 0 days, 22:40:58 | dn-ncf-1    | WEB1947V00001      |
	| NCF  | 2  | enabled  | up           | NCF-48CD   | 0 days, 22:40:58 | dn-ncf-2    | WEB1947300032      |
	| NCF  | 3  | enabled  | up           | NCF-48CD   | 0 days, 22:42:06 | dn-ncf-3    | WEB19B7N00026-P2   |
	| NCF  | 4  | enabled  | up           | NCF-48CD   | 0 days, 22:42:29 | dn-ncf-4    | WEB1977Y0000F-P1   |
	| NCF  | 5  | enabled  | up           | NCF-48CD   | 0 days, 22:42:01 | dn-ncf-5    | WEB1977X0000E-P1   |
	| NCF  | 6  | enabled  | up           | NCF-48CD   | 0 days, 22:42:03 | dn-ncf-6    | WEB1977M00021-P1   |
	| NCF  | 7  | enabled  | up           | NCF-48CD   | 0 days, 22:41:39 | dn-ncf-7    | WEB1977M00013-P1   |
	| NCF  | 8  | enabled  | up           | NCF-48CD   | 0 days, 22:42:02 | dn-ncf-8    | WEB1977N00014-P1   |
	| NCF  | 9  | enabled  | up           | NCF-48CD   | 0 days, 22:41:59 | dn-ncf-9    | WEB1977W00029-P1   |
	| NCF  | 10 | enabled  | up           | NCF-48CD   | 0 days, 22:40:26 | dn-ncf-10   | WEB1947400017      |
	| NCF  | 11 | enabled  | up           | NCF-48CD   | 0 days, 22:42:30 | dn-ncf-11   | WEB1A17S00019-P3   |
	| NCF  | 12 | enabled  | up           | NCF-48CD   | 0 days, 22:40:25 | dn-ncf-12   | WEB1957400010      |
	| NCP  | 0  | enabled  | up           | NCP-10CD   | 0 days, 22:35:44 | dn-ncp-0    | WDV1977M00006-P1   |
	| NCP  | 1  | enabled  | up           | NCP-10CD   | 0 days, 22:35:48 | dn-ncp-1    | WDV1957D0000C      |
	| NCP  | 2  | enabled  | up           | NCP-40C    | 0 days, 22:35:35 | dn-ncp-2    | WDY1957800009      |
	| NCP  | 3  | enabled  | up           | NCP-40C    | 0 days, 22:35:32 | dn-ncp-3    | WDY1977X0001F-P1   |
	| NCP  | 4  | enabled  | up           | NCP-40C    | 0 days, 22:35:30 | dn-ncp-4    | WDY1977J00021-P1   |
	| NCP  | 5  | enabled  | up           | NCP-40C    | 0 days, 22:35:35 | dn-ncp-5    | WDY1977U0002A-P1   |
	| NCP  | 6  | enabled  | up           | NCP-40C    | 0 days, 22:35:39 | dn-ncp-6    | WDY1977W00056-P1   |
	| NCP  | 7  | enabled  | up           | NCP-40C    | 0 days, 22:35:35 | dn-ncp-7    | WDY1977X0003B-P1   |
	| NCP  | 8  | enabled  | up           | NCP-40C    | 0 days, 22:35:38 | dn-ncp-8    | WDY1957A0000B      |
	| NCP  | 9  | enabled  | up           | NCP-40C    | 0 days, 22:35:37 | dn-ncp-9    | WDY1977X0002D-P1   |
	| NCP  | 10 | enabled  | up           | NCP-40C    | 0 days, 22:35:34 | dn-ncp-10   | WDY1977X00057-P1   |
	| NCP  | 11 | enabled  | up           | NCP-40C    | 0 days, 22:35:31 | dn-ncp-11   | WDY1957900050      |
	| NCM  | A0 |          | up           | NCM-48X-6C | 0 days, 22:59:17 | dn-ncm-A0   | AAF1925AADI        |
	| NCM  | A1 |          | up           | NCM-48X-6C | 0 days, 22:59:14 | dn-ncm-A1   | AAF1951AAAN        |

	dnRouter# show system hardware

	...

	# Module Name lexicographically single key

	CPLD Version:

	| Module Name   | Image Version   |
	|---------------+-----------------|
	| CPU CPLD      | v0.29           |
	| MB CPLD1      | v0.62           |
	| MB CPLD2      | v0.12           |
	| MB CPLD3      | v0.12           |

	...

	# CPU lexicographically single key

	CPU Usage:

	| CPU   | Use %   |
	|-------+---------|
	| 0     | 22      |
	| 1     | 19      |
	| 2     | 22      |
	| 3     | 52      |
	| 4     | 55      |
	| 5     | 19      |
	| 6     | 22      |
	| 7     | 31      |
	| 8     | 21      |
	| 9     | 19      |
	| 10    | 16      |
	| 11    | 15      |
	| 12    | 11      |
	| 13    | 19      |
	| 14    | 18      |
	| 15    | 15      |