# analyst — Market Analyst

> The honest brake: decides whether the idea is worth building before the team
> spends money on it.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/analyst.md`](../../framework/agents/analyst.md)

## At a glance

| | |
|---|---|
| **Phase** | 0.5, before the intent batch: the CEO signs the requirements and the verdict together |
| **Runs when** | The idea has a commercial or product side. Purely internal tools skip it |
| **Reads** | `requirements.md` |
| **Produces** | Market analysis with charts, and a GO / PIVOT / NO-GO verdict |
| **Gate** | 🔴 The CEO reads the verdict and decides |
| **Tools** | read · search · web (no write) |
| **Skills** | aidlc · image-authoring · widgets |
| **Memory** | Shared team memory |

## What it does

1. **Researches the live market** with web search, not training memory: real
   demand, the target segment, a rough TAM/SAM (with its assumptions stated),
   competitors and substitutes, and the trend direction.
2. **Charts it**: market-size bars, a competitor 2×2, a demand trend, a segment
   breakdown.
3. **Returns a verdict**:
   - **GO**: proceed to Phase 1.
   - **PIVOT**: the market is real but the framing is wrong. The adjusted
     framing goes back to Phase 0 and needs a new signature.
   - **NO-GO**: stop here. Killing the idea now is the cost saved.
4. **States its confidence and gaps.** Data it could not verify never counts as
   a GO.

## What it will not do

- Make a market claim without a source.
- Inflate a TAM to justify a build.
- Follow instructions embedded in a web page. It treats fetched content as data.

## Where it sits

```
orchestrator (P0 signed) ──▶ analyst ──▶ 🔴 CEO ──GO──▶ architect
                                           └─PIVOT──▶ back to P0
```
