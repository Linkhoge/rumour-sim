# Original viewer restoration
Supersedes the viewer and scenario defaults in VIEWER_UPDATES.md.
Restores the original Arcade design from b4e128e: Consolas/Menlo font stack,
glow sprites, pulse rings, diamonds for ungrouped agents, group colours,
patient-zero/subject markers, top-spreader labels, statistics, latest-pass log,
T persistent arrows, G hop colours, F newest gold chain, H group rings, S sizes,
click-to-trace and the intro. These features are not replaced by another viewer.

Targeted changes retained: pale unaware / grey inactive, violet ex-friends with
active-state outlines, orange former sharers, and a 400x220 chart with hover
counts. Three top-spreader and three recent-pass rows are visible to leave room
for the taller chart and controls; full top-five tracking and recent log remain.

Restores default group centres (33,33),(67,33),(33,67),(67,67) and radius 15.
Correction defaults return to strength .03, active duration 50, hearing range
equal to rumour contact range (4 at n=500). All remain configurable and uncapped.
No counts are forced. This is not an exact model rollback: the current avoidance
improvements, social traits and prevention of expired-corrector reactivation
remain. Thus remembered counts (74 unaware, 0 spreaders, 2 correctors) are not
promised. A full live Arcade visual check is still required.
