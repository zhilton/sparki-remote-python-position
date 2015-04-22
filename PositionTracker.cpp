#include "PositionTracker.h"

PositionTracker::PositionTracker() {
  currentOrientation.v1.x = -TRACK_WIDTH_CM/2;
  currentOrientation.v1.y = 0;
  currentOrientation.v2.x = TRACK_WIDTH_CM/2;
  currentOrientation.v2.y = 0;
  lastTravel[0] = 0;
  lastTravel[1] = 0;
}

orientation PositionTracker::updateFunction(orientation prev, int left, int right) {
  orientation cur = prev;
    while (left != 0 || right != 0) {
      if (right != 0) {
        int sign = (right > 0) - (right < 0);
        point diff = {cur.v2.x - cur.v1.x, cur.v2.y - cur.v1.y};
        point rotated = {COS_THETA*diff.x + sign*-SIN_THETA*diff.y,
                         sign*SIN_THETA*diff.x + COS_THETA*diff.y};
        cur.v2.x = cur.v1.x + rotated.x;
        cur.v2.y = cur.v1.y + rotated.y;
        right -= sign;
      }
      if (left != 0) {
        int sign = (left > 0) - (left < 0);
        point diff = {cur.v1.x - cur.v2.x, cur.v1.y - cur.v2.y};
        point rotated = {COS_THETA*diff.x + sign*SIN_THETA*diff.y,
                         sign*-SIN_THETA*diff.x + COS_THETA*diff.y};
        cur.v1.x = cur.v2.x + rotated.x;
        cur.v1.y = cur.v2.y + rotated.y;
        left -= sign;
      }
    }
    return cur;
}

void PositionTracker::update() {
  int curTravel[2] = {sparki.totalTravel(0), sparki.totalTravel(1)};
  currentOrientation = updateFunction(currentOrientation, curTravel[0]-lastTravel[0], curTravel[1]-lastTravel[1]);
  lastTravel[0] = curTravel[0];
  lastTravel[1] = curTravel[1];
}

orientation PositionTracker::getOrientation() {
  return currentOrientation;
}

point PositionTracker::getCenter() {
  point p = {(currentOrientation.v1.x + currentOrientation.v2.x)/2, (currentOrientation.v1.y + currentOrientation.v2.y)/2};
  return p;
}

float PositionTracker::getAngle() {
  return atan2(currentOrientation.v2.y - currentOrientation.v1.y,
               currentOrientation.v2.x - currentOrientation.v1.x);
}
