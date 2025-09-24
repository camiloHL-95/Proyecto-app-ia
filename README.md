Memorice (Pygame)

Pequeño proyecto de Memorice (parejas) con interfaz en Pygame y un agente automático (Greedy / MCTS reducido) para demostrar estrategias de resolución.
La mecánica sigue la regla clásica: levantas una carta, luego otra; si coinciden, quedan emparejadas; si no, se ocultan nuevamente tras un instante.

Contexto

Tablero con pares duplicados (por defecto, 18 pares = 36 cartas).

El objetivo es completar todas las parejas en el menor número de turnos posible.

Incluye dos agentes de ejemplo:

Greedy: usa información conocida para intentar cerrar pares rápidamente.

MCTS (muestreado): evalúa candidatos a partir de muestras aleatorias del tablero desconocido con mini-rollouts.

Requisitos

Python 3.9+

Pygame 2.x

Instalación:
- pip install pygame

Verificar instalación (opciones)

Cualquiera de estas sirve:

- python -m pygame --version

- python -c "import pygame; print(pygame.__version__)"


Ejecución

Asumiendo que tu archivo se llama juego.py (cámbialo si usas otro nombre, p. ej. pg_memorice.py):

- python juego.py


En Windows (PowerShell):

- python .\juego.py


Controles (teclado):

N → Nuevo juego

Espacio → Iniciar / Pausar juego automático

1 → Cambiar a agente Greedy

2 → Cambiar a agente MCTS

Cerrar ventana → Termina la ejecución

Reglas implementadas:

- El agente levanta una primera carta (se muestra su valor).

- Levanta la segunda carta.

- Si coinciden: ambas quedan emparejadas de forma permanente.

- Si no coinciden: ambas se ocultan después de un pequeño delay (para que el intento sea visible).

- El contador de turnos aumenta después de cada par levantado (match o no).
