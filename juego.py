# pg_memorice.py
# Ejecutar: python pg_memorice.py
import pygame
import sys
import random
from collections import defaultdict, Counter
import time

# ----------------- Motor y agentes (misma lógica simplificada) -----------------
class MemoryGame:
    def __init__(self, n_pairs=18, seed=None, board=None):
        if seed is not None:
            random.seed(seed)
        self.n_pairs = n_pairs
        self.N = 2*n_pairs
        if board is None:
            vals = list(range(n_pairs))*2
            random.shuffle(vals)
            self.board = vals
        else:
            self.board = board[:]
        self.matched = [False]*self.N      # cartas ya emparejadas (quedan arriba)
        self.revealed = [None]*self.N      # cartas visibles temporalmente (levantadas en este turno)
        self.turns = 0

    def flip_value(self, pos):
        """Devuelve el valor de la carta en pos (no cambia matched).
           El control de revealed/matched lo hace el bucle principal."""
        return self.board[pos]

    def is_done(self):
        return all(self.matched)

class BeliefState:
    def __init__(self, N, n_pairs):
        self.N = N; self.n_pairs = n_pairs
        self.matched = [False]*N
        self.seen = [None]*N
        self.remaining = Counter({v:2 for v in range(n_pairs)})

    def copy(self):
        b = BeliefState(self.N, self.n_pairs)
        b.matched = self.matched[:]; b.seen = self.seen[:]; b.remaining = Counter(self.remaining)
        return b

    def update_from_observation(self, pos, val):
        if self.seen[pos] is None:
            self.remaining[val]-=1
        self.seen[pos]=val

    def known_pair_positions(self):
        inv=defaultdict(list)
        for i,v in enumerate(self.seen):
            if v is not None and not self.matched[i]:
                inv[v].append(i)
        for v,poses in inv.items():
            if len(poses)>=2:
                return poses[0],poses[1],v
        return None

    def unseen_positions(self):
        return [i for i in range(self.N) if (not self.matched[i]) and (self.seen[i] is None)]

    def unmatched_positions(self):
        return [i for i in range(self.N) if not self.matched[i]]

class GreedyAgent:
    def next_action(self, belief):
        kp = belief.known_pair_positions()
        if kp: return kp[0], kp[1]
        unseen = belief.unseen_positions()
        if unseen:
            a = unseen[0]
            b = unseen[1] if len(unseen)>1 else [i for i in belief.unmatched_positions() if i!=a][0]
            return a,b
        um = belief.unmatched_positions(); return um[0], um[1]

