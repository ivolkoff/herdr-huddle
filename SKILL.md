---
name: huddle
description: Use when an agent inside herdr (HERDR_ENV=1) needs a decision or input from the user, or when the user asks for huddle, a question with pictures, diagrams, charts, previews, or sliders.
---

# huddle — ask with a page, not a prompt

One command opens the question zoomed over the pane of **this** herdr session, waits for the answer and
prints it as JSON. The runtime (layout, styles, charts, diagrams, sliders, keyboard) is done; you only
describe the question.

Set `H` to `bin/huddle` next to this `SKILL.md`. These are the usual skill locations:

```bash
H="$HOME/.agents/skills/huddle/bin/huddle"  # Codex
[ -f "$H" ] || H="$HOME/.claude/skills/huddle/bin/huddle"  # Claude Code
```

Requires: herdr (`HERDR_ENV=1`), plugin `ivolkoff.huddle` in `herdr plugin list`
(`herdr plugin install ivolkoff/herdr-huddle`), `terminal-browser` in `PATH`. Without herdr the page
opens in the default browser.

## Running

The command waits for the user's answer and prints JSON to stdout. Keep its process and output attached to
your agent session. In Claude Code, use `run_in_background: true`; the completed task brings you back, so
say that the question is open and end your turn. In Codex CLI, start it with a short `yield_time_ms` and,
if the command returns a session ID, collect the result with `write_stdin` on that session. Do not use
`sleep` or start a detached process that loses stdout. Say in one line that the question is open.

Write questions and options in the user's language.

## Quick: one line

```bash
python3 $H q "Where should sessions live?" "*Redis|already runs the job queue" "Postgres table|no new service" "Stateless JWT|cannot be revoked"
```

An option is `Label|subtitle`; a leading `*` marks it recommended. `--multi` for multiple choice,
`--context "markdown"` for a paragraph under the question, `--title` for the topic above it.

## Usual: a JSON spec

Write the spec to the scratchpad and pass the path (`python3 $H /path/spec.json`) or pipe it on stdin
(`python3 $H - <<'JSON' … JSON`).

```json
{
  "title": "Session storage",
  "prompt": "Where should sessions live?",
  "context": "Sessions live in process memory; every deploy logs everyone out.",
  "options": [
    {"id": "redis", "label": "Redis", "subtitle": "Managed, TTL per key",
     "recommended": "Already runs the job queue",
     "pros": ["Reads < 1 ms"], "cons": ["One more moving part"]},
    {"id": "pg", "label": "Postgres table", "subtitle": "One table, index on expiry"}
  ]
}
```

## Phrase the question first

The question is the largest thing on the page; everything else supports it.

- `prompt`: **one short direct question**, ideally under 12 words, ending with `?` or in the imperative
  ("Tune the card style until you like it"). It alone should make clear what to do.
- `title`: the topic in 2–5 words. Small, above the question.
- `hint`: one line under the question — what matters or how to answer. Not a second question.
- `context` / `body`: evidence — numbers, a diagram, a diff. Under the question.
- `header`: one or two words per question, for tabs and the summary.

## Pick the component for the answer

| The answer is… | Use | Template |
| --- | --- | --- |
| one of several alternatives | options, `layout: "list"` | `pick` |
| alternatives where trade-offs matter | `layout: "compare"` (side by side, pros and cons visible) | `tradeoffs` |
| a picture (diagram, layout, sample) | options with `preview` → `grid` | `architecture`, `layouts`, `design-tokens` |
| yes / no / later | `layout: "inline"` | `confirm` |
| several items from a list | `mode: "multi"`, `min`/`max` | `checklist` |
| a number or color by taste, no standard scale (radius, spacing, hue, speed, size, weight, delay) | **`controls`** — sliders with a live preview | `tune` |
| words | `mode: "text"` | `text` |
| several related decisions | `questions: [...]` — tabs, then a summary of all answers | `design-tokens` |

