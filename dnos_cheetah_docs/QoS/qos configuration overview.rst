QoS configuration overview
--------------------------

**Forwarding Classes and Queues**

Queue actions create queues for the forwarding class. There are five forwarding classes:

-	Super Expedite Forwarding (super-ef)
-	Expedite Forwarding (ef)
-	High-Priority (hp)
-	Assured Forwarding (af)
-	Default Forwarding (df) - best effort

You can create a single queue per forwarding class, and up to 6 queues for the Assured Forwarding class (and altogether up to eight queues per policy).

The queue inherits its properties from the forwarding class to which it belongs. The queue properties are:

-	Scheduling priority - strict priority according to traffic class level on the egress interfaces. While a higher forwarding class is still transmitting, all other forwarding classes are starved. If multiple af queues are created, the priority between them is according to a smart round-robin based on weight. 
-	Queue size - specifies the number of packets that a queue can hold for each forwarding class. Depending on the specified rules, packets satisfying the match criteria for a class accumulate in the queue reserved for the class until they are sent (according to strict priority). When the maximum packet threshold you defined for the class is reached, packets are dropped. The queue size is configured globally. See " qos policy rule action queue size".

	In the event of buffer scarcity, the fair adaptive drop threshold (FADT) ensures that the buffer resources are shared fairly between the queues.

-	Bandwidth - specifies the portion of the bandwidth that the queue is allowed to use. For priority queues (ef, hp, and sef), the max-bandwidth parameter is configured to prevent starvation of the lower priority queues. For af and df queues, the bandwidth parameter determines the ratio of the shared bandwidth that each queue can use. See "qos policy rule action queue bandwidth" on page 3383.

Super-ef and ef queues can be configured with max-bandwidth to avoid starvation of lower priority queues. It is recommended to set a maximum bandwidth limit for these forwarding classes because otherwise they can use 100% of the port bandwidth.

You can limit the bandwidth on af queues to set their relative bandwidth in the forwarding-class. If you do not set a bandwidth limit, the queue will get an equal quota of the remaining bandwidth on the af forwarding-class in the policy. The remaining bandwidth is calculated as follows:

(100 - sum of bandwidth in af queues) / number of af queues

To calculate the total bandwidth for the af forwarding class:
aggregate rate (shape rate or physical rate) - sum of max-bandwidth configured on the higher priority forwarding-classes.

**Example:**  Consider the following policy with 6 rules and a default rule:
::

	qos policy MyChildPolicy1_out
	 rule 1
	  match traffic-class myTrafficMap1
	  actions
	   queue super-ef max-bandwidth 10 percent
	 rule 2
	  match traffic-class myTrafficMap2
	  actions
	   queue ef max-bandwidth 15 percent
	 rule 3
	  match traffic-class myTrafficMap3
	  actions
	   queue hp max-bandwidth 25 percent
	 rule 4
	  match traffic-class myTrafficMap4
	  actions
	   queue af bandwidth 40 percent
	 rule 5
	  match traffic-class myTrafficMap5
	  actions
	   queue af bandwidth 20 percent
	 rule 6
	  match traffic-class myTrafficMap6
	  actions
	   queue af bandwidth 10 percent
	 rule-default
	  actions
	   queue df bandwidth 5 percent

**Calculating the bandwidth for the af forwarding class**

The guaranteed bandwidth of the af forwarding class is calculated as follows:
100 - (20 + 30) = 50%
So if the physical rate of the interface is 100 Mbps (assuming no shaping), then the af forwarding class will be guaranteed 42.5 Mbps. This rate is divided to 4 queues, according to rules 3-6:
af queue 3 (rule 3) - is guaranteed 25% of 50 Mbps (i.e. 7.5 Mbps)
af queue 4 (rule 4) - is guaranteed 40% of 50 Mbps (i.e. 20 Mbps)
af queue 5 (rule 5) - is guaranteed 20% of 50 Mbps (i.e. 10 Mbps)
af queue 6 (rule 6) - is guaranteed 10% of 50 Mbps (i.e. 5 Mpbs)

**Egress QoS Mechanisms**

-	**Scheduler** - implements strict priority according to traffic class level on the egress interfaces. The forwarding classes are:
	o	Super Expedite Forwarding (super-ef)
	o	Expedite Forwarding (ef)
	o	High-Priority (hp)
	o	Assured Forwarding (af)
	o	Default Forwarding (df) - best effort
	
	While a higher forwarding class is still transmitting, all other forwarding classes are starved. 

	For each forwarding class except "af", only one queue can be opened. For "af", up to four queues can be opened. If multiple queues are opened for "af", the priority is according to a smart round-robin based on weight.

	You can control the size of each queue by configuring tail-drop thresholds. See " qos policy rule action queue size".

-	**Shaper** - excess traffic is delayed in a buffer so that traffic can be sent at a constant rate. A shaping action is typically configured on egress interfaces.

To configure a QoS policy:

#. Enter the QoS configuration hierarchy.
#. Define a traffic-class map.
#. Create a rule in the QoS policy.
#. Define match criteria and actions for each rule.
#. Attach the policy to interfaces.

