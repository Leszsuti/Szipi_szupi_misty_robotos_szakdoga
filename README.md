# Kézikönyv

## Telepítés

Használd a `requirements.txt`-t  a szükséges Python csomagok telepítéséhez.

## Teljesítmény

A SAC eléggé megfingatja a CPU-t. Egy Ryzen 5 5600 esetén a Feladatkezelő szerint körülbelül 4 szálat 90%-on pörgetett.

A virtuális robotka kirajzolását szintén a CPU számolja. Az én processzoromon ez kb. észrevehetetlen terhelést jelentett, de az FPS viszonylag egyszerűen csökkenthető a kódban egyetlen szám átírásával.

Az animáció jelenleg **60 FPS-sel**, a SAC pedig körülbelül **5 FPS-sel** dolgozik.

---

## Virtuális robotkával – kevésbé macerás

### Tanítás

A `lagyszineszkritikus_playground.py` fájlt kell elindítani a zöld nyíllal a tanításhoz.

A kódban található két sor:

```python
# model = SAC.load("misty_sim", env=env)
# model.load_replay_buffer("misty_sim_replay")
```

Ha ezeket kiszeded a kommentből, akkor a legutóbbi modellt tudod továbbtanítani, ha még buta szegény.

A szükséges gombokat a program kiírja a képernyőre.

### Tesztelés

A `_test_playground.py` indításával meg tudod nézni, hogy mit tanult a robot.

### Pálya

A pályát érdemes nem túl kicsire rajzolni, mert a véletlenszerű spawnolás során lehet, hogy a robot a pályán kívülre kerül.

A robotnak lehet segíteni a tanulás elején azzal, hogy a **sárga pöttyöt** a látómezeje bal oldalához közel, de még a látómezőn kívülre helyezed. Így általában gyorsabban megtanulja, hogy érdemes elfordulnia ahhoz, hogy meglássa.

### A virtuális robot érzékelői

* **Távolságszenzorok:** 3 zöld vonal előre, 1 hátra
* **Kamera / látómező:** a kék vonalak által bezárt szög
* **Ütközésérzékelők:** 4 zöld pont a robot sarkain

Ha a robot ütközik, az érzékelő pirosra vált. A robotot a fal sem engedi át.

Tanítás közben ütközés esetén a robot újra spawnol, mivel falnak menni butaság.

(Ennek a leprogramozása közben jöttem rá, hogy miért bugolnak át a karakterek a játékokban a földön, ha gyorsan zuhannak. xd)

---

## Misty robottal

### Csatlakozás

Csatlakoztasd Mistyt a Wi-Fi hálózathoz.

Az útmutató:

https://lessons.mistyrobotics.com/misty-lessons/connect-to-misty

Nekem a pendrive-os, USB-dugogatós módszer működött.

Az `update.py` fájllal tudod tesztelni, hogy sikerült-e csatlakozni.

Ha a program nem áll le, csak fut a végtelenségbe, akkor valami gond van.

### Robot elhelyezése

A robotkának érdemes egy kisebb ketrecet építeni.
A céltárgy lehet bármi, amit a yolo felismer, alapból vizespalack/üveg van neki beállítva, pezsgővel volt tesztelve.

A ketrec legyen:

* legalább olyan magas, hogy a távolságszenzorok hullámai vissza tudjanak verődni róla;
* elég stabil ahhoz, hogy az ütközésérzékelő gombok a robot sarkain ténylegesen benyomódjanak.

### Tanítás

A `lagyszineszkritikus_yolo.py` fájlt kell elindítani a tanításhoz.

A programban **2 fázis** van:

1. az ágens irányítja a robotot;
2. te irányítod a robotot.

Alapból az ágens kezdi el vezetni a robotot.

Ha a robot falnak megy, a program átadja az irányítást neked. Ekkor **WASD** segítségével új helyre kell vezetned a robotot.

Ha szeretnéd, **ESC** megnyomásával visszaadhatod az irányítást az ágensnek.

### Tesztelés

A `_test_yolo.py` fájllal tudod tesztelni, hogy mit tanult az ágens.

### Gombok

| Gomb    | Funkció                           |
| ------- | --------------------------------- |
| **Q**   | Leállítás                         |
| **T**   | Irányítás átvétele                |
| **W**   | Előre                             |
| **A**   | Balra fordulás                    |
| **S**   | Hátra                             |
| **D**   | Jobbra fordulás                   |
| **ESC** | Irányítás visszaadása az ágensnek |

  

