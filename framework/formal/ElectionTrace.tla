---------------------------- MODULE ElectionTrace ----------------------------
(* Trace validation: is a run of the real boot.py a behaviour of Election?

   boot.py, run with DEVCREW_TRACE=<file>, logs every step that touches a claim
   -- in the order it happened, under an exclusive lock -- with what it saw.
   tools/check_models.py turns the log into the module TraceData (Trace, a
   sequence of records) and runs TLC on this spec.

   Each logged step must be the matching action of Election for that session,
   seeing exactly what was logged. Between logged steps only the environment
   may move unseen: time (Age). Which hook a `beat` was (the start of a turn,
   a tool call, the end of a turn) is not logged, so any that fits is allowed.

   TLC reports the invariant Unmatched VIOLATED when the WHOLE trace is
   matched -- that is the pass. "No error" means no behaviour of the model
   explains the run: the code and the model have drifted apart. *)
EXTENDS Election, TraceData, Sequences

VARIABLE i
tvars == <<vars, i>>

Seen(t) == [sid |-> IF t.sid = "none" THEN None ELSE t.sid, age |-> t.age, rel |-> t.rel]

Logged ==
  /\ i <= Len(Trace)
  /\ LET e == Trace[i]
         s == e.s
     IN CASE e.op = "fire" /\ e.mode = "start" -> Open(s)
          [] e.op = "fire" /\ e.mode = "beat"  -> Turn(s) \/ Mid(s) \/ Stop(s)
          [] e.op = "fire" /\ e.mode = "end"   -> Close(s)
          [] e.op = "scan"    -> top = Seen(e.top) /\ Scan(s)
          [] e.op = "touch"   -> Touch(s)
          [] e.op = "create"  -> e.ok = valid[s] /\ Create(s)
          [] e.op = "verify"  -> e.ok = valid[s] /\ Verify(s)
          [] e.op = "release" -> Release(s)
          [] OTHER            -> FALSE
  /\ i' = i + 1

TInit == Init /\ i = 1
TNext == Logged \/ (Age /\ UNCHANGED i)
TSpec == TInit /\ [][TNext]_tvars

Unmatched == i <= Len(Trace)
=============================================================================
