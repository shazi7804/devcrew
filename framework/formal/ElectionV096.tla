---------------------------- MODULE ElectionV096 ----------------------------
(* The orchestrator election as boot.py 0.9.6 implemented it: ONE lock path,
   taken by O_EXCL create, taken over by rename-then-create once its mtime is
   older than STALE. Kept as the seeded broken variant of Election.tla: under
   the SAME environment (the same hooks, the same timing assumptions A1, A2)
   TLC finds two sessions acting as orchestrator at once.

   The flaw is in the code, not the environment: rename acts on a PATH, not on
   the file that was read. A session that read a stale lock, then paused, can
   rename the fresh lock that another session created in between -- and
   utime(LOCK) can refresh a lock that is no longer the caller's. *)
EXTENDS Naturals, FiniteSets

CONSTANTS Sessions, None

Ages   == {"fresh", "margin", "stale"}   \* fresh: age <= STALE - MARGIN
NoLock == [sid |-> None, age |-> "stale"]

VARIABLES lock, snap, valid, pc, hook, role, acting, life
vars == <<lock, snap, valid, pc, hook, role, acting, life>>

Absent    == lock.sid = None
Mine(s)   == lock.sid = s
Stale(l)  == l.age = "stale"        \* 0.9.6 has no margin: margin is not stale

Init ==
  /\ lock = NoLock
  /\ snap = [s \in Sessions |-> NoLock]
  /\ valid = [s \in Sessions |-> FALSE]
  /\ pc = [s \in Sessions |-> "none"]
  /\ hook = [s \in Sessions |-> "none"]
  /\ role = [s \in Sessions |-> "none"]
  /\ acting = [s \in Sessions |-> FALSE]
  /\ life = [s \in Sessions |-> "off"]

Finish(s, r) ==
  /\ role' = [role EXCEPT ![s] = r]
  /\ acting' = [acting EXCEPT ![s] =
       \/ hook[s] = "pre" /\ r = "orch"
       \/ hook[s] = "mid" /\ acting[s] /\ r = "orch"]
  /\ hook' = [hook EXCEPT ![s] = "none"]
  /\ pc' = [pc EXCEPT ![s] = "none"]

Fire(s, h) == /\ hook' = [hook EXCEPT ![s] = h]
              /\ pc' = [pc EXCEPT ![s] = "scan"]

\* ---- the host's lifecycle events -------------------------------------------
Open(s)  == /\ life[s] = "off" /\ life' = [life EXCEPT ![s] = "idle"]
            /\ Fire(s, "start") /\ UNCHANGED <<lock, snap, valid, role, acting>>
Turn(s)  == /\ life[s] = "idle" /\ hook[s] = "none"
            /\ life' = [life EXCEPT ![s] = "turn"]
            /\ Fire(s, "pre") /\ UNCHANGED <<lock, snap, valid, role, acting>>
Mid(s)   == /\ life[s] = "turn" /\ hook[s] = "none"
            /\ Fire(s, "mid") /\ UNCHANGED <<lock, snap, valid, role, acting, life>>
Stop(s)  == /\ life[s] = "turn" /\ hook[s] = "none"
            /\ life' = [life EXCEPT ![s] = "idle"]
            /\ acting' = [acting EXCEPT ![s] = FALSE]
            /\ Fire(s, "post") /\ UNCHANGED <<lock, snap, valid, role>>
Close(s) == /\ life[s] = "idle" /\ hook[s] = "none"
            /\ Fire(s, "end") /\ UNCHANGED <<lock, snap, valid, role, acting, life>>
Crash(s) == /\ life[s] \in {"idle", "turn"} /\ hook[s] = "none"
            /\ life' = [life EXCEPT ![s] = "gone"]
            /\ acting' = [acting EXCEPT ![s] = FALSE]
            /\ UNCHANGED <<lock, snap, valid, pc, hook, role>>

