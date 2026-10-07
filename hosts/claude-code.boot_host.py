"""Claude Code adapter for framework/tools/boot.py.

Install beside boot.py as `.aidlc/tools/boot_host.py`. boot.py returns a
neutral {message, context, quiet}; this reshapes it into Claude Code's hook
protocol: `systemMessage` is shown to the human, and
`hookSpecificOutput.additionalContext` is injected into the model's context.
"""


def adapt(out, payload):
    shaped = {}
    if out.get("message"):
        shaped["systemMessage"] = out["message"]
    if out.get("quiet"):
        shaped["suppressOutput"] = True
    if out.get("context"):
        shaped["hookSpecificOutput"] = {
            "hookEventName": payload.get("hook_event_name", "SessionStart"),
            "additionalContext": out["context"],
        }
    return shaped
