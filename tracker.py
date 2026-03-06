import math

class EuclideanDistTracker:
    def __init__(self):
        self.center_points = {}
        self.missing_count = {}
        self.id_count = 0
        self.max_missing = 8  # frames before an ID is retired

    def update(self, objects_rect):
        objects_bbs_ids = []
        matched_ids = set()  # prevent one ID from being claimed twice in same frame

        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            best_id = None
            best_dist = float('inf')

            for id, pt in self.center_points.items():
                if id in matched_ids:          # KEY FIX: skip already-claimed IDs
                    continue
                dist = math.hypot(cx - pt[0], cy - pt[1])
                if dist < 60 and dist < best_dist:
                    best_dist = dist
                    best_id = id

            if best_id is not None:
                self.center_points[best_id] = (cx, cy)
                self.missing_count[best_id] = 0
                objects_bbs_ids.append([x, y, w, h, best_id])
                matched_ids.add(best_id)
            else:
                # Brand-new object
                self.center_points[self.id_count] = (cx, cy)
                self.missing_count[self.id_count] = 0
                objects_bbs_ids.append([x, y, w, h, self.id_count])
                matched_ids.add(self.id_count)
                self.id_count += 1

        # Age out unmatched objects — do NOT emit ghost boxes for them
        new_center_points = {}
        new_missing_count = {}
        for id, pt in self.center_points.items():
            if id in matched_ids:
                new_center_points[id] = pt
                new_missing_count[id] = 0
            else:
                age = self.missing_count.get(id, 0) + 1
                if age <= self.max_missing:
                    new_center_points[id] = pt   # keep in memory for re-match
                    new_missing_count[id] = age  # but don't draw a box for it

        self.center_points = new_center_points
        self.missing_count = new_missing_count

        return objects_bbs_ids  # only contains boxes for VISIBLE detections
