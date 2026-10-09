-------------------------------- MODULE Aidlc --------------------------------
(* The AIDLC run between the CEO's three batch sign-offs (SKILL.md § Batches
   and interrupts). The run is autonomous between batches; what it may do on
   its own is bounded by sensors, and this model proves the bounds hold.

   What it abstracts: a stage is one step; the work inside it is the agents'.
   Items are the requirement IDs of TASKS.md. A "trouble" is anything a sensor
   raises (check_tasks, check_live, check_formal, the model check); the
   environment may cause one at any moment. A judgment is no trouble: the
   role decides it and records a Cn (JudgmentRecorded).

   Conformance: the orchestrator is a model, not a program, so there is no
   trace to validate. What ties this model to the protocol is that its
   Stages, Batches and Interrupts are the ones SKILL.md names
   (tools/check_repo.py compares them), and that TASKS.md is checked by
   check_tasks.py at every step the model calls Advance. *)
EXTENDS Naturals

CONSTANTS Items, MaxAttempts, MaxStalled,
          SkipDesignGate,  \* TRUE only in AidlcBroken.cfg: a seeded broken safety variant
          NoRaise          \* TRUE only in AidlcLiveBroken.cfg: a seeded broken liveness variant

Stages     == <<"intent", "market", "arch", "design", "build", "verify", "deploy", "release">>
Batches    == {"intent", "design", "ship"}
\* the stops a MACHINE raises. A judgment (an irreversible action not on the
\* pre-authorized list, a design question, a spent budget) is not a stop: the
\* role decides it, records a Cn checkbox for the CEO's next batch, and goes on.
Interrupts == {"drift", "cross-design", "loop-bound", "missing-service", "model-fail"}
Optional   == {"market", "arch", "design", "deploy", "release"}   \* scope routing may skip these

\* every batch that must be signed before a stage starts -- cumulative: a scope
\* that skips a batch's phases skips that batch, never the ones before it
Order == <<"intent", "design", "ship">>
Required(s) == CASE s \in {"arch", "design"}                  -> {"intent"}
                 [] s \in {"build", "verify", "deploy"}        -> {"intent", "design"}
                 [] s \in {"release", "done"}                  -> {"intent", "design", "ship"}
                 [] OTHER                                      -> {}

VARIABLES stage, run, waiting, signed, trouble, skip, preauth, review,
          item, live, formal, attempts, stalled
vars == <<stage, run, waiting, signed, trouble, skip, preauth, review,
          item, live, formal, attempts, stalled>>

Idx(s) == CHOOSE k \in 1..8 : Stages[k] = s
DesignSkipped == {"arch", "design"} \subseteq skip
Needed(b) == ~(b = "design" /\ DesignSkipped)
Signed(b) == signed[b] \/ ~Needed(b)
\* what Advance checks; the broken variant opens it for the design batch
Gate(b) == Signed(b) \/ (b = "design" /\ SkipDesignGate)
\* the first batch, in order, that stage s still waits on ("none" if none)
Missing(s) == LET m == {k \in 1..3 : Order[k] \in Required(s) /\ ~Gate(Order[k])}
              IN IF m = {} THEN "none" ELSE Order[CHOOSE k \in m : \A j \in m : k <= j]

\* the next stage after s that the scope does not skip
Next(s) == LET later == {k \in Idx(s)+1..8 : Stages[k] \notin skip}
           IN IF later = {} THEN "done" ELSE Stages[CHOOSE k \in later : \A j \in later : k <= j]

TypeOK ==
  /\ stage \in {Stages[k] : k \in 1..8} \cup {"done"}
  /\ run \in {"running", "batch", "interrupted", "finished"}
  /\ waiting \in Batches \cup Interrupts \cup {"none"}
  /\ signed \in [Batches -> BOOLEAN]
  /\ trouble \in Interrupts \cup {"none"}
  /\ item \in [Items -> {"todo", "doing", "done"}]
  /\ attempts \in 0..MaxAttempts /\ stalled \in 0..MaxStalled

