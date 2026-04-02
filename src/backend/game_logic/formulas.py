# Iron Arena — Game Formulas
# Created by: engineering-backend-architect
# Purpose: ALL game formulas from mvp-setup.md implemented EXACTLY as specified.
# This is the single source of truth for all calculations.
# Senior Developer WebSocket engine MUST use these functions, not duplicate logic.

import random
from dataclasses import dataclass


# ============================================================
# STAT FORMULAS (from spec)
# ============================================================

def calc_max_hp(health_points: int) -> int:
    """Max HP = health_points * 10 (exact formula from spec)."""
    return health_points * 10


def calc_max_stamina(stamina: int) -> int:
    """Max stamina = stamina * 10."""
    return stamina * 10


def calc_dodge_chance(agility: int) -> float:
    """Dodge chance = agility * 1.5, capped at 40% (exact formula from spec)."""
    return min(agility * 1.5, 40.0)


def calc_xp_to_next_level(level: int) -> int:
    """XP required for next level = level * 100 (exact formula from spec)."""
    return level * 100


# ============================================================
# RECOVERY FORMULAS (from spec)
# ============================================================

def calc_hp_recovery_per_minute(health_points: int) -> int:
    """HP recovery = 10% of max_hp per minute (exact formula from spec)."""
    max_hp = calc_max_hp(health_points)
    return max(1, int(max_hp * 0.10))


def calc_stamina_recovery_per_minute(stamina: int) -> int:
    """Stamina recovery = 20% of max_stamina per minute (exact formula from spec)."""
    max_stamina = calc_max_stamina(stamina)
    return max(1, int(max_stamina * 0.20))


# ============================================================
# BATTLE DAMAGE FORMULA (from spec)
# ============================================================

def calc_damage(attacker_strength: int, defender_armor_at_zone: int) -> int:
    """
    Damage = strength * 2 - armor_of_attacked_zone (exact formula from spec).
    Minimum damage is 0 (cannot heal opponent).
    """
    raw = attacker_strength * 2 - defender_armor_at_zone
    return max(0, raw)


def roll_dodge(agility: int) -> bool:
    """
    Roll whether the defender dodges.
    Dodge probability = agility * 1.5%, max 40%.
    Returns True if the attack is dodged.
    """
    chance = calc_dodge_chance(agility)
    return random.uniform(0, 100) < chance


# ============================================================
# BATTLE REWARDS (from spec)
# ============================================================

@dataclass
class BattleRewards:
    winner_xp: int
    loser_xp: int
    winner_gold: int
    loser_gold: int = 0


def calc_battle_rewards(winner_level: int, loser_level: int) -> BattleRewards:
    """
    Battle rewards (exact formulas from spec):
    - Winner XP = loser_level * 50
    - Loser XP = winner_level * 10
    - Winner gold = loser_level * 20
    - Loser gold = 0
    """
    return BattleRewards(
        winner_xp=loser_level * 50,
        loser_xp=winner_level * 10,
        winner_gold=loser_level * 20,
        loser_gold=0,
    )


# ============================================================
# LEVEL UP LOGIC
# ============================================================

def check_level_up(current_level: int, current_xp: int) -> tuple[int, int]:
    """
    Check if player levels up and return (new_level, remaining_xp).
    Processes multiple level-ups in one call.
    """
    level = current_level
    xp = current_xp
    while xp >= calc_xp_to_next_level(level):
        xp -= calc_xp_to_next_level(level)
        level += 1
    return level, xp


# ============================================================
# AUCTION FEE (from spec)
# ============================================================

AUCTION_FEE_RATE = 0.05  # 5% platform fee


def calc_auction_seller_payout(final_price: int) -> int:
    """
    Seller receives final_price * 0.95 (5% platform fee).
    Exact formula from spec. Rounds down.
    """
    return int(final_price * (1 - AUCTION_FEE_RATE))


# ============================================================
# BATTLE ROUND PROCESSING
# ============================================================

@dataclass
class RoundResult:
    # Attacker 1 perspective
    p1_attack_zone: str
    p1_defend_zone: str
    p1_damage_dealt: int
    p1_dodged_by_p2: bool    # True if p2 dodged p1's attack

    # Attacker 2 perspective
    p2_attack_zone: str
    p2_defend_zone: str
    p2_damage_dealt: int
    p2_dodged_by_p1: bool    # True if p1 dodged p2's attack

    # Updated HP after round
    p1_hp_after: int
    p2_hp_after: int


def process_round(
    p1_strength: int,
    p1_agility: int,
    p1_hp: int,
    p1_attack_zone: str,
    p1_defend_zone: str,
    p1_armor_at_zone: int,  # armor value of item defending p1_defend_zone

    p2_strength: int,
    p2_agility: int,
    p2_hp: int,
    p2_attack_zone: str,
    p2_defend_zone: str,
    p2_armor_at_zone: int,  # armor value of item defending p2_defend_zone
) -> RoundResult:
    """
    Process one battle round with both players' moves simultaneously.
    Applies damage formula: Damage = strength * 2 - armor_of_attacked_zone
    Applies dodge formula: Dodge (%) = agility * 1.5, max 40%

    The armor is only applied if the defender chose to defend the zone being attacked.
    If attacker targets a zone the defender isn't protecting -> 0 armor applies.
    """
    # P1 attacks P2
    p2_effective_armor = p2_armor_at_zone if p2_defend_zone == p1_attack_zone else 0
    p2_dodged = roll_dodge(p2_agility)
    if p2_dodged:
        p1_damage = 0
    else:
        p1_damage = calc_damage(p1_strength, p2_effective_armor)

    # P2 attacks P1
    p1_effective_armor = p1_armor_at_zone if p1_defend_zone == p2_attack_zone else 0
    p1_dodged = roll_dodge(p1_agility)
    if p1_dodged:
        p2_damage = 0
    else:
        p2_damage = calc_damage(p2_strength, p1_effective_armor)

    # Apply damage (HP cannot go below 0)
    p2_hp_after = max(0, p2_hp - p1_damage)
    p1_hp_after = max(0, p1_hp - p2_damage)

    return RoundResult(
        p1_attack_zone=p1_attack_zone,
        p1_defend_zone=p1_defend_zone,
        p1_damage_dealt=p1_damage,
        p1_dodged_by_p2=p2_dodged,
        p2_attack_zone=p2_attack_zone,
        p2_defend_zone=p2_defend_zone,
        p2_damage_dealt=p2_damage,
        p2_dodged_by_p1=p1_dodged,
        p1_hp_after=p1_hp_after,
        p2_hp_after=p2_hp_after,
    )
