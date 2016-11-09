Plans of attack:

1. Master server gets request for who, then sshs into all machines in a list, calls who method, adds all of that to a dict that it spits out: {"borg05.cs.purdue.edu: ["1", ... "n"], "etc": {...}}, or defers to spawning slave processes that all ssh.

2. Daemonized version that just sits on all of the machines, or traverses each cluster (borg, sslab, etc) as a ring, then master server just needs to do an HTTP get on all of those, then format the return.
