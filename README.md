INTEGRANTES: CAMILO HERRERA - VICTOR MARDONES - DEBORA LEAL

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

1) Instalación:
- pip install pygame

Verificar instalación (opciones)

Cualquiera de estas sirve:

- python -m pygame --version

- python -c "import pygame; print(pygame.__version__)"


2) Ejecución

Asumiendo que tu archivo se llama juego.py (cámbialo si usas otro nombre, p. ej. pg_memorice.py):

- python juego.py


En Windows (PowerShell):

- python .\juego.py


3) Controles (teclado):

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


Implementamos dos estrategias de búsqueda: (i) Greedy, una política informada localmente que cierra pares conocidos y, en su defecto, revela posiciones no vistas para maximizar información; y (ii) Sampled MCTS, que estima la calidad de las jugadas mediante muestreos del tablero desconocido y rollouts de finalización, eligiendo el par inicial que minimiza los turnos esperados. Probamos ambos agentes en múltiples partidas dentro del entorno Pygame, observando métricas de turnos por episodio y ajustando los parámetros de simulación para evaluar el trade-off entre rendimiento y coste computacional.


4) Arquitectura y partes importantes del código
4.1. MemoryGame

Representa el entorno (tablero real):

board: arreglo con los valores de las cartas (dos copias por cada valor).

matched[i]: True si la carta de la posición i ya está emparejada (permanece visible).

revealed[i]: valor visible temporalmente en el turno actual (se oculta si fue un intento fallido).

turns: contador de turnos (aumenta al voltear el par del turno).

Métodos clave:

flip_value(pos): devuelve el valor real de la carta (la lógica de mostrar/ocultar se controla en el bucle principal).

is_done(): indica si todas las parejas están resueltas.

Nota: Separar matched (estado permanente) de revealed (estado temporal) permite aplicar correctamente la regla “si no coinciden, se ocultan”.

4.2. BeliefState

Modelo de conocimiento del agente (lo que recuerda del tablero):

seen[i]: valor observado en i (o None si nunca se levantó esa carta).

matched[i]: lo que el agente cree que ya quedó emparejado.

remaining: contador de copias faltantes por valor (desde 2 hacia 0).

Funciones de apoyo:

update_from_observation(pos, val): actualiza memoria y descuenta en remaining.

known_pair_positions(): devuelve un par de posiciones ya conocidas (si existen).

unseen_positions() / unmatched_positions(): ayudan a proponer jugadas.

4.3. Bucle principal (Pygame)

Controla el ciclo de turnos con las variables:

selected: primera carta levantada del turno.

planned_pair: par (a,b) sugerido por el agente.

pending_hide / hide_at: programan el ocultado de las dos cartas cuando no coinciden (tras un breve delay).

Secuencia por turno:

Levanta primera carta (revealed[a] = valor), actualiza BeliefState.

Levanta segunda carta (revealed[b] = valor), actualiza BeliefState.

Match → marca matched[a]=matched[b]=True, incrementa turns, limpia revelados temporales.
No match → programa ocultado de a y b tras el retardo; incrementa turns.

Render:

Cartas emparejadas (fondo verde) muestran el valor siempre.

Cartas en intento (fondo azul) muestran revealed.

Cartas ocultas muestran “?”.

5) Algoritmos de búsqueda implementados
5.1. GreedyAgent (búsqueda voraz informada por memoria)

Idea: tomar una decisión “mejor localmente” con la información disponible, sin planificar a largo plazo.

Regla:

Si el agente conoce un par (dos posiciones con el mismo valor aún no emparejado), lo cierra.

Si no hay par conocido, elige cartas no vistas para maximizar información (descubrir valores nuevos y habilitar pares futuros).

Naturaleza de la búsqueda: voraz/local; no expande el árbol global de estados.
Ventajas: simple, rápida, robusta.
Limitaciones: puede ser subóptima; no evalúa consecuencias a varios turnos vista.

5.2. SampledMCTSAgent (Monte Carlo muestreado, versión ligera)

Idea: aproximar una evaluación a futuro por simulación sin construir el árbol completo.

Pasos:

Muestreo del tablero desconocido: completa las posiciones no vistas con valores plausibles consistentes con remaining.

Candidatos de jugada: genera un subconjunto de pares (a,b) posibles.

Rollouts: para cada candidato y para varios tableros muestreados, simula terminar la partida con una política simple (cerrar pares conocidos y seguir revelando). Registra turnos usados.

Selección: elige el candidato con menor número de turnos esperados (promedio de simulaciones).

Naturaleza: búsqueda informada estocástica (Monte Carlo).
Ventajas: introduce “mirada a futuro”; se adapta a la incertidumbre.
Limitaciones: mayor coste computacional; la calidad depende de n_sims y n_rollouts.

6) Cómo se probaron los algoritmos
6.1. Pruebas funcionales

Interactivas (Pygame): Reiniciar varias veces (N) y observar que siempre se completa el tablero respetando la regla “levanto-levanto-match/oculto”.

Cambio de agente en vivo: Alternar con 1 (Greedy) y 2 (MCTS) y observar diferencias de comportamiento.

6.2. Métrica de evaluación

Turnos totales para completar el tablero (ya se muestra en pantalla).

Para evaluación más sólida: repetir varias partidas por agente (p. ej., 30–50) y comparar promedio y desviación de turnos.

6.3. Condiciones de experimento sugeridas

Mantener el mismo tamaño de tablero (por defecto 18 pares = 36 cartas).

Opcional: inicializar con una semilla fija en MemoryGame(seed=...) para comparar agentes sobre el mismo barajado.

Probar distintas configuraciones de MCTS: n_sims (número de tableros muestreados) y n_rollouts (simulaciones por tablero).

7) Tiempos de ejecución
7.1. Definición y medición

En este proyecto distinguimos:

Tiempo de juego “humano” (con render Pygame): influye el dibujo y los delays intencionales (para ver cartas), no sirve como benchmark puro del algoritmo.

Tiempo del algoritmo: lo ideal es medir sin render ni delays. Aun así, se puede estimar el tiempo total de resolución incluyendo la IU.

Medición práctica (con IU):

Medir tiempo desde el inicio del autoplay hasta is_done():

Al presionar Espacio para iniciar, guardar t0 = time.perf_counter().

Cuando game.is_done() pasa a True, calcular elapsed = time.perf_counter() - t0 y mostrarlo (por ejemplo junto a “Turnos:”).

Repetir varias veces y promediar. Nota: este tiempo incluye render y delays, por lo que es bueno para una métrica “de usuario”, no para micro-benchmark.

Medición justa del algoritmo (opcional, sin IU):

Ejecutar la lógica del agente en un bucle sin Pygame ni pauses (modo headless), midiendo con time.perf_counter().

Comparar Greedy vs MCTS variando n_sims/n_rollouts.
