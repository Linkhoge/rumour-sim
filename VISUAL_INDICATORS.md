# Small visual-only update
The original viewer, font, panels, intro, T arrows and gold chains are unchanged
in structure. FriendshipWindow substitutes a thinner arrow drawing primitive:
1px transmission lines, 1.5px gold/white chains, smaller arrowheads, lower opacity
and 6px endpoint inset (scaled down for short links). No timing or chain changes.
A steady red outer ring marks a.avoiding, excluding the subject. The existing
centre colours and active-state friendship outlines remain. The ring follows
the displayed node radius and disappears when avoidance stops, including after
correction. Believers who are not avoiding do not receive this indicator.
No simulation settings, rates, group sizes or movement rules are changed.
Six focused helper/mock-draw tests pass; live Arcade rendering is not verified.
