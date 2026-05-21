char command;

int IN1 = 8;
int IN2 = 9;
int IN3 = 10;
int IN4 = 11;

void setup() {

  Serial.begin(9600);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
}

void loop() {

  if (Serial.available()) {

    command = Serial.read();

    // FORWARD
    if (command == 'F') {

      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);

      digitalWrite(IN3, HIGH);
      digitalWrite(IN4, LOW);
    }

    // LEFT
    else if (command == 'L') {

      digitalWrite(IN1, LOW);
      digitalWrite(IN2, LOW);

      digitalWrite(IN3, HIGH);
      digitalWrite(IN4, LOW);

      delay(300);
    }

    // RIGHT
    else if (command == 'R') {

      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);

      digitalWrite(IN3, LOW);
      digitalWrite(IN4, LOW);

      delay(300);
    }

    // STOP
    else if (command == 'S') {

      digitalWrite(IN1, LOW);
      digitalWrite(IN2, LOW);

      digitalWrite(IN3, LOW);
      digitalWrite(IN4, LOW);
    }
  }
}
