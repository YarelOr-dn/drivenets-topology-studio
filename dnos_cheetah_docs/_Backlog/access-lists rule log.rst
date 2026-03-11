access-lists rule log - supported in v12
----------------------------------------

**Command syntax: rule [rule-id] [rule-type]** log

**Description:** configure access-lists rule log action

Log action provides logging entries for IP datagram packets flowing via the access-lists rules.

A rule configured with log action will generate a log entry every log-interval on a dedicated log file.

The log entry details the relevant interface, access-lists details, captured IP packet 5 tuple header and the number of matched packets since the last log entry interval.

Configuration

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# access-lists 
	dnRouter(cfg-acl)# ipv4 MyAccess_list_1
	dnRouter(cfg-acl-ipv4)# rule 100 allow protocol icmp(0x01) ipv4-options log
	
	dnRouter(cfg-acl-ipv4)# no rule 100 allow log
	
**Command mode:** config

**TACACS role:** operator

**Note:**

Log file name called "acl.log". The file saved under log folder location as all other log files (only on RE). managing the log file can be as other log files under "system logging file" command

All log entries written with severity "info", default level for this log file is "info". All other log properties are the same as default values under "system logging file"

Log action available only when acl is active (mode enabled).

Each log entry contains the following:

Interface name, attachment direction, access-list name, access-list type, rule id, action (allow/deny), matched frame 5 tuple header, match counter (the number of frames since the last logging interval or clear command on the same rule and interface)

no commands remove the access-lists log action from the rule.

**Help line:** Configure access-lists rule log action

**Parameter table:**

+-----------+------------+---------------+
| Parameter | Values     | Default value |
+===========+============+===============+
| rule-id   | 1-65434    |               |
+-----------+------------+---------------+
| rule-type | allow/deny |               |
+-----------+------------+---------------+