# small MCTS like agent (lighter)
class SampledMCTSAgent:
    def __init__(self, n_sims=20, n_rollouts=6):
        self.n_sims = n_sims; self.n_rollouts = n_rollouts
    def _sample_completion(self, belief):
        N = belief.N; board=[None]*N
        for i,v in enumerate(belief.seen):
            if v is not None: board[i]=v
        rem=[]
        for v,c in belief.remaining.items():
            rem.extend([v]*c)
        random.shuffle(rem)
        none_pos=[i for i in range(N) if board[i] is None]
        for i,pos in enumerate(none_pos): board[pos]=rem[i]
        return board
    def _rollout_playout(self, board, start_belief):
        N=start_belief.N; matched=start_belief.matched[:]; seen=start_belief.seen[:]; turns=0
        while not all(matched):
            inv=defaultdict(list)
            for i,v in enumerate(seen):
                if v is not None and not matched[i]: inv[v].append(i)
            did_pair=False
            for v,poses in inv.items():
                if len(poses)>=2:
                    a,b=poses[0],poses[1]; matched[a]=matched[b]=True; turns+=1; did_pair=True; break
            if did_pair: continue
            unseen=[i for i in range(N) if (not matched[i]) and (seen[i] is None)]
            if unseen: a=unseen[0]
            else: a=[i for i in range(N) if not matched[i]][0]
            va=board[a]; seen[a]=va
            others=[i for i in range(N) if seen[i]==va and not matched[i] and i!=a]
            if others: b=others[0]; matched[a]=matched[b]=True; turns+=1; continue
            unseen2=[i for i in range(N) if (not matched[i]) and (seen[i] is None) and i!=a]
            if unseen2: b=unseen2[0]
            else: b=[i for i in range(N) if not matched[i] and i!=a][0]
            vb=board[b]; seen[b]=vb
            if va==vb: matched[a]=matched[b]=True
            turns+=1
        return turns
    def next_action(self, belief):
        kp=belief.known_pair_positions()
        if kp: return kp[0],kp[1]
        unmat=belief.unmatched_positions()
        candidates=[]
        M=min(8,len(unmat)); sub=unmat[:M]
        for i in range(len(sub)):
            for j in range(i+1,len(sub)):
                candidates.append((sub[i],sub[j]))
        if not candidates: return unmat[0],unmat[1]
        totals={c:0.0 for c in candidates}; sims=0
        for s in range(self.n_sims):
            sampled=self._sample_completion(belief)
            sims+=1
            for c in candidates:
                total=0.0
                for r in range(self.n_rollouts):
                    bcopy=belief.copy(); p1,p2=c
                    v1=sampled[p1]; v2=sampled[p2]
                    if bcopy.seen[p1] is None: bcopy.seen[p1]=v1; bcopy.remaining[v1]-=1
                    if bcopy.seen[p2] is None: bcopy.seen[p2]=v2; bcopy.remaining[v2]-=1
                    if v1==v2: bcopy.matched[p1]=bcopy.matched[p2]=True
                    turns=self._rollout_playout(sampled,bcopy)
                    total+=turns
                totals[c]+= total/self.n_rollouts
        best=min(totals.items(), key=lambda x: x[1])[0]
        return best

# ----------------- Pygame UI -----------------
pygame.init()
WIDTH, HEIGHT = 720, 800
FPS = 30
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memorice - Pygame (IA)")
font = pygame.font.SysFont(None, 28)
bigfont = pygame.font.SysFont(None, 36)

cols = 6
tile_size = 100
margin = 10
top_offset = 80

def draw_text(surf, text, pos, color=(0,0,0)):
    img = font.render(text, True, color)
    surf.blit(img, pos)

