------------------------------- MODULE Election -------------------------------
(* The orchestrator election as boot.py implements it (0.9.7 on). One atomic
   file-system step per action, so a trace of the real script can be checked
   against it step by step (ElectionTrace.tla).

   THE FILES
     <state>/claims/ORCHESTRATOR.<n>.claim     generation n, O_EXCL-created
     <state>/claims/ORCHESTRATOR.<n>.released  marker: generation n released
   The highest n is the claim. A name is never reused, so "create n+1" is a
   compare-and-swap: it succeeds only if nobody created n+1 since we read n.
   Only the highest generation matters, so the model keeps just that one
   (`top`) plus, per session, whether its last read is still the highest
   (`valid`): a successful create anywhere makes every other read invalid.

   THE AGES of the top claim's mtime:
     fresh   age <= STALE - MARGIN    the holder may simply refresh it
     margin  age <= STALE             the holder must win n+1 to keep it
     stale   age >  STALE             anyone starting may take n+1

   THE ASSUMPTIONS (constants of the model; see session-governance.md)
     A1  a hook process pauses for less than MARGIN between two of its steps
     A2  an acting orchestrator beats (a hook fires) more often than
         STALE - MARGIN -- one beat per tool call, so no single tool call
         runs longer than that
     A3  a session told it is a worker stops acting as orchestrator
     A4  the claim directory is on a local file system (O_EXCL is atomic) *)
EXTENDS Naturals, FiniteSets, TLC

CONSTANTS Sessions, None,
          TakeOnBeat   \* FALSE only in ElectionLiveBroken.cfg: 0.9.6's "only a start
                       \* may take a claim" -- the seeded broken liveness variant

Ages  == {"fresh", "margin", "stale"}
NoTop == [sid |-> None, age |-> "stale", rel |-> TRUE]

VARIABLES top, snap, valid, pc, hook, role, acting, life
vars == <<top, snap, valid, pc, hook, role, acting, life>>

Absent(t)   == t.sid = None \/ t.rel
Mine(t, s)  == t.sid = s /\ ~t.rel

TypeOK ==
  /\ top \in [sid : Sessions \cup {None}, age : Ages, rel : BOOLEAN]
  /\ pc \in [Sessions -> {"none", "scan", "touch", "create", "verify", "release"}]
  /\ hook \in [Sessions -> {"none", "start", "pre", "mid", "post", "end"}]
  /\ role \in [Sessions -> {"none", "orch", "worker"}]
  /\ acting \in [Sessions -> BOOLEAN]
  /\ life \in [Sessions -> {"off", "idle", "turn", "gone"}]

Init ==
  /\ top = NoTop
  /\ snap = [s \in Sessions |-> NoTop]
  /\ valid = [s \in Sessions |-> FALSE]
  /\ pc = [s \in Sessions |-> "none"]
  /\ hook = [s \in Sessions |-> "none"]
  /\ role = [s \in Sessions |-> "none"]
  /\ acting = [s \in Sessions |-> FALSE]
  /\ life = [s \in Sessions |-> "off"]

\* A hook run ends: the session is told its role. A turn acts as orchestrator
\* from a "pre" beat that says orch until a beat says otherwise (A3).
Finish(s, r) ==
  /\ role' = [role EXCEPT ![s] = r]
  /\ acting' = [acting EXCEPT ![s] =
       \/ hook[s] = "pre" /\ r = "orch"
       \/ hook[s] = "mid" /\ acting[s] /\ r = "orch"]
  /\ hook' = [hook EXCEPT ![s] = "none"]
  /\ pc' = [pc EXCEPT ![s] = "none"]

Go(s, p) == /\ pc' = [pc EXCEPT ![s] = p]
            /\ UNCHANGED <<hook, role, acting>>

Fire(s, h) == /\ hook' = [hook EXCEPT ![s] = h]
              /\ pc' = [pc EXCEPT ![s] = "scan"]

\* ---- the host's lifecycle events -------------------------------------------
Open(s)  == /\ life[s] = "off" /\ life' = [life EXCEPT ![s] = "idle"]
            /\ Fire(s, "start") /\ UNCHANGED <<top, snap, valid, role, acting>>
Turn(s)  == /\ life[s] = "idle" /\ hook[s] = "none"
            /\ life' = [life EXCEPT ![s] = "turn"]
            /\ Fire(s, "pre") /\ UNCHANGED <<top, snap, valid, role, acting>>
Mid(s)   == /\ life[s] = "turn" /\ hook[s] = "none"
            /\ Fire(s, "mid") /\ UNCHANGED <<top, snap, valid, role, acting, life>>
Stop(s)  == /\ life[s] = "turn" /\ hook[s] = "none"
            /\ life' = [life EXCEPT ![s] = "idle"]
            /\ acting' = [acting EXCEPT ![s] = FALSE]
            /\ Fire(s, "post") /\ UNCHANGED <<top, snap, valid, role>>
\* The session closes; its end hook still runs, to release the claim.
Close(s) == /\ life[s] = "idle" /\ hook[s] = "none"
            /\ life' = [life EXCEPT ![s] = "gone"]
            /\ Fire(s, "end") /\ UNCHANGED <<top, snap, valid, role, acting>>
\* A session can die between hooks without its end hook (a killed process).
Crash(s) == /\ life[s] \in {"idle", "turn"} /\ hook[s] = "none"
            /\ life' = [life EXCEPT ![s] = "gone"]
            /\ acting' = [acting EXCEPT ![s] = FALSE]
            /\ UNCHANGED <<top, snap, valid, pc, hook, role>>

