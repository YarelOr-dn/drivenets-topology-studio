interfaces icmp-ttl-exceed - N/A for this version
-------------------------------------------------

**Command syntax: icmp-ttl-exceed [admin-state]**

**Description:** Configure on egress interface the option to reply ICMP time-exceeded messages

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# ge100-1/0/1
	dnRouter(cfg-if-ge100-1/0/1)# icmp-ttl-exceed enabled

**Command mode:** config

**TACACS role:** operator

**Note:** By default, option is enabled

**Help line:** Configure on egress interface the option to reply ICMP time-exceeded messages

**Parameter table:**

+----------------+---------------------------------------+---------------+
| Parameter      | Values                                | Default value |
+================+=======================================+===============+
| Interface-name | ge<interface speed>-<A>/<B>/<C>       |               |
|                |                                       |               |
|                | geX-<f>/<n>/<p>.<sub-interface id>    |               |
|                |                                       |               |
|                | bundle-<bundle id>                    |               |
|                |                                       |               |
|                | bundle-<bundle id>.<sub-interface id> |               |
|                |                                       |               |
|                | mgmt0                                 |               |
+----------------+---------------------------------------+---------------+
| Admin-state    | enabled \| disabled                   | enabled       |
+----------------+---------------------------------------+---------------+