def run_pygame():
    clock = pygame.time.Clock()
    n_pairs = 18
    game = MemoryGame(n_pairs=n_pairs)
    belief = BeliefState(game.N, n_pairs)

    # agentes
    agent = GreedyAgent()
    agent_type = "Greedy"

    # control
    running = True
    auto = False
    delay_between_flips = 0.35   # tiempo entre carta1 y carta2
    delay_after_mismatch = 0.60  # tiempo que quedan visibles si no coinciden
    last_action_time = 0.0

    # estado de turno (para mostrar/re-ocultar)
    selected = []            # indices revelados en este turno (0,1)
    planned_pair = None      # par planificado por el agente (a,b)
    pending_hide = None      # (a,b) a ocultar después de verlos
    hide_at = None           # timestamp de ocultado

    while running:
        clock.tick(FPS)
        now = time.time()

        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                running=False
            elif ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_SPACE:
                    auto = not auto
                elif ev.key==pygame.K_n:
                    game = MemoryGame(n_pairs=n_pairs); belief = BeliefState(game.N, n_pairs)
                    selected.clear(); planned_pair=None; pending_hide=None; hide_at=None
                elif ev.key==pygame.K_1:
                    agent = GreedyAgent(); agent_type="Greedy"
                elif ev.key==pygame.K_2:
                    agent = SampledMCTSAgent(n_sims=20, n_rollouts=6); agent_type="MCTS"

        # lógica de auto-play con revelar/ocultar
        if auto and not game.is_done():
            # 1) si hay un ocultado pendiente por mismatch y ya pasó el delay, ocúltalo
            if pending_hide and hide_at and now >= hide_at:
                a,b = pending_hide
                # ocultar en tablero (no afectamos matched; sólo visual)
                game.revealed[a] = None
                game.revealed[b] = None
                pending_hide = None
                hide_at = None
                selected.clear()
                # esperamos un poco antes del siguiente primer flip
                last_action_time = now

            # 2) si no hay ocultado pendiente, hacemos la secuencia del turno
            elif not pending_hide and (now - last_action_time >= delay_between_flips):
                # Si no hay ninguna carta levantada en este turno → elegir par y levantar la primera
                if len(selected) == 0:
                    # pedir par al agente (trabaja igual que antes)
                    planned_pair = agent.next_action(belief)
                    a = planned_pair[0]
                    # revelar primera
                    va = game.flip_value(a)
                    game.revealed[a] = va
                    # actualizar creencias
                    if belief.seen[a] is None:
                        belief.seen[a] = va; belief.remaining[va] -= 1
                    selected = [a]
                    last_action_time = now

                # Si ya hay una levantada → levantar la segunda y resolver
                elif len(selected) == 1:
                    a = selected[0]
                    b = planned_pair[1]
                    if b == a:
                        # seguridad (no debería pasar)
                        candidates = [i for i in range(game.N) if not game.matched[i] and i!=a and game.revealed[i] is None]
                        b = candidates[0] if candidates else a

                    vb = game.flip_value(b)
                    game.revealed[b] = vb
                    if belief.seen[b] is None:
                        belief.seen[b] = vb; belief.remaining[vb] -= 1

                    va = game.revealed[a]
                    # resolvemos turno
                    if va == vb and (not game.matched[a]) and (not game.matched[b]):
                        # Match: quedan arriba como emparejadas
                        game.matched[a] = True
                        game.matched[b] = True
                        belief.matched[a] = True
                        belief.matched[b] = True
                        # opcional: ya no necesitamos que sigan en revealed (el render de matched muestra el valor)
                        game.revealed[a] = None
                        game.revealed[b] = None
                        selected.clear()
                        planned_pair = None
                        game.turns += 1
                        last_action_time = now
                    else:
                        # No match: programamos ocultar ambas tras un delay
                        pending_hide = (a, b)
                        hide_at = now + delay_after_mismatch
                        planned_pair = None
                        game.turns += 1
                        # no limpiamos selected aún; se limpia al ocultar
                        last_action_time = now

        # ---- Render ----
        screen.fill((240,240,240))
        draw_text(screen, f"Agente: {agent_type}   (1=Greedy  2=MCTS)   SPACE play/pausa   N nuevo juego", (10,10))
        draw_text(screen, f"Turnos: {game.turns}", (10,40))

        # draw grid
        for i in range(game.N):
            r = i // cols; c = i % cols
            x = margin + c*(tile_size+margin)
            y = top_offset + r*(tile_size+margin)
            rect = pygame.Rect(x,y,tile_size,tile_size)

            if game.matched[i]:
                # emparejada (queda arriba siempre)
                pygame.draw.rect(screen, (180,220,180), rect)
                txt = bigfont.render(str(game.board[i]), True, (20,20,20))
                screen.blit(txt, (x+tile_size//2 - txt.get_width()//2, y+tile_size//2 - txt.get_height()//2))
            else:
                pygame.draw.rect(screen, (200,200,240), rect)
                if game.revealed[i] is not None:
                    # carta visible temporalmente en este turno
                    txt = bigfont.render(str(game.revealed[i]), True, (10,10,10))
                else:
                    txt = bigfont.render("?", True, (10,10,10))
                screen.blit(txt, (x+tile_size//2 - txt.get_width()//2, y+tile_size//2 - txt.get_height()//2))

        if game.is_done():
            draw_text(screen, f"¡Terminado en {game.turns} turnos!  (N = nuevo juego)", (10, HEIGHT-40))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run_pygame()