\* ---- boot.py, one atomic file-system step per action -----------------------
\* scan: list the claims, read the highest, stat its mtime
Scan(s) ==
  /\ pc[s] = "scan"
  /\ snap' = [snap EXCEPT ![s] = top]
  /\ valid' = [valid EXCEPT ![s] = TRUE]
  /\ IF hook[s] = "end" THEN
       IF Mine(top, s) THEN Go(s, "release") ELSE Finish(s, role[s])
     ELSE IF Mine(top, s) THEN
       Go(s, IF top.age = "fresh" THEN "touch" ELSE "create")
     ELSE IF (Absent(top) \/ top.age = "stale") /\ (hook[s] = "start" \/ TakeOnBeat) THEN
       Go(s, "create")             \* any beat may take a claim nobody holds
     ELSE Finish(s, "worker")
  /\ UNCHANGED <<top, life>>

\* os.utime(ORCHESTRATOR.<n>.claim) -- the file that was read, by its name.
\* If it fails the lease was not refreshed, so the session gives the role up.
Touch(s) ==
  /\ pc[s] = "touch"
  /\ top' = IF valid[s] THEN [top EXCEPT !.age = "fresh"] ELSE top
  /\ Go(s, "verify")
  /\ UNCHANGED <<snap, valid, life>>
TouchFail(s) ==
  /\ pc[s] = "touch"
  /\ Finish(s, "worker")
  /\ UNCHANGED <<top, snap, valid, life>>

\* os.open(ORCHESTRATOR.<n+1>.claim, O_CREAT | O_EXCL)
Create(s) ==
  /\ pc[s] = "create"
  /\ IF valid[s]
       THEN /\ top' = [sid |-> s, age |-> "fresh", rel |-> FALSE]
            /\ valid' = [t \in Sessions |-> t = s]
            /\ Go(s, "verify")
       ELSE /\ Finish(s, "worker")
            /\ UNCHANGED <<top, valid>>
  /\ UNCHANGED <<snap, life>>

\* list the claims again: is the generation I touched or made still the top?
Verify(s) ==
  /\ pc[s] = "verify"
  /\ Finish(s, IF valid[s] THEN "orch" ELSE "worker")
  /\ UNCHANGED <<top, snap, valid, life>>

\* create ORCHESTRATOR.<n>.released -- marks the generation that was read
Release(s) ==
  /\ pc[s] = "release"
  /\ top' = IF valid[s] THEN [top EXCEPT !.rel = TRUE] ELSE top
  /\ Finish(s, "worker")
  /\ UNCHANGED <<snap, valid, life>>
\* the marker could not be written: nothing is released, the lease just ages
ReleaseFail(s) ==
  /\ pc[s] = "release"
  /\ Finish(s, "worker")
  /\ UNCHANGED <<top, snap, valid, life>>

\* ---- time passes: the top claim ages ----------------------------------------
Age ==
  /\ ~Absent(top)
  /\ top.age # "stale"
  /\ ~\E s \in Sessions : acting[s] /\ Mine(top, s)                         \* A2
  /\ top.age = "margin" =>                                                 \* A1
       ~\E s \in Sessions : pc[s] \in {"touch", "verify"} /\ valid[s]
  /\ top' = [top EXCEPT !.age = IF @ = "fresh" THEN "margin" ELSE "stale"]
  /\ UNCHANGED <<snap, valid, pc, hook, role, acting, life>>

Step(s) == Scan(s) \/ Touch(s) \/ TouchFail(s) \/ Create(s) \/ Verify(s)
           \/ Release(s) \/ ReleaseFail(s)
Host(s) == Open(s) \/ Turn(s) \/ Mid(s) \/ Stop(s) \/ Close(s) \/ Crash(s)

Next == Age \/ \E s \in Sessions : Step(s) \/ Host(s)

\* Fairness: time passes, a running hook finishes, and a session that is open
\* keeps taking turns (somebody is using it). Nothing forces a crash or a close.
Fairness ==
  /\ WF_vars(Age)
  /\ \A s \in Sessions : WF_vars(Step(s)) /\ WF_vars(Turn(s)) /\ WF_vars(Stop(s))
Spec == Init /\ [][Next]_vars /\ Fairness

\* Sessions are interchangeable: safety may be checked up to their permutation
\* (Election.cfg). Not used for liveness, where symmetry is unsound.
Perms == Permutations(Sessions)

\* ---- the properties ----------------------------------------------------------
\* (d) safety: never two sessions acting as orchestrator at once
AtMostOneActing == Cardinality({s \in Sessions : acting[s]}) <= 1

\* only the holder of the top claim acts
ActingHoldsTop == \A s \in Sessions : acting[s] => Mine(top, s)

\* every hook run ends -- the script never blocks a session
HooksEnd == \A s \in Sessions : (hook[s] # "none") ~> (hook[s] = "none")

\* (g) liveness: once the holder is gone, a session that opens is elected, or
\* another live session holds a valid claim
Live(s) == life[s] \in {"idle", "turn"}
Held    == \E t \in Sessions : Live(t) /\ Mine(top, t) /\ role[t] = "orch"
ElectedAfterGone ==
  \A s \in Sessions : (hook[s] = "start" /\ pc[s] = "scan") ~> (Held \/ ~Live(s))
=============================================================================