\* ---- boot.py 0.9.6, one atomic file-system step per action -----------------
Scan(s) ==
  /\ pc[s] = "scan"
  /\ snap' = [snap EXCEPT ![s] = lock]
  /\ valid' = [valid EXCEPT ![s] = TRUE]
  /\ IF hook[s] = "end" THEN
       IF Mine(s) THEN pc' = [pc EXCEPT ![s] = "release"] /\ UNCHANGED <<hook, role, acting>>
       ELSE Finish(s, role[s])
     ELSE IF hook[s] = "start" THEN
       IF Absent THEN pc' = [pc EXCEPT ![s] = "create"] /\ UNCHANGED <<hook, role, acting>>
       ELSE IF Mine(s) THEN pc' = [pc EXCEPT ![s] = "touch"] /\ UNCHANGED <<hook, role, acting>>
       ELSE IF Stale(lock) THEN pc' = [pc EXCEPT ![s] = "rename"] /\ UNCHANGED <<hook, role, acting>>
       ELSE Finish(s, "worker")
     ELSE \* beat: refresh if mine (whatever its age), else demoted
       IF Mine(s) THEN pc' = [pc EXCEPT ![s] = "touch"] /\ UNCHANGED <<hook, role, acting>>
       ELSE Finish(s, "worker")
  /\ UNCHANGED <<lock, life>>

\* os.utime(LOCK): refreshes whatever file is at the path now
Touch(s) ==
  /\ pc[s] = "touch"
  /\ lock' = IF Absent THEN lock ELSE [lock EXCEPT !.age = "fresh"]
  /\ Finish(s, "orch")
  /\ UNCHANGED <<snap, valid, life>>

\* os.rename(LOCK, evidence): moves whatever file is at the path now
Rename(s) ==
  /\ pc[s] = "rename"
  /\ IF Absent THEN Finish(s, "worker") /\ UNCHANGED <<lock, valid>>
     ELSE /\ lock' = NoLock
          /\ valid' = [t \in Sessions |-> FALSE]
          /\ pc' = [pc EXCEPT ![s] = "create"]
          /\ UNCHANGED <<hook, role, acting>>
  /\ UNCHANGED <<snap, life>>

\* os.open(LOCK, O_CREAT | O_EXCL)
Create(s) ==
  /\ pc[s] = "create"
  /\ IF Absent THEN /\ lock' = [sid |-> s, age |-> "fresh"]
                    /\ valid' = [t \in Sessions |-> FALSE]
                    /\ Finish(s, "orch")
     ELSE Finish(s, "worker") /\ UNCHANGED <<lock, valid>>
  /\ UNCHANGED <<snap, life>>

\* os.rename(LOCK, RELEASED)
Release(s) ==
  /\ pc[s] = "release"
  /\ lock' = NoLock
  /\ valid' = [t \in Sessions |-> FALSE]
  /\ Finish(s, role[s])
  /\ UNCHANGED <<snap, life>>

\* ---- time passes: the lock ages ---------------------------------------------
\* A1: a hook process pauses for less than MARGIN, so a session that read the
\*     lock as fresh and is about to touch it does so before it can go stale.
\* A2: an acting orchestrator beats more often than STALE - MARGIN, so the
\*     lock of an acting holder does not age.
Age ==
  /\ ~Absent
  /\ ~\E s \in Sessions : acting[s] /\ Mine(s)                           \* A2
  /\ lock.age # "stale"
  /\ lock.age = "margin" =>
       ~\E s \in Sessions : pc[s] = "touch" /\ valid[s] /\ snap[s].age = "fresh"  \* A1
  /\ lock' = [lock EXCEPT !.age = IF @ = "fresh" THEN "margin" ELSE "stale"]
  /\ UNCHANGED <<snap, valid, pc, hook, role, acting, life>>

Step(s) == Scan(s) \/ Touch(s) \/ Rename(s) \/ Create(s) \/ Release(s)
Host(s) == Open(s) \/ Turn(s) \/ Mid(s) \/ Stop(s) \/ Close(s) \/ Crash(s)

Next == Age \/ \E s \in Sessions : Step(s) \/ Host(s)
Spec == Init /\ [][Next]_vars

\* ---- the property ------------------------------------------------------------
AtMostOneActing == Cardinality({s \in Sessions : acting[s]}) <= 1
=============================================================================
