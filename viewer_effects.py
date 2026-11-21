"""Drawing-only helpers: thin arrows and avoidance indicators. No model mutations."""
import math
AVOID_RING_COL = (255,95,95,210)
AVOID_RING_WIDTH = 1.4
AVOID_RING_GAP = 4.5

def showsAvoidance(a):
    return bool(a.avoiding) and not a.isSubject

def drawThinArrow(p1,p2,col,width):
    import arcade
    dx,dy = p2[0]-p1[0],p2[1]-p1[1]
    length = math.hypot(dx,dy)
    if length < 1e-6:
        return
    ux,uy = dx/length,dy/length
    inset = min(6.,length*.2)
    start = (p1[0]+inset*ux,p1[1]+inset*uy)
    tip = (p2[0]-inset*ux,p2[1]-inset*uy)
    highlight = tuple(col[:3]) in ((255,214,10),(255,255,255))
    stroke = 1.5 if highlight else 1.0
    alpha = col[3] if len(col) > 3 else 255
    colour = (*col[:3],round(alpha*(.85 if highlight else .65)))
    arcade.draw_line(*start,*tip,colour,stroke)
    head = min(5.,length*.22)
    wing = head*.32
    bx,by = tip[0]-head*ux,tip[1]-head*uy
    arcade.draw_triangle_filled(*tip,bx-wing*uy,by+wing*ux,bx+wing*uy,by-wing*ux,colour)
