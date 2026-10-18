#pragma once

// Conversion valeur ADC brute -> amplitude ECG en mV (au niveau des électrodes)
// La sortie de l'AD8232 est centrée sur Vref/2 : il faut retirer cet offset
// avant de diviser par le gain, sinon un signal plat vaut 1,5 mV au lieu de 0.

static const float ADC_VREF = 3.3f;     // tension de référence de l'ADC (V)
static const int   ADC_MAX = 4095;      // ADC 12 bits de l'ESP32
static const float AD8232_GAIN = 1100.0f; // gain total typique du module AD8232

static inline float ecgAdcToMillivolts(int raw) {
  float vMesure = raw * ADC_VREF / ADC_MAX;                  // (1) ADC -> volts
  return (vMesure - ADC_VREF / 2.0f) / AD8232_GAIN * 1000.0f; // (2) offset, gain, mV
}