Init ==
  /\ stage = "intent" /\ run = "running" /\ waiting = "none"
  /\ signed = [b \in Batches |-> FALSE]
  /\ trouble = "none"
  /\ skip \in SUBSET Optional          \* the scope, fixed at Phase 0
  /\ preauth \in BOOLEAN               \* is a production deploy pre-authorized?
  /\ review = FALSE                    \* a Cn checkbox recorded for the CEO
  /\ item = [i \in Items |-> "todo"]
  /\ live = [i \in Items |-> FALSE] /\ formal = [i \in Items |-> FALSE]
  /\ attempts = 0 /\ stalled = 0

Calm == run = "running" /\ trouble = "none"
Work == <<item, live, formal, attempts, stalled>>

\* ---- the agents (fair) -----------------------------------------------------
\* Leave the current stage. A batch boundary that is not signed stops the run.
Advance ==
  /\ Calm
  /\ stage \in {"build", "verify"} => \A i \in Items : item[i] = "done"
  /\ LET n == Next(stage) IN
       IF Missing(n) = "none"
       THEN /\ stage' = n
            /\ run' = IF n = "done" THEN "finished" ELSE "running"
            /\ UNCHANGED <<waiting, signed>>
       ELSE /\ run' = "batch" /\ waiting' = Missing(n)
            /\ UNCHANGED <<stage, signed>>
  /\ review' = (review \/ (stage = "deploy" /\ ~preauth))   \* decided, recorded as Cn
  /\ UNCHANGED <<trouble, skip, preauth>> /\ UNCHANGED Work

\* Loop A, inside build: an item starts, fails, or passes with its evidence.
Start(i) == /\ Calm /\ stage = "build" /\ item[i] = "todo"
            /\ \A j \in Items : item[j] # "doing"
            /\ item' = [item EXCEPT ![i] = "doing"]
            /\ attempts' = 0 /\ stalled' = 0
            /\ UNCHANGED <<live, formal, stage, run, waiting, signed, trouble, skip, preauth, review>>
Fail(i)  == /\ Calm /\ item[i] = "doing"
            /\ attempts < MaxAttempts /\ stalled < MaxStalled
            /\ attempts' = attempts + 1
            /\ stalled' \in {0, stalled + 1}        \* did the failure count drop?
            /\ UNCHANGED <<item, live, formal, stage, run, waiting, signed, trouble, skip, preauth, review>>
Under(i) == attempts < MaxAttempts /\ stalled < MaxStalled
Prove(i) == /\ Calm /\ item[i] = "doing" /\ Under(i)
            /\ live' = [live EXCEPT ![i] = TRUE] /\ formal' = [formal EXCEPT ![i] = TRUE]
            /\ UNCHANGED <<item, attempts, stalled, stage, run, waiting, signed, trouble, skip, preauth, review>>
Close(i) == /\ Calm /\ item[i] = "doing" /\ Under(i) /\ live[i] /\ formal[i]  \* check_tasks R3
            /\ item' = [item EXCEPT ![i] = "done"]
            /\ UNCHANGED <<live, formal, attempts, stalled, stage, run, waiting, signed, trouble, skip, preauth, review>>

\* The bound is reached: the run must stop, not try again.
Bound == /\ Calm /\ (attempts = MaxAttempts \/ stalled = MaxStalled)
         /\ trouble' = "loop-bound"
         /\ UNCHANGED <<stage, run, waiting, signed, skip, preauth, review>> /\ UNCHANGED Work
\* A sensor saw trouble: the run stops and the CEO is told which.
Raise == /\ ~NoRaise /\ run = "running" /\ trouble # "none"
         /\ run' = "interrupted" /\ waiting' = trouble
         /\ UNCHANGED <<stage, signed, trouble, skip, preauth, review>> /\ UNCHANGED Work

