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
int lastPowState = -1;


void timerIsr()
{
  encoder->service();
}

void checkPowerState()
{
    int state;

    bouncer.update();
    state = bouncer.read();
    if (state != lastPowState) {
        Serial.print("P:");
        Serial.println(!state);
    }
    lastPowState = state;
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
}
