// Test de la conversion ADC -> mV du firmware (firmware/esp32_health_monitor/ecg_conversion.h)
//
// Compilation : g++ -I firmware/esp32_health_monitor tests/test_ecg_conversion.cpp -o test_ecg
// Le programme renvoie 1 (échec) si une seule valeur est fausse.
//
// Valeurs attendues calculées à la main avec
//   V      = ADC * 3.3 / 4095
//   V_ECG  = (V - 1.65) / 1100 * 1000   (mV)
//
//   ADC 0     : V = 0          -> (0 - 1.65) / 1.1        = -1.500000 mV  (butée basse)
//   ADC 4095  : V = 3.3        -> (3.3 - 1.65) / 1.1      = +1.500000 mV  (butée haute)
//   ADC 2048  : V = 1.650403   -> 0.000403 / 1.1          = +0.000366 mV  (signal plat)
//   ADC 2047  : V = 1.649597   -> -0.000403 / 1.1         = -0.000366 mV
//   ADC 2100  : V = 1.692308   -> 0.042308 / 1.1          = +0.038462 mV  (pic du Serial Plotter, fig. 3.25)
//   ADC 638   : V = 0.514139   -> -1.135861 / 1.1         = -1.032601 mV  (valeur de la table ecg, fig. 3.17)
//   ADC 2482  : V = 2.000147   -> 0.350147 / 1.1          = +0.318315 mV

#include <cmath>
#include <cstdio>
#include "ecg_conversion.h"

static int erreurs = 0;

static void verifie(int raw, float attendu) {
  const float tolerance = 1e-4f;  // 0,1 µV, largement sous la résolution de l'ADC (~0,7 µV par pas)
  float obtenu = ecgAdcToMillivolts(raw);
  if (std::fabs(obtenu - attendu) > tolerance) {
    std::printf("ECHEC ADC=%4d : obtenu %+.6f mV, attendu %+.6f mV\n", raw, obtenu, attendu);
    erreurs++;
  } else {
    std::printf("ok    ADC=%4d : %+.6f mV\n", raw, obtenu);
  }
}

// Conversion du firmware du mémoire : int ecgValue = analogRead(34) * (3.3 / 4095.0);
// gardée ici pour montrer le bug de troncature (seules les valeurs 0, 1, 2, 3 existent)
static int conversionMemoire(int raw) { return raw * (3.3 / 4095.0); }

static void verifieMemoire(int raw, int attendu) {
  int obtenu = conversionMemoire(raw);
  if (obtenu != attendu) {
    std::printf("ECHEC mémoire ADC=%4d : obtenu %d, attendu %d\n", raw, obtenu, attendu);
    erreurs++;
  }
}

int main() {
  verifie(0, -1.500000f);
  verifie(4095, 1.500000f);
  verifie(2048, 0.000366f);
  verifie(2047, -0.000366f);
  verifie(2100, 0.038462f);
  verifie(638, -1.032601f);
  verifie(2482, 0.318315f);

  // Bug du mémoire : 1240 -> 0,9993 V tronqué à 0 ; 1241 -> 1,0001 V tronqué à 1
  verifieMemoire(1240, 0);
  verifieMemoire(1241, 1);
  verifieMemoire(2100, 1);   // un pic d'ECG devient simplement "1"
  verifieMemoire(4095, 3);

  if (erreurs) {
    std::printf("%d erreur(s)\n", erreurs);
  } else {
    std::printf("Tous les tests de conversion passent\n");
  }
  return erreurs ? 1 : 0;
}