\* ---- the environment (not fair: it may or may not happen) -----------------
Trouble == /\ run = "running" /\ trouble = "none" /\ stage # "intent"
           /\ trouble' \in Interrupts \ {"loop-bound"}
           /\ UNCHANGED <<stage, run, waiting, signed, skip, preauth, review>> /\ UNCHANGED Work

\* ---- the CEO (not fair: the model proves the run reaches the CEO, not that
\*      the CEO answers) --------------------------------------------------------
Sign == /\ run = "batch"
        /\ signed' = [signed EXCEPT ![waiting] = TRUE]
        /\ run' = "running" /\ waiting' = "none"
        /\ UNCHANGED <<stage, trouble, skip, preauth, review>> /\ UNCHANGED Work
Resolve == /\ run = "interrupted"
           /\ run' = "running" /\ waiting' = "none" /\ trouble' = "none"
           \* drift is resolved by re-signing what drifted; loop-bound by a
           \* fresh budget
           /\ attempts' = IF waiting = "loop-bound" THEN 0 ELSE attempts
           /\ stalled' = IF waiting = "loop-bound" THEN 0 ELSE stalled
           /\ UNCHANGED <<stage, signed, skip, preauth, review, item, live, formal>>

Done == run = "finished" /\ UNCHANGED vars

Agent == Advance \/ Bound \/ Raise
         \/ \E i \in Items : Start(i) \/ Fail(i) \/ Prove(i) \/ Close(i)
NextStep == Agent \/ Trouble \/ Sign \/ Resolve \/ Done
Spec == Init /\ [][NextStep]_vars /\ WF_vars(Agent)

\* ---- the properties --------------------------------------------------------
\* (a) no stage starts past an unsigned batch -- any of the batches before it
NoPhasePastUnsignedBatch == \A b \in Required(stage) : Signed(b)

\* (c) an item is done only with live and formal evidence
DoneHasEvidence == \A i \in Items : item[i] = "done" => live[i] /\ formal[i]

\* (e, bound) at Loop A's bound nothing more is proved or closed: the only way
\* on is the interrupt, then a CEO decision
AtBoundNoProgress ==
  [][(attempts = MaxAttempts \/ stalled = MaxStalled) =>
       (item' = item /\ live' = live /\ formal' = formal)]_vars

\* the CEO is only ever asked for a batch or an interrupt, and an interrupt is
\* only ever one of R7's five
AsksOnlyForBatchOrInterrupt ==
  /\ run = "batch" => waiting \in Batches
  /\ run = "interrupted" => waiting \in Interrupts

\* (b) the run stops only at a batch or on an interrupt, and while a trouble is
\* open nothing advances
StopsOnlyForCEO ==
  [][ /\ (run = "running" /\ run' \notin {"running", "finished"}) =>
          (run' = "batch" \/ (run' = "interrupted" /\ waiting' = trouble))
      /\ (trouble # "none") => (stage' = stage /\ item' = item) ]_vars

\* (f) the run never deadlocks between batches: running leads to a batch, an
\* interrupt the CEO sees, or the end
NeverStuck == (run = "running") ~> (run \in {"batch", "interrupted", "finished"})

\* (e) Loop A terminates: an item in progress is closed or stops the run
LoopTerminates == \A i \in Items : (item[i] = "doing") ~> (item[i] = "done" \/ run = "interrupted")

\* a production deploy that was not pre-authorized never passes unrecorded:
\* the role decided it, and the CEO sees the Cn checkbox at the next batch
JudgmentRecorded ==
  ("deploy" \notin skip /\ ~preauth /\ stage \in {"release", "done"}) => review

\* reaching the bound stops the run
BoundInterrupts == (attempts = MaxAttempts \/ stalled = MaxStalled) ~> (run = "interrupted")

\* every trouble a sensor sees reaches the CEO
TroubleReachesCEO == (trouble # "none") ~> (run = "interrupted")
=============================================================================
