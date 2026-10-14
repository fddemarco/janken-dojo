"""Random architectures from the kit's grammar: a population of unknown bots (idea #91).

Research script, not part of the package: `JANKEN_JIT=off uv run python
research/tools/random_pop.py N_L2 N_L3 SEED` writes bots/inactive/random_pop/rand{2,3}_SEED_i.yaml,
keeping only the shapes the kit compiles. The strong half of each seed's population
is kept by a gauntlet vs strong field L1-L2s (research/gauntlet/randpop_*.txt).
"""
import os, random, sys

OUT = "bots/inactive/random_pop"
ROT = ["COPY", "BEAT", "BEAT_BEAT"]
DECAYS = [1.0, 0.98, 0.95, 0.9, 0.85, 0.8]

def block(rng):
    kind = rng.choice(["backoff", "ctw", "frequency", "longest_match", "ngram", "period",
                       "rarest", "relative", "score_state", "second_match", "geometry"])
    of = rng.choice(["OPP", "OPP", "MY"]); ctx = rng.choice(["OPP", "MY", "JOINT"])
    p = {
        "backoff": {"MAX_ORDER": rng.randint(2, 4), "CTX": ctx, "OF": of},
        "ctw": {"DEPTH": rng.randint(1, 3), "CTX": ctx, "OF": of, "DECAY": rng.choice(DECAYS)},
        "frequency": {"OF": of, "DECAY": rng.choice(DECAYS)},
        "longest_match": {"MAX_LEN": rng.randint(4, 20), "CTX": ctx, "OF": of},
        "ngram": {"ORDER": rng.randint(1, 3), "CTX": ctx, "OF": of, "DECAY": rng.choice(DECAYS)},
        "period": {"OF": of, "MAX_PERIOD": rng.randint(4, 16), "DECAY": rng.choice(DECAYS)},
        "rarest": {"OF": of, "DECAY": rng.choice(DECAYS)},
        "relative": {"REF": of, "BY_OUTCOME": rng.randint(0, 1), "DECAY": rng.choice(DECAYS)},
        "score_state": {"OF": of, "DECAY": rng.choice(DECAYS)},
        "second_match": {"MAX_LEN": rng.randint(4, 20), "CTX": ctx, "OF": of},
        "geometry": {"ALPHA": rng.choice([0.02, 0.05, 0.1]), "MAX_LEN": rng.randint(8, 30), "SAMPLE": 1},
    }[kind]
    rots = rng.sample(ROT, rng.randint(2, 3))
    space = ", ".join(f"{k}: {v}" for k, v in p.items())
    return f"{{bot: {kind}, space: {{{space}}}, rotations: [{', '.join(rots)}]}}"

def selection(rng):
    if rng.random() < 0.5:
        return ("Dirichlet", f"scorer: {{Dirichlet: {{decay: {rng.choice([0.99, 0.95, 0.9, 0.85])}}}}}\n      random_arm: RA_SCORED\n      selector: {{Thompson: {{sharp: {rng.choice([1.0, 2.0, 3.0])}}}}}")
    return ("DecayedNet", f"scorer: {{DecayedNet: {{decay: {rng.choice([0.99, 0.95, 0.9, 0.8])}}}}}\n      selector: {{Greedy: {{ties: TIES_RANDOM}}}}")

def write(stem, preds, sel, noise, rng):
    guards = f"  guards: [{{Noise: {{p: {noise}}}}}]\n" if noise else ""
    body = "\n".join(f"        - {p}" for p in preds)
    with open(f"{OUT}/{stem}.yaml", "w") as f:
        f.write(f"description: |\n  Random architecture (research only, never in the field): an unknown opponent sampled from the kit's grammar.\ndefaults: {{}}\nblueprint:\n{guards}  core:\n    Bandit:\n      predictors:\n{body}\n      {sel}\n")

def ok(stem):
    from janken.engine import build
    try:
        build.load_bot(f"{OUT}/{stem}.yaml")
        return True
    except Exception as exc:  # research script: a sampled shape the kit refuses
        print("refused", stem, str(exc)[:100], file=sys.stderr)
        return False

def main(n2, n3, seed):
    os.makedirs(OUT, exist_ok=True); rng = random.Random(seed); l2 = {}
    i = 0
    while len(l2) < n2:
        stem = f"rand2_{seed}_{i}"; i += 1
        kind, sel = selection(rng)
        write(stem, [block(rng) for _ in range(rng.randint(3, 6))], sel, rng.choice([0, 0, 0, 0.03]), rng)
        if ok(stem): l2[stem] = kind
        else: os.remove(f"{OUT}/{stem}.yaml")
    made = 0; i = 0
    while made < n3:
        stem = f"rand3_{seed}_{i}"; i += 1
        kind, sel = selection(rng)
        preds = []
        for arm in rng.sample(sorted(l2), rng.randint(2, 3)):
            est = "estimate: NORMAL" if l2[arm] == "Dirichlet" else "draws: 0"
            side = rng.choice(["MY", "MY", "OPP"])
            rots = ["COPY", "BEAT", "BEAT_BEAT"] if side == "MY" else ["BEAT", "BEAT_BEAT", "COPY"]
            preds.append(f"{{bot: {arm}, side: {side}, {est}, rotations: [{', '.join(rots)}]}}")
        preds += [block(rng) for _ in range(rng.randint(1, 3))]
        write(stem, preds, sel, 0, rng)
        if ok(stem): made += 1
        else: os.remove(f"{OUT}/{stem}.yaml")
    print("made", len(l2), "L2 and", made, "L3")

if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