..
	A qos policy is a set of rules. A rule is a policy comprising a traffic-class to match and list of actions to perform if the traffic matches the pattern defined in the traffic-class.

	Rules in a policy define the order of execution. Every rule is identified by a number and the rules are executed in ascending order.

	The following is the general structure of a policy:

	Qos policy <policy-name>

	rule 1

	description "rule description"

	match traffic-class <traffic-class-map>

	actions

	<action-1>

	<action-2>

	rule 2

	. . .

	rule-default

	action

	<action-1>

	<action-2>

	**rule-default**

	A default rule is implicitly created for each policy. Traffic that doesn't match any of the preceding rules will match the default rule.


	**Traffic-class map**

	The traffic-class-map defines a traffic class by specifying the packet field to match against and a set of values. By default, a traffic-class match is defined as "match-any", i.e., traffic will hit the rule if any of the match fields is met.

	.. If "match-all" is configured for the traffic-class-map, then all conditions must be met (currently not supported).

	Qos traffic-map traffiClassMap1 match-any

	Dscp 24, 26

	Qos traffic-map traffiClassMap2 match-any

	Mpls exp 7

	Precedence 7

	The following match fields are supported

	+------------------+-------------+------------+
	| **Match field**  | **Ingress** | **Egress** |
	+------------------+-------------+------------+
	| Dscp             | +           |            |
	+------------------+-------------+------------+
	| Precedence       | +           |            |
	+------------------+-------------+------------+
	| Mpls exp topmost | +           |            |
	+------------------+-------------+------------+
	| qos-tag          |             | +          |
	+------------------+-------------+------------+

	Dscp and precedence fields are relevant for ipv4 or ipv6.

	Examples:

	Qos traffic-map match-any traffiClassMap1

	Dscp 24, 26

	Qos traffic-map match-any traffiClassMap2

	Mpls exp 7

	Precedence 7

	**Qos actions**

	The following are the QoS actions that are supported in the QoS policy:

	+-------------------------+-------------+------------+
	| **Action \  interface** | **Ingress** | **Egress** |
	+-------------------------+-------------+------------+
	| Set qos-tag             | +           |            |
	+-------------------------+-------------+------------+
	| Set drop-tag            | +           |            |
	+-------------------------+-------------+------------+
	| Set pcp                 |             | +          |
	+-------------------------+-------------+------------+
	| Queue                   |             | +          |
	+-------------------------+-------------+------------+

	**Egress scheduling**

	The aggregate rate of a policy is the shape rate configured on the parent policy or the physical rate of the port (if shape is not configured).

	The rates and guaranteed bandwidth of the queues are relative to the aggregate bandwidth.

	The scheduler has 5 forwarding classes: super-expedited-forwarding (super-ef), expedited-forwarding (ef), high-priority (hp), up to 6 assured-forwarding (af) classes and default-forwarding (df). super-ef has the highest priority. ef is assigned with the second highest priority. hp is assigned with the third highest priority. af and df forwarding classes share the same priority, each receiving a share of the avaialble bandwidth proportional to their configured bandwidth. As long as there is traffic on a queue matching a forwarding class, and the queue hasn't reached its max-bandwidth, the scheduler will not serve queues in lower priority forwarding classes.

	A policy on interface can have up to 8 queues, consisting of the following:

	-  up to 1 super-ef queue

	-  up to 1 ef queue

	-  up to 1 hp queue

	-  up to 6 af queue

	-  up to 1 df queue

	A queue inherits its properties from the forwarding-class to which it belongs.


	*Super-ef*, *ef* and *hp* queues configured with max-bandwidth to avoid starvation of lower priory queues.

	The *bandwidth* command on af or df queue sets its relative bandwidth in the forwarding-class

	for example:

	qos policy MyChildPolicy1_out

	rule 1

	match traffic-class myTrafficMap1

	actions

	queue super-ef max-bandwidth 10 percent

	rule 2

	match traffic-class myTrafficMap2

	actions

	queue ef max-bandwidth 15 percent

	rule 3

	match traffic-class myTrafficMap3

	actions

	queue hp max-bandwidth 25 percent

	rule 4

	match traffic-class myTrafficMap4

	actions

	queue af bandwidth 40 percent

	rule 5

	match traffic-class myTrafficMap6

	actions

	queue af bandwidth 20 percent

	rule 6

	match traffic-class myTrafficMap6

	actions

	queue af bandwidth 10 percent

	rule default

	actions

	queue df bandwidth 5 percent


	To determine the guaranteed bandwidth on the af and df queues:

	The guaranteed bandwidth of the af forwarding class is calculated as the aggregate rate (shape rate or physical rate) minus the max-bandwidth configured on higher priority forwarding-classes.

	In the example above:

	The sum of all bandwidth commands is 75 percent (40 + 20 + 10 +5)

	The guaranteed bandwidth for all the af and df classes is 50% of the link bandwidth (100 - 10 (max-bandwidth of super-ef) - 15 (max bandwidth of ef ) - 25 (max bandwidth of hp ))

	The guaranteed bandwidth of a specific af (or for df) is the relative rate for that class.

	For example, the guaranteed bandwidth for af with bandwidth 40% on a 100Gbps link is 26.66 Gpbs ((40% / 75%) * 50% of 100Gpbs)

	**Queue size**

	The queue size is specified in milliseconds or microseconds and determines the trail drop threshold of the queue.

	**Wred**

	WRED profiles are configured globally per af traffic forwarding class.

	i.e. each af forwarding classes can have up to  **2 curves**.

	The matching of traffic to wred-profile is done by the drop tag:

	Traffic marked with drop-tag green will be subject to drop profile of curve-green (DP = 0, Green color), traffic marked with drop-tag yellow will be subject to drop profile of curve-yellow (DP = 1, Yellow color).

	Marking of drop-tag is done in ingress policies. This drop-tag is used to select the wred profile in the queue.

	Default values:

	All curves are set to "no random drops". (i.e. min and max are set to queue-max-size)

	example for global wred config

	qos

	wred-profile

	my_af1_profile

	af curve-green min 20 max 100

	af curve-yellow min 1 max 100

	!

	my_af2_profile

	af curve-green min 40 max 100

	af curve-yellow min 10 max 100

	!

	!

	**Locally generated packets**

	Each protocol management is responsible to configure its priority hence to determine where it will be queued according to QoS policy.
