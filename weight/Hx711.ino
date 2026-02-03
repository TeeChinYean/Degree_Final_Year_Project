#include "HX711.h"

#define DOUT 2
#define CLK  3

HX711 scale;

// Use the calibration factor that already works
float calibration_factor = 277.82;

void setup() {
  Serial.begin(9600);

  scale.begin(DOUT, CLK);
  scale.set_scale(calibration_factor);
  scale.tare();              // Zero the scale

  Serial.println("Scale ready.");
}

void loop() {
  if (!scale.is_ready()) {
    delay(50);
    return;
  }

  // Get stable averaged reading
  float weight = scale.get_units(10);

  // Output PURE number only
  Serial.println(weight, 2);

  delay(50);
}
