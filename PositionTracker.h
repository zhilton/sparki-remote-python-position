#include <sparki.h>

struct point {
  float x;
  float y;
};

struct orientation {
  point v1;
  point v2;
};

const float SPARKI_ROTATION_PER_STEP = (WHEEL_DIAMETER_CM * PI / STEPS_PER_REV) / TRACK_WIDTH_CM;
const float COS_THETA = cos(SPARKI_ROTATION_PER_STEP);
const float SIN_THETA = sin(SPARKI_ROTATION_PER_STEP);

class PositionTracker {
  public:
    PositionTracker();
    void update();
    point getCenter();
    float getAngle();
    void setCenter(point newCenter);
    void setAngle(float newAngle);
  private:
    static orientation updateFunction(orientation o, int left, int right);
    orientation currentOrientation;
    int lastTravel[2];
};
