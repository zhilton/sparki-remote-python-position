/*
 * Sparki code to accept commands over Bluetooth and respond.
 * Wheel values are sent continuously, other sensor values can be requested.
 * Works in tandem with Sparki.java v.1
 *
 * Zack Butler, Kedarnath Calangutkar, Ruturaj Hagawane, zde
 */
 
#include <Sparki.h>  // include the sparki library
#include "PositionTracker.h"

#define STATUS_OK 0
#define MOVE_FORWARD 1
#define MOVE_LEFT 2
#define MOVE_RIGHT 3
#define SERVO 4
#define REQ_PING 5
#define REQ_WHEELS 6
#define MOVE_STOP 7
#define MOVE_FORWARD_DIST 9
#define REQ_POS 10
#define MOVE_RIGHT_DEG 11
#define MOVE_LEFT_DEG 12
#define SENSE 13
#define UPDATE_POSE 14
#define REQ_3PING 15

#define GOAL_TOLERANCE_CM 0.5
#define RADIUS 8 // radius of landmark
#define BLACK_THRESHOLD 700
#define EPS_T 0.03
#define DIST_TO_FRONT 4
#define DIST_TO_SIDE 4.3
#define ANG_TO_SENS 0.749269314
#define DIST_TO_SENS 5.8728187440

PositionTracker p;

void setup()
{
  Serial1.begin(9600);
  p = PositionTracker();
  sparki.servo(SERVO_CENTER);
}

void sendTravel() {
  Serial1.print(sparki.totalTravel(0));
  Serial1.print(" ");
  Serial1.print(sparki.totalTravel(1));
  Serial1.print("*");
}

void writePosition() {
  Serial1.print(p.getCenter().x);
  Serial1.print(" ");
  Serial1.print(p.getCenter().y);
  Serial1.print(" ");
  Serial1.print(p.getAngle());
  Serial1.print("*");
}

void move_to(point goal) {
  p.update();
  float phi = atan2(goal.y - p.getCenter().y, goal.x - p.getCenter().x); // bearing of goal
  float delta_theta = atan2(sin(phi - p.getAngle()),cos(phi - p.getAngle())); // signed difference between bearing and goal
  if (abs(delta_theta) < EPS_T) // if facing goal -> move forward
      sparki.moveForward();
  else // else turn toward goal
      sparki.moveLeft(delta_theta*RAD_TO_DEG);
}

float dist(point a, point b) {
  return sqrt(sq(b.x - a.x) + sq(b.y - a.y));
}

// spin sparki in the middle of the landmark until it lines up with the tick.
void twirl() {
  sparki.moveLeft();
  while (sparki.lineCenter() > BLACK_THRESHOLD ||
         sparki.lineLeft() > BLACK_THRESHOLD ||
         sparki.lineRight() > BLACK_THRESHOLD) {
    // wait until it's dark
  }
  sparki.moveStop();
  p.update();
}

void senseLandmark() {
  // move forward until either left or right sensor hits
  if (sparki.edgeLeft() > BLACK_THRESHOLD && sparki.edgeRight() > BLACK_THRESHOLD) {
    Serial1.print(0);
    Serial1.print("*");
    return;
  }
  sparki.moveStop();
  p.update();
  point p1, p2;
  boolean leftTripped = false;
  boolean rightTripped = false;
  if (sparki.edgeLeft() <= BLACK_THRESHOLD) { // left sensor was tripped -> record as p1
    p1 = (point) {p.getCenter().x + cos(p.getAngle() + ANG_TO_SENS) * DIST_TO_SENS,
                  p.getCenter().y + sin(p.getAngle() + ANG_TO_SENS) * DIST_TO_SENS};
    leftTripped = true;
  } else if (sparki.edgeRight() <= BLACK_THRESHOLD) { // right sensor was tripped -> record as p1
    p1 = (point) {p.getCenter().x + cos(p.getAngle() - ANG_TO_SENS) * DIST_TO_SENS,
                  p.getCenter().y + sin(p.getAngle() - ANG_TO_SENS) * DIST_TO_SENS};
    rightTripped = true;
  }
  else {  // fucked
    return;
  }
  // keep moving until second sensor hits -> p2
  sparki.moveForward();
  while (!(leftTripped && rightTripped)) {
    if (!rightTripped && (sparki.edgeRight() <= BLACK_THRESHOLD)) {
      sparki.beep();
      rightTripped = true;
      p.update();
      p2 = (point) {p.getCenter().x + cos(p.getAngle() - ANG_TO_SENS) * DIST_TO_SENS,
                  p.getCenter().y + sin(p.getAngle() - ANG_TO_SENS) * DIST_TO_SENS};
    } else if (!leftTripped && (sparki.edgeLeft() <= BLACK_THRESHOLD)) {
      sparki.beep();
      leftTripped = true;
      p.update();
      p2 = (point) {p.getCenter().x + cos(p.getAngle() + ANG_TO_SENS) * DIST_TO_SENS,
                  p.getCenter().y + sin(p.getAngle() + ANG_TO_SENS) * DIST_TO_SENS};
    }
  }

  float q = dist(p1, p2);
  float x3 = (p1.x+p2.x)/2;
  float y3 = (p1.y+p2.y)/2;
  // center of first circle
  float circ_1_x = x3 + sqrt(sq(RADIUS)-sq(q/2))*(p1.y-p2.y)/q;
  float circ_1_y = y3 + sqrt(sq(RADIUS)-sq(q/2))*(p2.x-p1.x)/q; 
  // center of second circle
  float circ_2_x = x3 - sqrt(sq(RADIUS)-sq(q/2))*(p1.y-p2.y)/q;
  float circ_2_y = y3 - sqrt(sq(RADIUS)-sq(q/2))*(p2.x-p1.x)/q; 
  // determine which center in the best
  float phi = atan2(circ_1_y - p.getCenter().y, circ_1_x - p.getCenter().x); // bearing of goal
  float theta_1 = atan2(sin(phi - p.getAngle()),cos(phi - p.getAngle())); // signed difference between bearing and center of first circle
  phi = atan2(circ_2_y - p.getCenter().y, circ_2_x - p.getCenter().x); // bearing of goal
  float theta_2 = atan2(sin(phi - p.getAngle()),cos(phi - p.getAngle())); // signed difference between bearing and center of second circle
  point circ;
  if (abs(theta_1) < abs(theta_2))
    circ = (point) {circ_1_x,circ_1_y};
  else
    circ = (point) {circ_2_x,circ_2_y};
  // move towards center of circ
  while (dist(p.getCenter(), circ) > GOAL_TOLERANCE_CM) 
    move_to(circ);
  // turn until all three sensors hit angle tab
  twirl(); 
  Serial1.print(1);
  Serial1.print("*");
  return;
}

