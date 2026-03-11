**rsvp optimizationqueue-delay - supported in v11.1**
------------------------------------------------------

**Command syntax: queue-delay [delay]**

**Description:** Set a delay, in seconds, between optimization attempts of sequential tunnels in optimization queue.

In order to allow the network to stabilize after establishing a Tunnel LSP, it is recommended that next Tunnel optimization will be delayed in order for the IGP-TE to converge.

When set to 0, no delay is done

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# rsvp
	dnRouter(cfg-protocols-rsvp)# optimization 
	dnRouter(cfg-protocols-rsvp-optimization)# queue-delay 1
	 
	dnRouter(cfg-protocols-rsvp-optimization)# no queue-delay
	 
**Command mode:** config

**TACACS role:** operator

**Note:**

-  can configure queue-delay while optimization is undergoing, delay will take effect for the next tunnel being optimize.

-  no queue-delay - return delay to its default value

****

**Help line:**

**Parameter table:**

+-----------+--------+---------------+----------+
| Parameter | Values | default value | comments |
+===========+========+===============+==========+
| delay     | 0..59  | 3             | seconds  |
+-----------+--------+---------------+----------+
