#define RED_LED     9
#define GREEN_LED   10
#define AUDIO_OUT   11
#define ENCODER_A   2
#define ENCODER_B   3
#define POW_SWITCH  8
#define LIKE_BUT    7
#define POT_IN      A0

void setup()
{
    Serial.begin(115200);

    pinMode(RED_LED, OUTPUT);
    pinMode(GREEN_LED, OUTPUT);

    pinMode(ENCODER_A, INPUT_PULLUP);
    pinMode(ENCODER_B, INPUT_PULLUP);
    pinMode(POW_SWITCH, INPUT_PULLUP);
    pinMode(LIKE_BUT, INPUT_PULLUP);
}

void loop()
{
    Serial.print("POT=");
    Serial.print(analogRead(POT_IN));
    Serial.print(" POW=");
    Serial.print(!digitalRead(POW_SWITCH));
    Serial.print(" LIKE=");
    Serial.print(!digitalRead(LIKE_BUT));
    Serial.print(" A=");
    Serial.print(!digitalRead(ENCODER_A));
    Serial.print(" B=");
    Serial.print(!digitalRead(ENCODER_B));
    Serial.println();
    digitalWrite(RED_LED, HIGH);
    delay(20);
    digitalWrite(GREEN_LED, HIGH);
    delay(20);
    digitalWrite(RED_LED, LOW);
    delay(20);
    digitalWrite(GREEN_LED, LOW);
    delay(100);
}
