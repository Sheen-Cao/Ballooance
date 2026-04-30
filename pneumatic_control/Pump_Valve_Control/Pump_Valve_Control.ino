#include <AFMotor.h>

int i = 0;

AF_DCMotor pump1(1, MOTOR12_64KHZ); // create motor #1, 64KHz pwm
AF_DCMotor valve(3, MOTOR12_64KHZ); // create valve, 64KHz pwm
AF_DCMotor pump2(4, MOTOR12_64KHZ); // create motor #2, 64KHz pwm

void setup() {
  Serial.begin(9600);           // set up Serial library at 9600 bps
  Serial.println();
  Serial.println("------");
  Serial.println("Air pouch test!");
  
  pump1.setSpeed(255);     // set the speed to 255/255
  pump2.setSpeed(255);     // set the speed to 255/255
  valve.setSpeed(255);
}

void loop() {
  if (i < 255)
    i = i+1;
  else 
    i = 0;
  Serial.print("test ");
  Serial.println(i);
  
  //inflate
  Serial.print("inflate, 0.8s; ");
  valve.run(FORWARD);      // port 2 & 3 are connected
  pump1.run(FORWARD);      // turn the pump1 on
  pump2.run(RELEASE);      // turn the pump2 off 
  delay(800);

  //hold
  Serial.print("hold, 1s; "); 
  pump1.run(RELEASE);      // turn the pump1 off
  delay(1000);
  
  //deflate
  Serial.print("deflate, 0.8s.");
  pump2.run(FORWARD);      // turn the pump2 on
  valve.run(RELEASE);      // port 1 & 3 are connected
  delay(800);

  //hold
  Serial.println("hold, 1s; "); 
  pump2.run(RELEASE);      // turn the pump2 off
  delay(1000);
  
}