Standard values exist (4/8/16 px, a design-system scale) — offer them as options with previews. The value is
continuous or purely a matter of taste — sliders: the user sees the result while dragging. They combine:
pick a direction with options, then fine-tune with a `controls` question (see `demos/ui-kit`).

`python3 $H templates` lists the templates (`templates/<name>.json` next to this file): copy one and fill
it in. Combined examples are in `demos/` (`motion`, `ui-kit`, `auth-flow`, `rollout`, `pricing`) — read the
files; `python3 $H demo NAME` opens one.

## The answer

```json
{"status": "answered",
 "answers": {"answer": {"selected": ["redis"], "labels": ["Redis"], "text": "but only for prod"}}}
```

- `answers` is keyed by question id (`answer` for a single-question spec, `q1`, `q2`… for unnamed ones).
- Every choice question ends with an "Other" option (`id: "other"`). When it is chosen, the user's own answer
  is in `text`; the page will not submit it without text. Do not add such an option to `options` yourself.
- `selected` holds option ids in display order; `text` is present only if the user wrote something. It comes
  **alone** (their own answer) or **together** with a choice (a comment on it). Read both: comments carry
  corrections and new branches.
- A question with `controls` adds `values` (`{"radius": 12, "hue": 174, "shadow": true}`). `selected` holds a
  preset only if it was left untouched; `from` is the preset they started from and then changed.
- `extra` — if the page's JS called `api.setExtra(...)`.
- Exit 0 with `status: "chat"` (and `text`): **Discuss in chat** was pressed — the user wants to talk in the
  terminal. Stop and ask there; do not choose for them.
- Exit 2, `status: "dismissed"`: the pane was closed without an answer. That means "not now": do not reopen
  the same question in a loop; say in the chat what you need.
- Exit 3: nowhere to show it (plugin not installed, outside herdr with `HUDDLE_NO_BROWSER=1`, the browser did
  not open) — ask with AskUserQuestion and name the reason from `error`.
- Exit 4: `--timeout` ran out (a day by default). The page is closed and cannot be resumed — ask again.

## Spec reference

