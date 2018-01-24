###
### Generated by QuakeC -> Python translator
### Id: qc2python.py,v 1.5 2001/02/05 21:15:44 barryp Exp 
###
### 2001-02-17 Cleaned up translation (barryp)
###
from qwpython.qwsv import engine, Vector
from qwpython.qcsupport import qc

import defs
import client
import subs
import weapons
import teamplay
import math

# 
# ============
# CanDamage
# 
# Returns true if the inflictor can directly damage the target.  Used for
# explosions and melee attacks.
# ============
# 
def CanDamage(targ, inflictor, *qwp_extra):
    #  bmodels need special checking because their origin is 0,0,0
    if targ.movetype == defs.MOVETYPE_PUSH:
        qc.traceline(inflictor.origin, 0.5 * (targ.absmin + targ.absmax), defs.TRUE, qc.self)
        if qc.trace_fraction == 1:
            return defs.TRUE
        if qc.trace_ent == targ:
            return defs.TRUE
        return defs.FALSE
        
    qc.traceline(inflictor.origin, targ.origin, defs.TRUE, qc.self)
    if qc.trace_fraction == 1:
        return defs.TRUE
    qc.traceline(inflictor.origin, targ.origin + Vector(15, 15, 0), defs.TRUE, qc.self)
    if qc.trace_fraction == 1:
        return defs.TRUE
    qc.traceline(inflictor.origin, targ.origin + Vector(-15, -15, 0), defs.TRUE, qc.self)
    if qc.trace_fraction == 1:
        return defs.TRUE
    qc.traceline(inflictor.origin, targ.origin + Vector(-15, 15, 0), defs.TRUE, qc.self)
    if qc.trace_fraction == 1:
        return defs.TRUE
    qc.traceline(inflictor.origin, targ.origin + Vector(15, -15, 0), defs.TRUE, qc.self)
    if qc.trace_fraction == 1:
        return defs.TRUE
    return defs.FALSE

    
# 
# ============
# Killed
# ============
# 
def Killed(targ, attacker, *qwp_extra):
    oself = qc.self
    qc.self = targ
    if qc.self.health < -99:
        qc.self.health = -99 #  don't let sbar look bad if a player
    if qc.self.movetype == defs.MOVETYPE_PUSH or qc.self.movetype == defs.MOVETYPE_NONE:
        #  doors, triggers, etc
        qc.self.th_die()
        qc.self = oself
        return 
        
    qc.self.enemy = attacker
    #  bump the monster counter
    if qc.self.flags & defs.FL_MONSTER:
        qc.killed_monsters += 1
        qc.WriteByte(defs.MSG_ALL, defs.SVC_KILLEDMONSTER)
        
    client.ClientObituary(qc.self, attacker)
    qc.self.takedamage = defs.DAMAGE_NO
    qc.self.touch = subs.SUB_Null
    qc.self.effects = 0
    # SERVER
    # 	monster_death_use();
    # 
    qc.self.th_die()
    qc.self = oself

    
#  *TEAMPLAY*
#  Prototypes
# 
# ============
# T_Damage
# 
# The damage is coming from inflictor, but get mad at attacker
# This should be the only function that ever reduces health.
# ============
# 
def T_Damage(targ, inflictor, attacker, damage, *qwp_extra):
    if not targ.takedamage:
        return 
    #  used by buttons and triggers to set activator for target firing
    defs.damage_attacker = attacker
    #  check for quad damage powerup on the attacker
    if attacker.super_damage_finished > qc.time:
        damage *= 4
    #  RUNE: check for double damage for rune of Black Magic powerup
    if attacker.player_flag & defs.ITEM_RUNE2_FLAG:
        damage *= 2
    #  RUNE
    # RUNE check if target has rune of Earth Magic (half damage)
    if targ.player_flag & defs.ITEM_RUNE1_FLAG:
        damage /= 2
        weapons.ResistanceSound(targ)
        
    # RUNE
    #  *XXX* EXPERT CTF mark players who hurt the flag carrier, so they 
    #  are worth more points for a while.
    if (attacker.classname == 'player') and (targ.player_flag & defs.ITEM_ENEMY_FLAG) and (attacker.steam != targ.steam): #  target and attacker on diff teams
        attacker.last_hurt_carrier = qc.time
    #  save damage based on the target's armor level
    #  *TEAMPLAY*
    #  TeamArmorDam returns true iff the attacker can damage the target's armor
    if teamplay.TeamArmorDam(targ, inflictor, attacker, damage):
        save = math.ceil(targ.armortype * damage)
    else:
        save = 0
    if save >= targ.armorvalue:
        save = targ.armorvalue
        targ.armortype = 0 #  lost all armor
        targ.items -= targ.items & (defs.IT_ARMOR1 | defs.IT_ARMOR2 | defs.IT_ARMOR3)
        
    targ.armorvalue -= save
    take = math.ceil(damage - save)
    #  add to the damage total for clients, which will be sent as a single
    #  message at the end of the frame
    #  FIXME: remove after combining shotgun blasts?
    if targ.flags & defs.FL_CLIENT:
        targ.dmg_take += take
        targ.dmg_save += save
        targ.dmg_inflictor = inflictor
        
    #  figure momentum add
    if (inflictor != qc.world) and (targ.movetype == defs.MOVETYPE_WALK):
        dir = targ.origin - (inflictor.absmin + inflictor.absmax) * 0.5
        dir = dir.normalize()
        targ.velocity += dir * damage * 8
        
    #  check for godmode or invincibility
    if qc.self.killed != 99:
        #  god or 666 doesn't save your from team change
        if targ.flags & defs.FL_GODMODE:
            return 
        if targ.invincible_finished >= qc.time:
            if qc.self.invincible_sound < qc.time:
                targ.sound(defs.CHAN_ITEM, 'items/protect3.wav', 1, defs.ATTN_NORM)
                qc.self.invincible_sound = qc.time + 2                
            return 
                    
    #  team play damage avoidance
    if (defs.teamplay == 1) and (targ.team > 0) and (targ.team == attacker.team):
        return 
    #  *TEAMPLAY*
    #  TeamHealthDam will return true if the attacker can damage the target's
    #  health
    if not teamplay.TeamHealthDam(targ, inflictor, attacker, damage):
        return 
    #  do the damage
    targ.health -= take
    if targ.health <= 0:
        Killed(targ, attacker)
        return 
        
    #  react to the damage
    oldself = qc.self
    qc.self = targ
    
    if qc.self.th_pain:
        qc.self.th_pain(attacker, take)
        
    qc.self = oldself
    
# 
# ============
# T_RadiusDamage
# ============
# 
def T_RadiusDamage(inflictor, attacker, damage, ignore, *qwp_extra):
    for head in engine.findradius(inflictor.origin, damage + 40):
        if head.takedamage and (head != ignore):
            org = head.origin + (head.mins + head.maxs) * 0.5
            points = 0.5 * qc.length(inflictor.origin - org)
            if points < 0:
                points = 0
            points = damage - points
            if head == attacker:
                points *= 0.5
            if (points > 0) and CanDamage(head, inflictor):
                T_Damage(head, inflictor, attacker, points)                                                                        

            
# 
# ============
# T_BeamDamage
# ============
# 
def T_BeamDamage(attacker, damage, *qwp_extra):
    for head in engine.findradius(attacker.origin, damage + 40):
        if head.takedamage:
            points = 0.5 * qc.length(attacker.origin - head.origin)
            if points < 0:
                points = 0
            points = damage - points
            if head == attacker:
                points *= 0.5
            if (points > 0) and CanDamage(head, attacker):
                T_Damage(head, attacker, attacker, points)
