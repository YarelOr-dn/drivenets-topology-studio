isis instance overload-bit
--------------------------

**Command syntax: overload-bit [period]** interval [interval] advertise-max-metric bgp-delay [bgp-delay]

**Description:** Set overload bit to avoid any transit traffic - signal other routers not to use it as an intermediate hop in their SPF calculations

period -

-  administrative - overload-bit is always on.

-  on-startup - Upon ISIS process start, overload-bit is on for an [interval] time period

-  wait-for-bgp - Upon ISIS process start, overload-bit is on until bgp covergence completed + [bgp_delay] or until [interval] time period, the first between the two events.

interval - interval timer to hold overload-bit on. timer starts when first isis interface is available for the isis instance

bgp-delay - additional delay time where overload-bit is still set after bgp covergence completed. In use only when period = wait-for-bgp.

advertise-max-metric - when set, the overload bit will not be set and dnRouter will advertise maximum metric value for all links (16777214), so it will be considered as least-preferable in path calculations (but can still be chosen). If interface is configured with maximum metric value - 16777215, the metric value will remain 16777215.

When ISIS Graceful-restart is enabled, upon restart the dnRouter will send its' LSP packet only after ISIS will converge. overload bit / max-metric will not be set if graceful-restart flow was used.

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protocols isis
	dnRouter(cfg-protocols-isis)# instance area_1
	dnRouter(cfg-protocols-isis-inst)# overload-bit administrative

	dnRouter(cfg-protocols-isis-inst)# overload-bit on-startup

	dnRouter(cfg-protocols-isis-inst)# overload-bit on-startup advertise-max-metric

	dnRouter(cfg-protocols-isis-inst)# no overload-bit on-startup
	dnRouter(cfg-protocols-isis-inst)# no overload-bit administrative
	dnRouter(cfg-protocols-isis-inst)# no overload-bit


**Command mode:** config

**TACACS role:** operator

**Note:**

-  overload-bit is disabled be default

-  when overload-bit is enabled, by default suppress also external routes (redistributed routes)

-  overload-bit is only relevent for cases ISIS has a clean start where no routes are installed in FIB. I.e, not relevent for cases of process restart

-  support only if metric-style is "wide"

-  interval - can only be set when **period** is "on-startup" or "wait-for-bgp"

-  'no overload-bit ' / 'no overload-bit [period]' - disable overload-bit

-  'no overload-bit [period] interval' - return interval to default value

-  'no overload-bit [period] interval advertise-max-metric' - return interval to default value and disable advertise-max-metric

**Help line:**

**Parameter table:**

+-----------+----------------------------+---------------+----------+
| Parameter | Values                     | Default value | comments |
+===========+============================+===============+==========+
| period    | administrative, on-startup,|               |          |
|           | wait-for-bgp               |               |          |
+-----------+----------------------------+---------------+----------+
| interval  | 5-86400                    | 600           | seconds  |
+-----------+----------------------------+---------------+----------+
| bgp-delay | 0-86400                    | 0             | seconds  |
+-----------+----------------------------+---------------+----------+
