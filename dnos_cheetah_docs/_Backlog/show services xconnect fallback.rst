show services xconnect fallback - N/A for this version
------------------------------------------------------

**Command syntax: show services xconnect fallback** service-id [xconnect-fallback-id]

**Description:** display configured xconnect fallback service

**CLI example:**
::

	dnRouter# show services xconnect fallback
	xConnect-fallback Id: 1
	Service Admin state: enabled 
	| Interface    | Admin       | Operational | Uptime             |
	+--------------+-------------+-------------|--------------------|
	| ge100-1/4/1  | enabled     | up          | 600 days, 21:43:56 |
	| ge100-1/4/2  | enabled     | up          | 600 days, 21:43:56 |
	 
	xConnect-fallback Id: 2
	Service Admin state: enabled
	| Interface    | Admin       | Operational | Uptime             |
	+--------------+-------------+-------------|--------------------|
	| ge100-2/2/1  | enabled     | down        | 0 days, 0:00:00    |
	| ge100-2/2/2  | enabled     | system-down | 0 days, 0:00:00    |
	
	xConnect-fallback Id: 3
	Service Admin state: disabled
	| Interface    | Admin       | Operational | Uptime             |
	+--------------+-------------+-------------|--------------------|
	| ge100-3/2/1  | enabled     | up          | 0 days, 0:05:00    |
	| ge100-3/2/2  | enabled     | up          | 0 days, 0:05:00    |
	
	xConnect-fallback Id: 4
	Service Admin state: enabled
	| Interface    | Admin       | Operational | Uptime             |
	+--------------+-------------+-------------|--------------------|
	| ge100-4/2/1  | disabled    | down        | 0 days, 0:00:00    |
	| ge100-4/2/2  | enabled     | system-down | 0 days, 0:00:00    |
	
	dnRouter# show services xconnect fallback service-id 2
	
	xConnect-fallback Id: 2
	Service Admin state: enabled
	| Interface    | Admin       | Operational | Uptime             |
	+--------------+-------------+-------------|--------------------|
	| ge100-2/2/1  | enabled     | down        | 0 days, 0:00:00    |
	| ge100-2/2/2  | enabled     | system-down | 0 days, 0:00:00    |
	
	
**Command mode:** operational

**TACACS role:** viewer

**Note:**

**Help line:** show xconnect service status

**Parameter table:**

+-----------------------+---------------------+---------------+
| Parameter             | Values              | Default value |
+=======================+=====================+===============+
| xconnect-fallback id  | 1-255               |               |
+-----------------------+---------------------+---------------+
| Service Admin state   | enabled/disabled    |               |
+-----------------------+---------------------+---------------+
| interfaces            | geX-<f>/<n>/<1>     |               |
|                       |                     |               |
|                       | geX-<f>/<n>/<2>     |               |
+-----------------------+---------------------+---------------+
| Interface Admin state | enabled/disabled    |               |
+-----------------------+---------------------+---------------+
| Operational           | up/down/system-down |               |
+-----------------------+---------------------+---------------+
| Uptime                | D days, HH:MM:SS    |               |
|                       |                     |               |
|                       | uint32 for days     |               |
+-----------------------+---------------------+---------------+
