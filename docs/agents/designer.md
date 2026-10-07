# designer — Design (UI/UX)

> Hands over a design contract that can be verified, not a picture: tokens, a
> clickable prototype, and a scorecard showing it reached award grade.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/designer.md`](../../framework/agents/designer.md)

## At a glance

| | |
|---|---|
| **Phase** | 2 |
| **Runs when** | The product has a user-facing surface. The orchestrator makes that call and records it |
| **Reads** | `requirements.md` · `design.md` |
| **Produces** | `design-system.md` (tokens as CSS custom properties), the chosen prototype, and `design-scorecard.md` |
| **Gate** | The scorecard shows the bar is met, then 🔴 the CEO signs the chosen prototype |
| **Tools** | read · write · edit · shell · search · web |
| **Skills** | aidlc · frontend-design-workflow · web-preview · [impeccable](https://impeccable.style/) |
| **Memory** | Shared team memory |

## What it does

1. **Design system first**: color, type scale, spacing, radius, elevation and
   motion, all as CSS variables, so the implementation cannot drift from them.
2. **Information architecture and user flows**, tied to the requirements' user
   journeys.
3. **2–3 genuinely distinct hi-fi prototypes**, not three shades of one idea,
   shown in the browser. It recommends one and the CEO chooses. **The chosen
   prototype is the visual spec.**
4. **Accessibility pass**: contrast, focus order, keyboard paths, semantics,
   reduced motion.
5. **Award-grade loop.** The target is Awwwards Site of the Day, a Webby, and
   FWA of the Day. Each round runs through five steps:

```
   screenshot ──▶ /impeccable critique + audit + `impeccable detect`
       ▲                         │
       │                         ▼
   refine (typeset · layout · animate · ...)  ◀── score the rubric
                                  │
                                  ▼
                        record the round in design-scorecard.md
```

   The rubric weights the Awwwards categories: Design 40%, Usability 30%,
   Creativity 20%, Content 10%. The Webby and FWA lenses do not score, but
   either one can veto a design.
   **Exit**: weighted score ≥ 8.0, no category below 7.5, no veto,
   `impeccable detect` exits 0, and a11y still holds. Then a final
   `/impeccable polish`.
   **Stop**: if two rounds in a row fail to raise the score, or round 6 ends
   below the bar, it reports the gap to the CEO instead of passing the design.

## Mobile

A mobile app has to follow two design languages: Apple HIG and Material 3. The
prototypes are shown in real device frames (a compact and a large phone, plus
iPad if the app is universal), and each direction states how it adapts to each
platform.

## What it will not do

- Hand over a design that is below the bar as if it had passed.
- Let impeccable's `DESIGN.md` become a second token contract.
  `design-system.md` is the only one.
- Design only the happy path. Empty, loading, error and success states are all
  designed.

## Where it sits

```
architect ──▶ designer ──▶ 🔴 CEO picks ──▶ frontend (builds it exactly)
```
