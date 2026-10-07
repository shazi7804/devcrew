---------------------------- MODULE ElectionTrace ----------------------------
(* Trace validation: is a run of the real boot.py a behaviour of Election?

   boot.py, run with DEVCREW_TRACE=<file>, logs every step that touches a claim
   -- in the order it happened, under an exclusive lock -- with what it saw.
   tools/check_models.py turns the log into the module TraceData (Trace, a
   sequence of records) and runs TLC on this spec.

   Each logged step must be the matching action of Election for that session,
   seeing exactly what was logged. The model keeps only the top generation;
   two ghost variables here keep its number (gen) and the number each session
   last read (sgen), so a scan must report the current number and a create
   must make exactly the next one. Between logged steps only the environment
   may move unseen: time (Age). Which hook a `beat` was (the start of a turn,
   a tool call, the end of a turn) is not logged, so any that fits is allowed.

   TLC reports the invariant Unmatched VIOLATED when the WHOLE trace is
   matched -- that is the pass. "No error" means no behaviour of the model
   explains the run: the code and the model have drifted apart. *)
EXTENDS Election, TraceData, Sequences

VARIABLES i, gen, sgen
tvars == <<vars, i, gen, sgen>>

Seen(t) == [sid |-> IF t.sid = "none" THEN None ELSE t.sid, age |-> t.age, rel |-> t.rel]

Logged ==
  /\ i <= Len(Trace)
  /\ LET e == Trace[i]
         s == e.s
     IN /\ CASE e.op = "fire" /\ e.mode = "start" -> Open(s)
             [] e.op = "fire" /\ e.mode = "beat"  -> Turn(s) \/ Mid(s) \/ Stop(s)
             [] e.op = "fire" /\ e.mode = "end"   -> Close(s)
             [] e.op = "scan"    -> top = Seen(e.top) /\ e.n = gen /\ Scan(s)
             [] e.op = "touch"   -> IF e.ok THEN Touch(s) ELSE TouchFail(s)
             [] e.op = "create"  -> e.n = sgen[s] + 1 /\ e.ok = valid[s] /\ Create(s)
             [] e.op = "verify"  -> e.ok = valid[s] /\ Verify(s)
             [] e.op = "release" -> IF e.ok THEN Release(s) ELSE ReleaseFail(s)
             [] OTHER            -> FALSE
        /\ sgen' = IF e.op = "scan" THEN [sgen EXCEPT ![s] = e.n] ELSE sgen
        /\ gen' = IF e.op = "create" /\ e.ok THEN e.n ELSE gen
  /\ i' = i + 1

TInit == Init /\ i = 1 /\ gen = 0 /\ sgen = [s \in Sessions |-> 0]
TNext == Logged \/ (Age /\ UNCHANGED <<i, gen, sgen>>)
TSpec == TInit /\ [][TNext]_tvars

Unmatched == i <= Len(Trace)
=============================================================================
