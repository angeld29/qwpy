###
### Generated by QuakeC -> Python translator
### Id: qc2python.py,v 1.5 2001/02/05 21:15:44 barryp Exp 
###
from qwpython.qwsv import engine, Vector
from qwpython.qcsupport import qc

import defs
import client
import subs
import math

# SERVER
# void() monster_death_use;
# 
# ============================================================================
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
    oself = engine.world
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
    
# 
# ============
# T_Damage
# 
# The damage is coming from inflictor, but get mad at attacker
# This should be the only function that ever reduces health.
# ============
# 

def T_Damage(targ, inflictor, attacker, damage, *qwp_extra):
    dir = Vector(0, 0, 0)
    oldself = engine.world
    save = 0
    take = 0
    s = None
    attackerteam = None
    targteam = None
    if not targ.takedamage:
        return 
    #  used by buttons and triggers to set activator for target firing
    defs.damage_attacker = attacker
    #  check for quad damage powerup on the attacker
    if attacker.super_damage_finished > qc.time and inflictor.classname != 'door':
        if defs.deathmatch == 4:
            damage *= 8
        else:
            damage *= 4
    #  save damage based on the target's armor level
    save = math.ceil(targ.armortype * damage)
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
        
    defs.damage_inflictor = inflictor
    #  figure momentum add
    if (inflictor != qc.world) and (targ.movetype == defs.MOVETYPE_WALK):
        dir = targ.origin - (inflictor.absmin + inflictor.absmax) * 0.5
        dir = dir.normalize()
        #  Set kickback for smaller weapons
        # Zoid -- use normal NQ kickback
        # 		// Read: only if it's not yourself doing the damage
        # 		if ( (damage < 60) & ((attacker.classname == "player") & (targ.classname == "player")) & ( attacker.netname != targ.netname)) 
        # 			targ.velocity = targ.velocity + dir * damage * 11;
        # 		else                        
        #  Otherwise, these rules apply to rockets and grenades                        
        #  for blast velocity
        targ.velocity += dir * damage * 8
        #  Rocket Jump modifiers
        if (defs.rj > 1) & ((attacker.classname == 'player') & (targ.classname == 'player')) & (attacker.netname == targ.netname):
            targ.velocity += dir * damage * defs.rj
        
    #  check for godmode or invincibility
    if targ.flags & defs.FL_GODMODE:
        return 
    if targ.invincible_finished >= qc.time:
        if qc.self.invincible_sound < qc.time:
            targ.sound(defs.CHAN_ITEM, 'items/protect3.wav', 1, defs.ATTN_NORM)
            qc.self.invincible_sound = qc.time + 2
            
        return 
        
    #  team play damage avoidance
    # ZOID 12-13-96: self.team doesn't work in QW.  Use keys
    attackerteam = attacker.infokey('team')
    targteam = targ.infokey('team')
    if (defs.teamplay == 1) and (targteam == attackerteam) and (attacker.classname == 'player') and (attackerteam != None) and inflictor.classname != 'door':
        return 
    if (defs.teamplay == 3) and (targteam == attackerteam) and (attacker.classname == 'player') and (attackerteam != None) and (targ != attacker) and inflictor.classname != 'door':
        return 
    #  do the damage
    targ.health -= take
    if targ.health <= 0:
        Killed(targ, attacker)
        return 
        
    #  react to the damage
    oldself = qc.self
    qc.self = targ
    # SERVER
    # 	if ( (self.flags & FL_MONSTER) && attacker != world)
    # 	{
    # 	// get mad unless of the same class (except for soldiers)
    # 		if (self != attacker && attacker != self.enemy)
    # 		{
    # 			if ( (self.classname != attacker.classname) 
    # 			|| (self.classname == "monster_army" ) )
    # 			{
    # 				if (self.enemy.classname == "player")
    # 					self.oldenemy = self.enemy;
    # 				self.enemy = attacker;
    # 				FoundTarget ();
    # 			}
    # 		}
    # 	}
    # 
    if qc.self.th_pain:
        qc.self.th_pain(attacker, take)
        
    qc.self = oldself
    
# 
# ============
# T_RadiusDamage
# ============
# 

def T_RadiusDamage(inflictor, attacker, damage, ignore, dtype, *qwp_extra):
    points = 0
    head = engine.world
    org = Vector(0, 0, 0)
    head = qc.findradius(inflictor.origin, damage + 40)
    while head:
        # bprint (PRINT_HIGH, head.classname);
        # bprint (PRINT_HIGH, " | ");
        # bprint (PRINT_HIGH, head.netname);
        # bprint (PRINT_HIGH, "\n");
        if head != ignore:
            if head.takedamage:
                org = head.origin + (head.mins + head.maxs) * 0.5
                points = 0.5 * qc.length(inflictor.origin - org)
                if points < 0:
                    points = 0
                points = damage - points
                if head == attacker:
                    points *= 0.5
                if points > 0:
                    if CanDamage(head, inflictor):
                        head.deathtype = dtype
                        T_Damage(head, inflictor, attacker, points)
                        
                    
                
            
        head = head.chain
        
    
# 
# ============
# T_BeamDamage
# ============
# 

def T_BeamDamage(attacker, damage, *qwp_extra):
    points = 0
    head = engine.world
    head = qc.findradius(attacker.origin, damage + 40)
    while head:
        if head.takedamage:
            points = 0.5 * qc.length(attacker.origin - head.origin)
            if points < 0:
                points = 0
            points = damage - points
            if head == attacker:
                points *= 0.5
            if points > 0:
                if CanDamage(head, attacker):
                    T_Damage(head, attacker, attacker, points)
                
            
        head = head.chain
        
    
