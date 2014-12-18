#define RED_LED     9
#define GREEN_LED   10
#define AUDIO_OUT   11
#define ENCODER_A   2
#define ENCODER_B   3
#define POW_SWITCH  8
#define LIKE_BUT    7
#define POT_IN      A0

#include <ClickEncoder.h>
#include <TimerOne.h>
#include <Bounce.h>

ClickEncoder *encoder;
ClickEncoder::Button lastBtnState = encoder->getButton();

Bounce bouncer = Bounce(POW_SWITCH, 20); 


void timerIsr()
{
  encoder->service();
}

void checkPowerState()
{
    static int8_t lastPowState = -1;
    int8_t state;

    bouncer.update();
    state = bouncer.read();
    if (state != lastPowState) {
        Serial.print("P:");
        Serial.println(!state);
    }
    lastPowState = state;
}

uint16_t getPotValue()
{
    uint16_t sum = 0;

    for (uint8_t i = 0 ; i < 5 ; ++i) {
        sum += analogRead(POT_IN);
        delay(1);
    }

    return sum / 5;
}

void checkPot()
{
    static int lastLevel = -1;
    int currentLevel = constrain(map(getPotValue(), 0, 1023, 0, 100), 0, 100);

    if (lastLevel != currentLevel) {
        Serial.print("V:");
        Serial.println(currentLevel);
        lastLevel = currentLevel;
    }
}

void setup()
{
    Serial.begin(115200);
    encoder = new ClickEncoder(ENCODER_B, ENCODER_A, LIKE_BUT);

    Timer1.initialize(1000);
    Timer1.attachInterrupt(timerIsr); 

    encoder->setAccelerationEnabled(true);

    pinMode(POW_SWITCH, INPUT_PULLUP);
}

void loop()
{
    int16_t encDelta = encoder->getValue();

    if (encDelta != 0) {
        Serial.print("E:");
        Serial.println(encDelta);
    }

    ClickEncoder::Button b = encoder->getButton();
    if (b != ClickEncoder::Open && b != lastBtnState) {
        Serial.print("B:");
        Serial.println(b);
    }
    lastBtnState = b;

    checkPowerState();
    checkPot();
}