void loop()
{
  if (Serial1.available()) 
  {
    byte opcode = Serial1.read();
    int ping, angle;
    
    switch(opcode) {
      case MOVE_FORWARD:
          sparki.moveForward();
        break;
      case MOVE_FORWARD_DIST:
        {
          float dist = 0;
          char* distbytes = (char* ) &dist;
          for (int i=0; i<=3; i++) {
            while(!Serial1.available());
            distbytes[i] = Serial1.read();
          }
          sparki.moveForward(dist);
        }
        break;
      case MOVE_LEFT:
          sparki.moveLeft();
        break;
      case MOVE_LEFT_DEG:
        {
          float deg = 0;
          char* degbytes = (char* ) &deg;
          for (int i=0; i<=3; i++) {
            while(!Serial1.available());
            degbytes[i] = Serial1.read();
          }
          sparki.moveLeft(deg);
        }
        break;
      case MOVE_RIGHT:
          sparki.moveRight();
        break;
      case MOVE_RIGHT_DEG:
        {
          float deg = 0;
          char* degbytes = (char* ) &deg;
          for (int i=0; i<=3; i++) {
            while(!Serial1.available());
            degbytes[i] = Serial1.read();
          }
          sparki.moveRight(deg);
        }
        break;
      case MOVE_STOP:
          sparki.moveStop();
        break;
      case SERVO:
          while(!Serial1.available());
          angle = Serial1.read();
          angle -= 90;
          sparki.servo(angle);
        break;
      case REQ_PING:
          Serial1.print(sparki.ping());
          Serial1.print("*");
        break;
  		// post condition - sparki is stopped.
  	  case REQ_3PING:
        {
    		  //sparki.moveStop();
    		  sparki.servo(-90);
    		  float v1 = sparki.ping();
    		  delay(200);
    		  sparki.servo(0);
    		  float v2 = sparki.ping();
    		  delay(200);
    		  sparki.servo(90);
    		  float v3 = sparki.ping();
    		  Serial1.print(v1);
          Serial1.print(" ");
    		  Serial1.print(v2);
          Serial1.print(" ");
    		  Serial1.print(v3);
          Serial1.print(" ");
    		  writePosition();
          break;
        }
      case REQ_WHEELS:
          sendTravel();
        break;
      case REQ_POS:
          writePosition();
        break;
      case SENSE:
          senseLandmark();
        break;  
      case UPDATE_POSE:
        {
          float x,y,theta = 0;
          char* xbytes = (char* ) &x;
          char* ybytes = (char* ) &y;
          char* thetabytes = (char* ) &theta;
          for (int i=0; i<=3; i++) {
            while(!Serial1.available());
            xbytes[i] = Serial1.read();
          }
          for (int i=0; i<=3; i++) {
            while(!Serial1.available());
            ybytes[i] = Serial1.read();
          }
          for (int i=0; i<=3; i++) {
            while(!Serial1.available());
            thetabytes[i] = Serial1.read();
          }
          point pt = {x,y};
          p.setCenter(pt);
          p.setAngle(theta);
          break;
        }
      default:
        break;
    }   
	p.update();
  }
}
