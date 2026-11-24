# A generated copy of the files for each host

**The idea.** Keep one source and generate a tree of files per host.

**Why not.** The hosts now read each other's folders, so copies collide and show every skill more than once. A generator also has to be kept correct for every host's format. Version 2 ships one set of files that every host reads.

**What would reopen it.** A supported host that needs a different file for the same skill, where an adapter (ADR 0004) cannot cover it.
