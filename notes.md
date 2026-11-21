# Technical notes

Primary implementation reference. These are implemented rules, not validation
of the social extensions by the infection article. Sources: [references.md](references.md).

## Index

[Model](#model) | [Transmission](#transmission) | [Movement](#movement) |
[Update order](#update-order) | [Statistics](#statistics) |
[GIF export](#gif-export) | [Defaults](#defaults) | [Limits](#limits)

## Model

| State | Meaning / exit |
|---|---|
| Unaware | No message accepted; may accept rumour or correction |
| Spreader | Shares rumour; expires or accepts correction |
| Corrector | Shares correction; expires |
| Stifler | Silent believer, expired sharer or explicit rejecter; may accept first correction |

Belief, sharing, friendship and avoidance are separate. Expiry preserves belief.
Correction clears belief/avoidance, not lost friendship. Previously corrected
stiflers do not restart correction activity on repeated exposure.

Domain: 100x100. Centres: (33,33), (67,33), (33,67), (67,67); radius 15.
No-group probability: 0.2. Patient zero is in A; subject in D. Up to 12 friends
are selected across all groups/no-group agents; four start nearby and linger.
Friendship does not change home group. Shape follows membership, not location.

## Transmission

Method: `simulation.rollSpread`. For recipient i, let g_i=gullibility,
o_i=openness and beta_r/beta_c=message strengths. Neighbours read old states.

```text
D_ij = sqrt((x_i-x_j)^2 + (y_i-y_j)^2)
A_r(i,j) = 1[i != j and D_ij < contactRadius]
A_c(i,j) = 1[i != j and D_ij < correctionRadius]
nr_i = sum_j A_r(i,j)*1[state_j == SPREADER]
nc_i = sum_j A_c(i,j)*1[state_j == CORRECTOR]
P_r(i) = 1 - (1 - g_i*beta_r)^nr_i
P_c(i) = 1 - (1 - o_i*beta_c)^nc_i
P(share | rumour accepted) = m + (1-m)*s_i
```

The aggregate probabilities assume independent contact opportunities. Code draws
one Bernoulli per message/recipient. If both succeed for an unaware agent, a fair
coin chooses one. Sender credit is uniform among eligible nearby active senders.
Changes apply after sampling; no same-step contagion cascade.

m=minInterest; s_i=sharingTendency (reuses interest). Openness and loyalty are
independent per-agent samples. No loudness/influence trait is implemented.
Acceptance without sharing creates a silent believer. Failed acceptance leaves
the agent unaware. Explicit rejection currently uses the subject-denial branch;
subjectDenies=1 yields denial/correction, so zero explicit rejections is expected.
Uncorrected stiflers and active spreaders can accept correction.

Methods: `Agent.acceptBelief`, `becomeCorrector`, `tick`.

```text
P(friendship ends | first belief) = 1-loyalty_i
P(avoid | non-friend's first belief) = avoidChance
counter(t+1)=counter(t)-1 for active agents; counter<=0 -> STIFLER
```

Breakup forces avoidance and ends lingering. Loyal friends may believe/share
without avoiding. Non-friend avoidance is drawn once. Recovery is fixed-duration,
not exponential recovery with a fitted gamma.

## Movement

Methods: `randomPointNear`, `randomWalk`, `moveAgent`, `moveAgents`.

```text
Disk sample: theta=2*pi*U1; r=R*sqrt(U2)
p=(cx+r*cos(theta),cy+r*sin(theta))
Walk: p'=p+stepSize*(U(-1,1),U(-1,1))
Travel: p'=p+min(travelSpeed,||c-p||)*(c-p)/||c-p||
R_outer=avoidRadius*avoidVisualBuffer
Outward pressure=stepSize*(R_outer-d)/(R_outer-avoidRadius)
```

U1/U2 are independent uniforms; sqrt produces uniform disk area. Coordinates are
clamped to the box; wanderers project back to the target group circle. Visits
travel to another group, stay, then return. Lingering friends use a subject-centred
region. Soft pressure applies only for avoidRadius<d<R_outer. Alternate targets
reduce attraction toward a centre blocked by the subject; tangential fallback remains.

Methods: `segmentDistance`, `safeMove`. For segment p->q and subject centre c:

```text
v=q-p
t=clip(((c-p) dot v)/(v dot v),0,1); t=0 if v dot v=0
d_segment=||p+t*v-c||
Accept path if d_segment>=avoidRadius
```

Blocked paths try safe tangential/outward movement. Existing overlaps evacuate
to a feasible boundary point; not speed-limited physics or global path planning.
A moving subject can create overlaps between updates. Display easing also uses
the collision guard.

Subject awareness (`stepSimulation`): accumulate observations of avoiders within
avoidRadius+2. At noticeAfter, start correction without an invented teller/hop.
Direct rumour contact can also trigger denial.

## Update order

```text
set correction duration and pending avoidance probability
subject observation -> subject movement -> other movement / avoidance
timer expiry -> sample snapshot transmissions -> apply transitions
configured correction seeds -> record counts
```

Movement and RNG draws remain ordered. Snapshot contagion alone does not provide
serial/parallel equivalence.

## Statistics

Methods: `countStates`, `countSpreadersByGroup`, `nearSubject`, `transmissionStats`.

```text
N_k(t)=sum_i 1[state_i(t)==k]; sum_k N_k(t)=N
Told_j=sum_i 1[infector_i==j]
Near_all=sum_(i != subject) 1[distance(i,subject)<nearRadius]
Near_believers=sum_(i != subject) 1[distance<nearRadius and believed_i]
```

Direct-told is attributed recipients, not descendants, correction sources or all
conversations. Equal counts can tie. Live joint-rank display remains outstanding.

Rendering methods: `RumourWindow.on_update`, `FriendshipWindow.on_draw`.

```text
Base radius: inactive=3.25px; active=5.75px; hop view=4.75px
S mode, Told>0: radius=max(base,min(16,3+3*sqrt(Told)))
Diamond offsets: (0,1.5r),(.75r,0),(0,-1.5r),(-.75r,0)
p_shown += (p_real-p_shown)*(1-exp(-14*dt))
```

The size ceiling does not cap transmissions. Original font/sprites retained;
intro=3s hold+2s glide. Pink=friend/subject; violet=ex-friend; orange=inactive former
sharer. Red rings follow avoiding, not all belief. Correction does not restore
friendship colour. Chart=400x220; three visible leaderboard/log rows. T arrows,
F gold chains, G hop colours, H group rings and top-five tracking remain.

## GIF export

Entry: `gif_export.py`; CPU rendering, no Arcade/OpenGL context.

```powershell
python gif_export.py "A rumour about the subject" --seed=42
python gif_export.py "A rumour about the subject" --n=200 --steps=400 --every=4 --fps=15 --width=1000 --output=results/simulation.gif
```

| Export argument | Default | Meaning |
|---|---:|---|
| --output | results/simulation.gif | GIF path |
| --every | 4 | Model steps between snapshots |
| --fps | 15 | Playback frames/second |
| --width | 1000 | Width in pixels; minimum 480 |

Model arguments pass to main.py's parser. Methods:

1. `recordRun`: calls the existing serial step once per step. Records state/group
   counts and proximity every step. Captures agents at step 0, every interval and
   the final step; no rerun and no additional random draws.
2. `snapshot`: copies positions, states, membership, social flags and direct counts.
   Later agent changes cannot overwrite earlier frames.
3. `saveGif`: Matplotlib Agg + FuncAnimation + PillowWriter. Synchronized agent
   view, state curves, proximity curves and statistics from the same recorded step.
4. JSON sidecar: seed, population, steps, model settings, frame steps, FPS, interval,
   width and rumour. Package versions are not captured; record the environment separately.

```text
Frame steps={0,every,2*every,...} union {steps}
F=ceil(steps/every)+1; approximate playback length=F/fps seconds
Snapshot memory=O(N*F); cached raster memory can be O(F*width*height)
```

GIF timing is quantised. Sampling can omit short-lived events; final partial
interval is included. Uses model positions, not the intro/eased path. Glows,
transient arrows, hover and selected chains are not reproduced. Marker sizes
are Matplotlib point units: results renderer, not pixel-identical screen capture.

Reports model+recording and render+encode times separately; neither is model-only
benchmark time. main.py's headless elapsed time still includes plot generation.
Large exports can exhaust RAM: reduce width or increase every.

## Defaults

| Setting | Value | CLI |
|---|---:|---|
| Population / steps / seed | 500 / 400 / 42 | --n / --steps / --seed |
| Centre distance from edges / radius | 33 / 15 | --group-spread / --leash |
| Correction strength / duration | 0.03 / 50 | --correction-strength / --correction-duration |
| Correction radius | Contact radius | --correction-radius |
| Avoidance outer-zone multiplier | 1.15 | --avoid-visual-buffer |

Code settings: contactRadius=4*sqrt(500/N), rumourStrength=0.06,
rumour active duration=50, stepSize=1.5, travelChance=0.003, travelSpeed=2,
stayLength=40, minInterest=0.5, subjectDenies=1, avoidRadius=7,
avoidChance=0.75, noticeAfter=20, nearRadius=10, correctionStart=60,
correctionSeeds=0. No correction-count cap. These are main.py defaults;
Agent.correctionDuration and stepSimulation fallback still use 110 without matching settings.

## Implementation record

| Commit/change | Scope |
|---|---|
| 161a6b6 | Social rules, strict avoidance, import-safe CLI, tests |
| b4e128e / f2c008c | Superseded changes/placeholder failure; repaired later |
| e69665a | Source repair, configurable correction/spacing |
| 732f8a3 | Original viewer, compact groups, baseline correction defaults |
| f64e8db / f9c79f9 | Avoidance rings/thin arrows; documentation consolidation |
| 79bd57b / ac2168b | Larger agents and pointed no-group diamonds |
| GIF export | Recorded run, combined animation, JSON sidecar; no model-rule changes |

## Limits

```powershell
python -m unittest discover -s tests -v
```

GIF regressions cover copied snapshots, initial/final sampling, mocked-model
result/RNG preservation, and an actual Pillow GIF/JSON write. These do not replace
full-model equivalence tests or live Arcade checks.

- Global NumPy RNG: draw order matters; same seed does not establish cross-version
  reproducibility or serial/parallel equivalence.
- Dense distance/contact matrices: O(N^2) space/work.
- Added social rules and chosen parameters are assumptions, not article validation.
- Historical seed-specific counts are not regression targets or benchmark findings.
- Next: full regression run; live checks; model-only timer; deterministic streams;
  array reference; parallel implementation/equivalence; spatial-index evaluation;
  benchmarks and client feedback log. S=Ts/Tp and E=S/p require comparable timings.
