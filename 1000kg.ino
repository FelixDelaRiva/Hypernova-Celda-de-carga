#include "HX711.h"

HX711 scale;

const int DOUT_PIN = 2;
const int CLK_PIN  = 3;

// Variables para cálculo de velocidad
float lastWeight = 0;
unsigned long lastTime = 0;

// --- Filtro de promedio móvil ---
const int samplesForFilter = 5;
float movingWindow[samplesForFilter] = {0};
int windowIndex = 0;
float filteredWeight = 0;

// Histéresis para ignorar pequeños cambios
const float hysteresisThreshold = 0.05; // en kg (50g)

void setup() {
  Serial.begin(115200);
  scale.begin(DOUT_PIN, CLK_PIN);
  scale.set_scale();  // Inicializa sin escala
  scale.tare();
  scale.set_scale(4360.f);  // Calibración real

  lastTime = millis();  // Inicializa tiempo base

  Serial.println("Tiempo (s), Peso (kg), Cambio (kg/s)");
}

void loop() {
  // Leer peso actual
  float weight = scale.get_units(1);  // 1 muestra para velocidad máxima (~1000Hz)

  // Agregar al buffer circular del filtro
  movingWindow[windowIndex] = weight;
  windowIndex = (windowIndex + 1) % samplesForFilter;

  // Calcular promedio móvil
  float sum = 0;
  for (int i = 0; i < samplesForFilter; i++) {
    sum += movingWindow[i];
  }
  float avgWeight = sum / samplesForFilter;

  // Aplicar histéresis
  if (fabs(avgWeight - filteredWeight) > hysteresisThreshold) {
    filteredWeight = avgWeight;
  }

  // Calcular cambio por segundo
  unsigned long now = millis();
  float deltaTime = (now - lastTime) / 1000.0;

  float kg_per_s = 0;
  if (deltaTime > 0) {
    kg_per_s = (filteredWeight - lastWeight) / deltaTime;
  }

  float tiempoSegundos = now / 1000.0;

  // Enviar datos por serial
  Serial.print(tiempoSegundos, 3);
  Serial.print(",");
  Serial.print(filteredWeight, 3);
  Serial.print(",");
  Serial.println(kg_per_s, 3);

  // Actualizar valores anteriores
  lastWeight = filteredWeight;
  lastTime = now;

  delay(1);  // 1000 lecturas por segundo
}
