import math

class EuclideanDistTracker:
    def __init__(self):
        # Store the center positions of the objects
        self.center_points = {}
        # Track how many frames each object has been missing
        self.missing_count = {}
        # Keep the count of the IDs
        self.id_count = 0
        # Max frames to keep a lost object before removing it
        self.max_missing = 5

    def update(self, objects_rect):
        objects_bbs_ids = []
        matched_ids = set()

        # Get center point of new object
        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            same_object_detected = False
            best_id = None
            best_dist = float('inf')

            # Find the closest existing object (instead of first match)
            for id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])
                if dist < 50 and dist < best_dist:  # Increased threshold: 25 → 50
                    best_dist = dist
                    best_id = id

            if best_id is not None:
                self.center_points[best_id] = (cx, cy)
                self.missing_count[best_id] = 0  # Reset missing counter
                objects_bbs_ids.append([x, y, w, h, best_id])
                matched_ids.add(best_id)
                same_object_detected = True

            if not same_object_detected:
                self.center_points[self.id_count] = (cx, cy)
                self.missing_count[self.id_count] = 0
                objects_bbs_ids.append([x, y, w, h, self.id_count])
                matched_ids.add(self.id_count)
                self.id_count += 1

        # Increment missing count for unmatched objects
        for id in list(self.center_points.keys()):
            if id not in matched_ids:
                self.missing_count[id] = self.missing_count.get(id, 0) + 1

        # Only remove objects missing for too long
        new_center_points = {}
        new_missing_count = {}
        for id, pt in self.center_points.items():
            if self.missing_count.get(id, 0) <= self.max_missing:
                new_center_points[id] = pt
                new_missing_count[id] = self.missing_count.get(id, 0)

        self.center_points = new_center_points
        self.missing_count = new_missing_count

        return objects_bbs_ids
