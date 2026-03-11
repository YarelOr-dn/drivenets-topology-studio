show interfaces dampening
-------------------------

**Minimum user role:** viewer

To display detailed dampening information for an interface:

**Command syntax: show interfaces dampening [interface-name]**

**Command mode:** operational

**Note**

- This command is applicable to the following interfaces:

	- Physical

	- Bundle

- "Interface oper state uptime" refers to the time since this interface dampening passed oper state upwards to the higher layers.  Alternatively, if interface dampening is disabled,
  uptime is the time since the lower layers (e.g. Carrier Delay, LFS) changed the interface's oper-state to "up".

- The interface dampening admin-state is independent of the interface admin-state.

- An interface oper state down change casued by admin state down results in a penalty when interface dampeninig admins-state is enabled.

**Parameter table**

+----------------+----------------------------------------------------------------------+---------------------------------+
| Parameter      | Description                                                          | Range                           |
+================+======================================================================+=================================+
| interface-name | The name of the interface for which to display dampening information | ge<interface speed>-<A>/<B>/<C> |
+----------------+----------------------------------------------------------------------+---------------------------------+

**Example**
::

	dnRouter# show interfaces dampening ge100-1/0/1

	Interface ge100-1/0/1 Dampening:
	  Interface oper state: Up, Uptime: 0 days, 00:01:30
	  Dampening Admin State: Enabled
	  Dampening Config:
	       Half-life: 60 sec, reuse-threshold: 750, suppress-threshold: 2000,
	       Penalty step: 1000, max-suppress: 300 sec.
	  Dampening State:
	       Current penalty counter: 1500, Calculated time to reuse: 13 sec,
	       Next half-life expiration: 11 sec,
	       Interface state changes due to dampening event: 58
	  Interface-Dampening Event counters:
	       Suppress state changed due to max-suppress timer expiration.         : 12
	       Suppress state changed due to penalty exceeding suppress threshold.  : 23
	       Suppress state changed due to penalty decay below reuse threshold.   : 23
	       Suppress state changed due to manual clear penalty.                  :  0

.. **Help line:** Show interface dampening status

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
