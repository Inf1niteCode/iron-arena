#!/usr/bin/env python3
# Iron Arena — Battle Simulator Prototype
# Created by: engineering-rapid-prototyper
# Purpose: Standalone working prototype to validate battle formulas before full engine.
# Run: python src/prototypes/battle_prototype.py
# Priority: working code, exact formulas from spec, no DB/Redis dependencies.

import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# EXACT FORMULAS FROM SPEC (no changes allowed)
# ============================================================

def max_hp(health_points: int) -> int:
    return health_points * 10

def max_stamina(stamina: int) -> int:
    return stamina * 10

def dodge_chance(agility: int) -> float:
    return min(agility * 1.5, 40.0)

def calc_damage(strength: int, armor_at_zone: int) -> int:
    return max(0, strength * 2 - armor_at_zone)

def calc_xp_to_level(level: int) -> int:
    return level * 100

def battle_rewards(winner_level: int, loser_level: int):
    return {
        "winner_xp": loser_level * 50,
        "loser_xp": winner_level * 10,
        "winner_gold": loser_level * 20,
        "loser_gold": 0,
    }

# ============================================================
# FIGHTER CLASS
# ============================================================

VALID_ZONES = ["head", "chest", "waist", "legs"]

@dataclass
class Fighter:
    name: str
    level: int = 1
    health_points: int = 5
    stamina: int = 5
    strength: int = 5
    agility: int = 5
    # Armor per zone (simulating equipped items)
    armor: dict = field(default_factory=lambda: {"head": 0, "chest": 0, "waist": 0, "legs": 0})

    def __post_init__(self):
        self.current_hp = max_hp(self.health_points)
        self.current_stamina = max_stamina(self.stamina)

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def get_armor(self, zone: str) -> int:
        return self.armor.get(zone, 0)

    def take_damage(self, dmg: int):
        self.current_hp = max(0, self.current_hp - dmg)

    def dodges(self) -> bool:
        chance = dodge_chance(self.agility)
        return random.uniform(0, 100) < chance

    def choose_move(self) -> tuple[str, str]:
        """AI: random zone selection (prototype simplification)."""
        attack = random.choice(VALID_ZONES)
        defend = random.choice(VALID_ZONES)
        return attack, defend

    def status(self) -> str:
        hp_pct = self.current_hp / max_hp(self.health_points) * 100
        bar = "#" * int(hp_pct // 5) + "." * (20 - int(hp_pct // 5))
        return f"{self.name:15} HP:[{bar}] {self.current_hp:3}/{max_hp(self.health_points)} | Dodge:{dodge_chance(self.agility):.1f}%"

# ============================================================
# BATTLE ENGINE
# ============================================================

def run_battle(fighter1: Fighter, fighter2: Fighter, max_rounds: int = 50, verbose: bool = True) -> dict:
    """
    Run a complete battle between two fighters.
    Returns result dict with winner, rounds, rewards.
    Implements all formulas exactly as specified.
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"  BATTLE: {fighter1.name} vs {fighter2.name}")
        print(f"{'='*60}")
        print(fighter1.status())
        print(fighter2.status())
        print()

    round_num = 0

    for round_num in range(1, max_rounds + 1):
        if not fighter1.is_alive or not fighter2.is_alive:
            break

        # Both choose moves simultaneously
        f1_attack, f1_defend = fighter1.choose_move()
        f2_attack, f2_defend = fighter2.choose_move()

        if verbose:
            print(f"Round {round_num}:")
            print(f"  {fighter1.name}: attack={f1_attack}, defend={f1_defend}")
            print(f"  {fighter2.name}: attack={f2_attack}, defend={f2_defend}")

        # F1 attacks F2
        f2_armor = fighter2.get_armor(f2_attack) if f2_defend == f1_attack else 0
        f2_dodged = fighter2.dodges()
        if f2_dodged:
            f1_damage = 0
            if verbose: print(f"  {fighter2.name} DODGED!")
        else:
            f1_damage = calc_damage(fighter1.strength, f2_armor)
            fighter2.take_damage(f1_damage)
            if verbose: print(f"  {fighter1.name} hits {fighter2.name} for {f1_damage} dmg (armor={f2_armor})")

        # F2 attacks F1
        f1_armor = fighter1.get_armor(f1_attack) if f1_defend == f2_attack else 0
        f1_dodged = fighter1.dodges()
        if f1_dodged:
            f2_damage = 0
            if verbose: print(f"  {fighter1.name} DODGED!")
        else:
            f2_damage = calc_damage(fighter2.strength, f1_armor)
            fighter1.take_damage(f2_damage)
            if verbose: print(f"  {fighter2.name} hits {fighter1.name} for {f2_damage} dmg (armor={f1_armor})")

        if verbose:
            print(f"  >> {fighter1.status()}")
            print(f"  >> {fighter2.status()}")
            print()

        if not fighter1.is_alive or not fighter2.is_alive:
            break

    # Determine winner
    if not fighter1.is_alive and not fighter2.is_alive:
        # Both died same round: higher HP before round wins (tie-break by original HP)
        winner = fighter1 if fighter1.health_points >= fighter2.health_points else fighter2
        loser = fighter2 if winner == fighter1 else fighter1
    elif not fighter2.is_alive:
        winner, loser = fighter1, fighter2
    elif not fighter1.is_alive:
        winner, loser = fighter2, fighter1
    else:
        # Max rounds reached: higher HP wins
        winner = fighter1 if fighter1.current_hp >= fighter2.current_hp else fighter2
        loser = fighter2 if winner == fighter1 else fighter1

    rewards = battle_rewards(winner.level, loser.level)

    if verbose:
        print(f"{'='*60}")
        print(f"  WINNER: {winner.name}!")
        print(f"  Rounds: {round_num}")
        print(f"  Winner XP: +{rewards['winner_xp']}, Gold: +{rewards['winner_gold']}")
        print(f"  Loser XP: +{rewards['loser_xp']}")
        print(f"{'='*60}\n")

    return {
        "winner": winner.name,
        "loser": loser.name,
        "rounds": round_num,
        "rewards": rewards,
    }

# ============================================================
# SIMULATION: Run 1000 battles to validate formula balance
# ============================================================

def run_simulation(n_battles: int = 1000):
    """Validate formula balance: check win rates across different builds."""
    print(f"\nRunning {n_battles} simulation battles...\n")

    builds = [
        # (name, health_points, strength, agility, armor_bonus)
        ("StrengthFighter (str+3)", 5, 8, 5, 0),
        ("AgilityFighter (agi+3)", 5, 5, 8, 0),
        ("TankFighter (hp+3)", 8, 5, 5, 2),
        ("Balanced", 6, 6, 6, 1),
    ]

    results: dict[str, dict[str, int]] = {b[0]: {"wins": 0, "losses": 0} for b in builds}

    for i in range(n_battles):
        b1_def = builds[i % len(builds)]
        b2_def = builds[(i + 1) % len(builds)]

        f1 = Fighter(b1_def[0], level=5, health_points=b1_def[1], strength=b1_def[2], agility=b1_def[3],
                     armor={"head": b1_def[4], "chest": b1_def[4], "waist": b1_def[4], "legs": b1_def[4]})
        f2 = Fighter(b2_def[0], level=5, health_points=b2_def[1], strength=b2_def[2], agility=b2_def[3],
                     armor={"head": b2_def[4], "chest": b2_def[4], "waist": b2_def[4], "legs": b2_def[4]})

        result = run_battle(f1, f2, verbose=False)
        results[result["winner"]]["wins"] += 1
        results[result["loser"]]["losses"] += 1

    print("Simulation Results:")
    print(f"{'Build':<30} {'Wins':>6} {'Losses':>8} {'Win%':>8}")
    print("-" * 55)
    for name, stats in results.items():
        total = stats["wins"] + stats["losses"]
        win_rate = (stats["wins"] / total * 100) if total > 0 else 0
        print(f"{name:<30} {stats['wins']:>6} {stats['losses']:>8} {win_rate:>7.1f}%")


# ============================================================
# FORMULA VERIFICATION TEST
# ============================================================

def verify_formulas():
    """Verify all formulas produce expected values from spec examples."""
    print("\n=== Formula Verification ===")

    # Max HP = health_points * 10
    assert max_hp(5) == 50, f"Expected 50, got {max_hp(5)}"
    assert max_hp(8) == 80, f"Expected 80, got {max_hp(8)}"
    print("max_hp: PASS")

    # Dodge = agility * 1.5, max 40
    assert dodge_chance(5) == 7.5
    assert dodge_chance(8) == 12.0
    assert dodge_chance(30) == 40.0, f"Expected 40.0 (capped), got {dodge_chance(30)}"
    print("dodge_chance: PASS")

    # Damage = strength * 2 - armor
    assert calc_damage(5, 0) == 10
    assert calc_damage(5, 3) == 7
    assert calc_damage(5, 15) == 0, f"Expected 0 (floor), got {calc_damage(5, 15)}"
    print("calc_damage: PASS")

    # XP formula
    assert calc_xp_to_level(1) == 100
    assert calc_xp_to_level(5) == 500
    print("xp_to_level: PASS")

    # Battle rewards
    r = battle_rewards(5, 3)
    assert r["winner_xp"] == 150, f"loser_level(3) * 50 = 150, got {r['winner_xp']}"
    assert r["loser_xp"] == 50, f"winner_level(5) * 10 = 50, got {r['loser_xp']}"
    assert r["winner_gold"] == 60, f"loser_level(3) * 20 = 60, got {r['winner_gold']}"
    assert r["loser_gold"] == 0
    print("battle_rewards: PASS")

    print("\nAll formula verifications PASSED\n")


if __name__ == "__main__":
    # Run formula verification first
    verify_formulas()

    if "--simulate" in sys.argv:
        # Mass simulation for balance testing
        run_simulation(500)
    else:
        # Demo battle
        warrior = Fighter(
            name="IronWarrior",
            level=3, health_points=8, strength=7, agility=5,
            armor={"head": 3, "chest": 5, "waist": 0, "legs": 2},
        )
        mage = Fighter(
            name="ShadowMage",
            level=3, health_points=5, strength=6, agility=8,
            armor={"head": 0, "chest": 2, "waist": 3, "legs": 0},
        )
        result = run_battle(warrior, mage, verbose=True)
        print("Use --simulate to run 500 balance battles")
