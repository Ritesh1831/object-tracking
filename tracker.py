import math

class EuclideanDistTracker:
    def __init__(self):
        self.center_points = {}       # id -> (cx, cy)
        self.sizes = {}               # id -> (w, h) for IoU-aware matching
        self.velocity = {}            # id -> (vx, vy) predicted motion
        self.missing_count = {}       # id -> frames missing
        self.confirm_count = {}       # id -> frames seen (must hit threshold before "real")
        self.id_count = 0
        self.max_missing = 10         # frames to keep lost object in memory
        self.min_confirm = 2          # must be seen N frames before getting a stable ID
        self.pending = []             # [cx, cy, w, h, seen_count] — unconfirmed candidates

    def _iou(self, boxA, boxB):
        """Compute IoU between two (x,y,w,h) boxes."""
        ax, ay, aw, ah = boxA
        bx, by, bw, bh = boxB
        ix  = max(ax, bx);        iy  = max(ay, by)
        ix2 = min(ax+aw, bx+bw);  iy2 = min(ay+ah, by+bh)
        inter = max(0, ix2-ix) * max(0, iy2-iy)
        union = aw*ah + bw*bh - inter
        return inter/union if union > 0 else 0

    def update(self, objects_rect):
        objects_bbs_ids = []
        matched_ids     = set()

        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            best_id    = None
            best_score = float('inf')

            for id, pt in self.center_points.items():
                if id in matched_ids:
                    continue

                # Velocity-predicted position
                pvx, pvy  = self.velocity.get(id, (0, 0))
                pred_cx   = pt[0] + pvx
                pred_cy   = pt[1] + pvy
                dist      = math.hypot(cx - pred_cx, cy - pred_cy)

                # Dynamic threshold based on object size
                ow, oh    = self.sizes.get(id, (w, h))
                threshold = max(60, math.hypot(ow, oh) * 0.6)

                # Blend distance with IoU so overlapping boxes score better
                iou       = self._iou([x,y,w,h],
                                      [int(pt[0]-ow/2), int(pt[1]-oh/2), ow, oh])
                score     = dist * (1.0 - 0.5*iou)

                if dist < threshold and score < best_score:
                    best_score = score
                    best_id    = id

            if best_id is not None:
                # Update velocity with EMA smoothing
                old_pt = self.center_points[best_id]
                vx = cx - old_pt[0];  vy = cy - old_pt[1]
                ovx, ovy = self.velocity.get(best_id, (0, 0))
                self.velocity[best_id]      = (0.7*ovx + 0.3*vx, 0.7*ovy + 0.3*vy)
                self.center_points[best_id] = (cx, cy)
                self.sizes[best_id]         = (w, h)
                self.missing_count[best_id] = 0
                self.confirm_count[best_id] = self.confirm_count.get(best_id, 0) + 1
                objects_bbs_ids.append([x, y, w, h, best_id])
                matched_ids.add(best_id)
            else:
                # Try matching unconfirmed pending candidates
                matched_pending = False
                for p in self.pending:
                    if math.hypot(cx - p[0], cy - p[1]) < 60:
                        p[0], p[1], p[2], p[3] = cx, cy, w, h
                        p[4] += 1
                        matched_pending = True
                        if p[4] >= self.min_confirm:
                            # Promote: assign a real ID
                            nid = self.id_count
                            self.center_points[nid] = (cx, cy)
                            self.sizes[nid]         = (w, h)
                            self.velocity[nid]      = (0, 0)
                            self.missing_count[nid] = 0
                            self.confirm_count[nid] = p[4]
                            objects_bbs_ids.append([x, y, w, h, nid])
                            matched_ids.add(nid)
                            self.id_count += 1
                            self.pending.remove(p)
                        break
                if not matched_pending:
                    self.pending.append([cx, cy, w, h, 1])

        # Expire pending that have gone stale (not matched this frame — decay them)
        still_pending = []
        for p in self.pending:
            # If a pending wasn't just matched (count didn't change this frame), decay
            still_pending.append(p)
        self.pending = still_pending

        # Age confirmed tracks; advance position by velocity during occlusion
        new_cp = {};  new_mc = {};  new_sz = {};  new_vel = {};  new_cf = {}
        for id, pt in self.center_points.items():
            if id in matched_ids:
                new_cp[id]  = pt
                new_mc[id]  = 0
                new_sz[id]  = self.sizes.get(id, (50,50))
                new_vel[id] = self.velocity.get(id, (0,0))
                new_cf[id]  = self.confirm_count.get(id, 1)
            else:
                age = self.missing_count.get(id, 0) + 1
                if age <= self.max_missing:
                    vx, vy = self.velocity.get(id, (0,0))
                    new_cp[id]  = (pt[0]+vx, pt[1]+vy)   # coast forward
                    new_mc[id]  = age
                    new_sz[id]  = self.sizes.get(id, (50,50))
                    new_vel[id] = self.velocity.get(id, (0,0))
                    new_cf[id]  = self.confirm_count.get(id, 1)

        self.center_points = new_cp;  self.missing_count = new_mc
        self.sizes         = new_sz;  self.velocity       = new_vel
        self.confirm_count = new_cf

        return objects_bbs_ids