Top level: `title`, `subtitle`, `source` (replaces "Your agent is asking"), `context` (blocks),
`width: "narrow"` (for short questions), `submitLabel`, `chat: false` (hide Discuss in chat), `script`
(JS, see [Extending](#extending)), `style`, `review` (see [Look and summary](#look-and-summary)) and
**either** the fields of a single question **or** `questions: [...]` (tabs, answered in order).

Question: `id`, `header`, `prompt`, `hint`, `body` (blocks), `recommendation` (a markdown banner with the
overall pick), `mode` (`single` by default · `multi` · `text`; `tune` is implied by `controls`),
`min`/`max` (multi), `layout` (`list` · `grid` · `compare` · `inline`; defaults to `grid` if some option
has a `preview`, `inline` for presets, otherwise `list`), `columns`, `expanded: true` (expand the details of
all options), `optional: true` (may be submitted empty), `text` (`false` removes the text field and the
"Other" option, or `{label, placeholder, required, multiline, value}`), `other` (`false` removes the "Other"
option, a string renames it; it is not added when there are 9 options).

Option: `id`, `label`, `subtitle` (grey line), `recommended` (`true` or a string — the reason, shown under
it), `badge` (replaces the word "Recommended"), `tags` (small chips: effort, risk), `pros`, `cons`,
`detail` (blocks behind "details"), `preview` (a block — the card's picture), `default: true` (preselected),
`values` (a preset in a `controls` question). Plain strings work as options: `"options": ["Yes", "No"]`.

### Controls (sliders with a live preview)

```json
{
  "title": "Dashboard cards",
  "prompt": "Tune the card style until you like it",
  "controls": [
    {"id": "radius", "label": "Corner radius", "min": 0, "max": 28, "value": 8, "unit": "px"},
    {"id": "hue", "label": "Accent", "type": "hue", "value": 220},
    {"id": "speed", "label": "Duration", "min": 100, "max": 1200, "step": 20, "value": 300, "unit": "ms"},
    {"id": "weight", "label": "Heading weight", "type": "select", "options": ["500", "600", "700"], "value": "600"},
    {"id": "shadow", "label": "Shadow", "type": "toggle", "value": false, "on": "0 6px 18px rgba(0,0,0,.3)", "off": "none"},
    {"id": "brand", "label": "Brand color", "type": "color", "value": "#0d9488"}
  ],
  "preview": {"html": "<div style='border-radius:var(--radius);background:hsl({hue} 65% 45%);box-shadow:{shadow};font-weight:{weight};transition:all var(--speed)'>Sample</div>"},
  "baseline": true,
  "options": [{"id": "soft", "label": "Soft", "values": {"radius": 14, "shadow": true}}]
}
```

- Control `type`: `range` (default; `min`, `max`, `step`, `unit`) · `hue` (0–360, a rainbow track) ·
  `color` (picker, `#rrggbb`) · `select` (segments, `options`) · `toggle` (`on`/`off` — substituted
  strings; `"1"`/`"0"` by default).
- In `preview` (any block) `{id}` is replaced with the raw value (`12`, `#0d9488`, `600`), while `var(--id)`
  carries the unit (`12px`, `300ms`). The preview redraws on every change and replays CSS animations; `r` or
  the ⟳ button replays without a change.
- `baseline: true` (or a caption string) shows the starting values next to the live ones ("Now" | "Yours").
- `options` with `values` are presets: picking one moves the sliders.
- Every slider has ↺ to restore its starting value.
- Linking, optional: a `preview` can read answers on the same page — `{@qid}` is the id of the option chosen
  in question `qid` (comma-separated for multi), `{@qid.label}` its label, `{@qid.ctl}` a slider value of
  another controls question. Use it when the fine-tuning applies to what was just chosen (`demos/motion`);
  independent questions do not need it.

### Blocks

Used in `context`, `body`, `detail`, `preview`. A plain string is markdown (`**bold**`, `*em*`,
`` `code` ``, lists, `> quote`, `[link](https://…)`, fenced code). Every block accepts `title`, `caption`
and `card: true`.

| Block | Shape |
| --- | --- |
| markdown | `"text"` or `{"md": "text"}` |
| Jira wiki | `{"jira": "h2. Context\n\n* item"}` — rendered the way Jira shows a description: `h1.`–`h6.`, nested `*`/`#` lists, `{{mono}}`, `*bold*`, `_italic_`, `~sub~`, `[text\|url]`, `{code}`, `{quote}`, `\|\|` tables. Lines under a list item stick to it until a blank line, as in Jira. Show a draft issue description with this block before writing it, not with `code` |
| diagram | `{"mermaid": "flowchart LR\n A --> B"}` — any mermaid type (flowchart, sequence, class, state, ER, gantt, gitGraph). Avoid `#` in labels (it starts an entity: `#1` cuts the line) and `%` (a comment in gantt); add `todayMarker off` to gantt |
| chart | `{"chart": {"type": "bar"\|"line"\|"area"\|"hbar"\|"donut"\|"pie", "labels": [...], "series": [{"name", "values", "color"}], "unit": " ms"}}` — `values` is enough for one series. Optional: `title`, `highlight` (index or label; not for donut/pie), `marks: [{"value", "label"}]` (threshold lines), `min`, `max`, `height`; donut/pie take `colors`, `center`, `size`; hbar takes `labelWidth` |
| stat tiles | `{"stats": [{"label", "value", "delta", "good": true\|false\|null, "sub"}]}` |
| image | `{"image": "/abs/or/relative.png", "height": 160, "fit": "cover", "alt": "…"}` — local files are embedded (up to 8 MB); a missing one shows its alt |
| code / diff | `{"code": "…", "lang": "ts"}`, `{"diff": "@@ …\n+added\n-removed"}` |
| table | `{"table": {"columns": [...], "rows": [[...]]}}`, `{"kv": {"key": "value"}}` |
| callout | `{"callout": "markdown", "tone": "ok"\|"warn"\|"bad"}` |
| design samples | `{"radius": 12}`, `{"gap": 16, "items": 4, "direction": "column"}`, `{"colors": ["#hex", {"name", "value"}]}`, `{"type": {"family", "size", "weight", "tracking", "text"}}`, `{"style": {css}, "text": "…"}` |
| layout | `{"row": [block, block]}` — side by side; a list of blocks — stacked |
| svg / html / js | see [Extending](#extending) |

Mermaid is downloaded once to `~/.cache/huddle/`; without network, diagrams show their source.

## Extending

The standard components cover almost everything. If a question needs something they lack (a real component
in the product's style, an animation, a filterable list), build it inside the question, not in the skill:

- `{"html": "…"}` / `{"svg": "…"}` — raw markup as a block or an option's `preview`. `<style>` and CSS
  animations work. Take colors from the variables: `--fg`, `--bg`, `--accent`, `--ok`, `--warn`, `--bad`,
  `--magenta`, `--cyan`, `--muted`, `--line`, `--line-strong`, `--panel`, `--panel-2`. Hardcode a color only
  when the color is the question.
- `{"js": "code"}` — runs as `function(el, api)`; draw into `el`. A top-level `script` runs once with `api`.
  `api.setExtra(questionId, value)` (comes back as `extra`), `api.setText(questionId, text)`,
  `api.select(questionId, optionId)`, `api.submit()`, `api.block(spec)` / `api.chart(spec)` (render a
  standard block), `api.md(text)`, `api.css("--accent")` (computed color).
- Use `controls` instead of hand-made sliders: keyboard, reset, presets, baseline and the summary come free.
- Do not escape anything in ordinary fields — the runtime escapes them. `html`, `svg` and `js` are raw: never
  put foreign text (an issue body, a log line) there; put it in markdown or `code`.

## How the user answers

`1`–`9`, arrows, `Space`, `Enter`, `Tab` into the comment field, `⇧←`/`⇧→` between questions, `⌥Enter` to
discuss in chat. Hints are in the page footer, `?` shows the rest. No need to explain this to the user.

## Look and summary

Defaults live in `defaults.json` next to this file, overlaid by the personal
`~/.config/huddle/defaults.json` (or `$HUDDLE_CONFIG`). Do not override personal settings without a reason.
For a single call, a flag or the same key in the spec wins:

- `style`: `refined` (soft cards) · `minimal` (rows with a thin rule) · `bold` (large type, filled
  selection) · `terminal` (monospace). `--style NAME`.
- `review`: a summary before sending — every choice, a thumbnail of visual answers, slider values with a
  preview, the comment. `auto` — when there are several questions or a comment was written on a choice ·
  `always` · `never`. `--review MODE`. Question tabs also show the current answer ("Radius · 14 px + note").

## Behavior

- The page opens as a plugin pane over this session's pane (`$HERDR_PANE_ID`) without stealing focus. Coming
  back to the workspace focuses the page again. After the answer the pane closes by itself.
- A pane closed without an answer is `dismissed`. The script sends a zoom reset (`ctrl+0`) on load and on
  every scale change: terminal-browser changes zoom along with herdr's cell size.
- `--browser` opens the default browser even inside herdr. A closed tab is also `dismissed`.
- The server lives as long as the process: a question that timed out cannot be resumed.
- `python3 $H render spec.json -o out.html` builds the page without showing it — to check a spec.

## Recommendations

- Recommend when you have an opinion, and write **why** in the `recommended` string; mark several if several
  are good. A one-line verdict above the options goes in `recommendation`.
- Up to 6 options read well; 7–9 only for homogeneous lists (versions, files).
- A subtitle carries the one fact that sets the option apart; the rest goes in pros/cons.
- Gather related questions on one page (`questions`) instead of opening several in a row.
