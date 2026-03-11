protocols bgp maximum-sessions 
-------------------------------

**Command syntax: bgp maximum-sessions [maximum] threshold [threshold]**

**Description:** configure system maximum bgp session scale and threshold limit

maximum session scale applies for all bgp session types (iBGP, eBGP). Only establish sessions are counted.

sessions are accorss all bgp instances.

-  when threshold is crossed - a single system-event notification is generated

-  when threshold is cleared - a single system-event notification is generated

-  when maximum is crossed - a system-event notification is generated

-  when maximum is cleared - a single system-event notification is generated

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bgp maximum-sessions 600 threshold 70
	
	dnRouter(cfg-protocols)# no bgp maximum-sessions
			
**Command mode:** config

**TACACS role:** operator

**Note:**

-  this is a global bgp configuration not under a specifc bgp as-number

-  there is no limitation for how many bgp neighbors/groups user can configure. A session will open for every configured peer.

-  no command returns maximum & threshold to their default values

**Help line:**

**Parameter table:**

+-----------+----------+---------------+
| Parameter | Values   | Default value |
+===========+==========+===============+
| maximum   | 1..65535 | 500           |
+-----------+----------+---------------+
| threshold | 1..100   | 75            |
+-----------+----------+---------------+
