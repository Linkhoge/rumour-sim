# Repair and experimental defaults
Replaces the placeholder-only commit with actual Python source. This supersedes
CORRECTOR_DISPLAY.md: correctors have finite, configurable activity (110 steps).
Correction strength is 0.004; correction range is 6 units versus rumour range 4
at n=500. Longer correction activity and increased hearing range strengthen the
previous weak repair candidate without adding agents or imposing a count cap.
Expired correctors retain acceptance but cannot be repeatedly reactivated.
All three settings have CLI options: --correction-strength, --correction-duration,
--correction-radius. No final count or nonzero correction population is guaranteed.
Default seed 42, 500 agents, 400 steps: 33 active correctors, 37 ever corrected.
This is scenario calibration, not empirical validation; other seeds can differ.

Group centres are 25 units from box edges; leash is 20. Both are configurable.
Soft repulsion outside the hard radius and alternate goals reduce edge sticking;
collision-safe tangential fallback remains. Initial overlaps still evacuate.
Pink means friendship/subject, violet ex-friend, red/green outlines active state,
orange an inactive former sharer, grey inactive and pale unaware. Chart remains
400px wide, is 280px tall, with hover counts. Click traces a chain; T toggles
short fading links (off by default), not a persistent tree. Intro is retained.
Explicit rejection is distinct from silent belief. With subjectDenies=1, zero
explicit rejections is expected; the two counters are labelled separately.
Live Arcade behaviour is not verified in the sandbox. Run the full tests locally.
