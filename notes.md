# Technical notes

Core design and formulas. The project adapts a mobile-agent contagion approach;
friendship, correction, avoidance and related social rules are project extensions,
not claims of faithful article reproduction. Sources: [references.md](references.md).

## Model

Agents occupy one of four states:

$$
\text{Unaware} \rightarrow \text{Spreader or Stifler},
\qquad
\text{Spreader} \rightarrow \text{Stifler or Corrector},
\qquad
\text{Corrector} \rightarrow \text{Stifler}.
$$

A spreader shares the rumour; a corrector shares the correction; a stifler is
inactive. Belief, sharing, friendship and avoidance are separate. Timer expiry
preserves belief. Correction clears belief and avoidance, but does not restore
friendship. Previously corrected stiflers cannot restart correction activity.

The world is a $100 \times 100$ domain with four circular groups. One agent is
the rumour source; one agent is the subject. A fixed number of friends are
selected across groups and no-group agents; some start near the subject.

## Rumour and correction

For recipient $i$, let $g_i$ be gullibility, $o_i$ correction openness, and
$\beta_r,\beta_c$ the rumour and correction strengths. Let $n^r_i$ and $n^c_i$
be the numbers of nearby active spreaders and correctors.

$$
P_r(i)=1-\left(1-g_i\beta_r\right)^{n^r_i}
$$

$$
P_c(i)=1-\left(1-o_i\beta_c\right)^{n^c_i}
$$

These use the complement rule for at least one success among independent
contact opportunities: $P(\text{at least one})=1-\prod_j(1-p_j)$.
[web:461][web:471]

If both messages succeed for an unaware agent, a fair coin selects one. Sender
credit is sampled uniformly from eligible nearby active senders. Transmission
uses a state snapshot, so changes are applied after all recipients are sampled.

An accepted rumour is shared with probability

$$
P(\text{share}\mid\text{rumour accepted})=m+(1-m)s_i,
$$

where $m$ is minimum interest and $s_i$ is sharing tendency. Accepted but
unshared rumour creates a silent believer; failed acceptance leaves the agent
unaware. These sharing and correction rules are project extensions.

The rumour framework follows the ignorant–spreader–stifler structure of the
Maki–Thompson model: spreaders pass rumours to ignorants, while contact with
another spreader or a stifler can stop spreading. [web:463][web:464]

## Friendship and avoidance

On first believing the rumour, a friend ends the friendship with probability

$$
P(\text{friendship ends})=1-\ell_i,
$$

where $\ell_i$ is loyalty. A breakup forces avoidance and ends lingering.
A non-friend begins avoiding with probability $a_i$; loyal friends may remain
nearby. These social rules are project extensions.

Avoidance uses a hard exclusion radius around the subject and a wider soft zone.
For distance $d$ from the subject, with hard radius $r_h$ and outer radius
$r_o$, outward pressure is applied when $r_h<d<r_o$:

$$
\Delta p=\text{step}\cdot\frac{r_o-d}{r_o-r_h}.
$$

## Movement

Initial positions in a group circle use uniform polar sampling:

$$
\theta=2\pi U_1,
\qquad
r=R\sqrt{U_2},
$$

where $U_1$ and $U_2$ are independent uniform samples. The square root makes
the radial distribution uniform by area rather than clustering points near the
centre. [web:462][web:468]

Random walking adds bounded random displacement each step. Group members may
travel between groups, remain for a fixed stay period, then return home.
No-group agents move across the whole domain.

## Update order

Each step updates subject awareness, movement and avoidance, agent timers,
then samples transmission from a snapshot of the old states. Transitions are
applied after sampling, preventing a recipient from spreading within the same
step. The RNG draw order remains sequential in the current serial version.

## Statistics

Let $N_k(t)$ be the number of agents in state $k$ at step $t$:

$$
N_k(t)=\sum_{i=1}^{N}\mathbf{1}\{s_i(t)=k\},
\qquad
\sum_kN_k(t)=N.
$$

Direct recipients of agent $j$ are counted from infector links:

$$
T_j=\sum_{i=1}^{N}\mathbf{1}\{\text{infector}_i=j\}.
$$

This is a direct-transmission count, not downstream reach. Equal counts are
valid; the live viewer still highlights the first listed leader when counts tie.

## Defaults

| Setting | Value | CLI |
|---|---:|---|
| Population / steps / seed | 500 / 400 / 42 | `--n` / `--steps` / `--seed` |
| Centre distance from edges / group radius | 33 / 15 | `--group-spread` / `--leash` |
| Correction strength / duration | 0.03 / 50 | `--correction-strength` / `--correction-duration` |
| Correction radius | Contact radius | `--correction-radius` |
| Avoidance outer-zone multiplier | 1.15 | `--avoid-visual-buffer` |

Contact radius is $4\sqrt{500/N}$. Rumour strength is $0.06$; rumour active
duration is $50$ steps. Other code defaults include step size $1.5$, travel
chance $0.003$, travel speed $2$, stay length $40$, minimum interest $0.5$,
avoidance radius $7$, avoidance chance $0.75$, notice threshold $20$, and
near-subject radius $10$. There is no correction-count cap.

## Limits

```powershell
python -m unittest discover -s tests -v
```

- The global NumPy RNG makes draw order important; the same seed does not
  establish cross-version reproducibility or serial/parallel equivalence.
- Dense distance/contact matrices require $O(N^2)$ space and work.
- Social rules and chosen parameters are experimental assumptions, not
  validation from the source article.
- Historical seed-specific counts are not regression targets or benchmark results.

## Outstanding work

- [x] Agents, groups, no-group agents, movement, visiting
- [x] Rumour + correction spread, stifling
- [x] Live window + headless mode + plots
- [ ] Seeded RNG per (seed, step, agent)
- [ ] NumPy array version
- [ ] Parallel version (Numba)
- [ ] Serial vs parallel equivalence test
- [ ] Benchmarks (absolute time, speed-up, efficiency)
