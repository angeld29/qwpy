###
### Generated by QuakeC -> Python translator
### Id: qc2python.py,v 1.5 2001/02/05 21:15:44 barryp Exp 
###
from qwpython.qwsv import engine, Vector
from qwpython.qcsupport import qc

import combat
import defs
import subs
import math

DOOR_START_OPEN = 1
DOOR_DONT_LINK = 4
DOOR_GOLD_KEY = 8
DOOR_SILVER_KEY = 16
DOOR_TOGGLE = 32
# 
# 
# Doors are similar to buttons, but can spawn a fat trigger field around them
# to open without a touch, and they link together to form simultanious
# double/quad doors.
#  
# Door.owner is the master door.  If there is only one door, it points to itself.
# If multiple doors, all will point to a single one.
# 
# Door.enemy chains from the master door through all doors linked in the chain.
# 
# 
# 
# =============================================================================
# 
# THINK FUNCTIONS
# 
# =============================================================================
# 

def door_blocked(*qwp_extra):
    qc.other.deathtype = 'squish'
    combat.T_Damage(qc.other, qc.self, qc.self.goalentity, qc.self.dmg)
    #  if a door has a negative wait, it would never come back if blocked,
    #  so let it just squash the object to death real fast
    if qc.self.wait >= 0:
        if qc.self.state == defs.STATE_DOWN:
            door_go_up()
        else:
            door_go_down()
        
    

def door_hit_top(*qwp_extra):
    qc.self.sound(defs.CHAN_NO_PHS_ADD + defs.CHAN_VOICE, qc.self.noise1, 1, defs.ATTN_NORM)
    qc.self.state = defs.STATE_TOP
    if qc.self.spawnflags & DOOR_TOGGLE:
        return  #  don't come down automatically
    qc.self.think = door_go_down
    qc.self.nextthink = qc.self.ltime + qc.self.wait
    

def door_hit_bottom(*qwp_extra):
    qc.self.sound(defs.CHAN_NO_PHS_ADD + defs.CHAN_VOICE, qc.self.noise1, 1, defs.ATTN_NORM)
    qc.self.state = defs.STATE_BOTTOM
    

def door_go_down(*qwp_extra):
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise2, 1, defs.ATTN_NORM)
    if qc.self.max_health:
        qc.self.takedamage = defs.DAMAGE_YES
        qc.self.health = qc.self.max_health
        
    qc.self.state = defs.STATE_DOWN
    subs.SUB_CalcMove(qc.self.pos1, qc.self.speed, door_hit_bottom)
    

def door_go_up(*qwp_extra):
    if qc.self.state == defs.STATE_UP:
        return  #  allready going up
    if qc.self.state == defs.STATE_TOP:
        #  reset top wait time
        qc.self.nextthink = qc.self.ltime + qc.self.wait
        return 
        
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise2, 1, defs.ATTN_NORM)
    qc.self.state = defs.STATE_UP
    subs.SUB_CalcMove(qc.self.pos2, qc.self.speed, door_hit_top)
    subs.SUB_UseTargets()
    
# 
# =============================================================================
# 
# ACTIVATION FUNCTIONS
# 
# =============================================================================
# 

def door_fire(*qwp_extra):
    oself = engine.world
    starte = engine.world
    if qc.self.owner != qc.self:
        qc.objerror('door_fire: self.owner != self')
    #  play use key sound
    if qc.self.items:
        qc.self.sound(defs.CHAN_VOICE, qc.self.noise4, 1, defs.ATTN_NORM)
    qc.self.message = defs.string_null #  no more message
    oself = qc.self
    if qc.self.spawnflags & DOOR_TOGGLE:
        if qc.self.state == defs.STATE_UP or qc.self.state == defs.STATE_TOP:
            starte = qc.self
            while 1:
                door_go_down()
                qc.self = qc.self.enemy
                if not ((qc.self != starte) and (qc.self != qc.world)):
                    break
            qc.self = oself
            return 
            
        
    #  trigger all paired doors
    starte = qc.self
    while 1:
        qc.self.goalentity = defs.activator #  Who fired us
        door_go_up()
        qc.self = qc.self.enemy
        if not ((qc.self != starte) and (qc.self != qc.world)):
            break
    qc.self = oself
    

def door_use(*qwp_extra):
    oself = engine.world
    qc.self.message = None #  door message are for touch only
    qc.self.owner.message = None
    qc.self.enemy.message = None
    oself = qc.self
    qc.self = qc.self.owner
    door_fire()
    qc.self = oself
    

def door_trigger_touch(*qwp_extra):
    if qc.other.health <= 0:
        return 
    if qc.time < qc.self.attack_finished:
        return 
    qc.self.attack_finished = qc.time + 1
    defs.activator = qc.other
    qc.self = qc.self.owner
    door_use()
    

def door_killed(*qwp_extra):
    oself = engine.world
    oself = qc.self
    qc.self = qc.self.owner
    qc.self.health = qc.self.max_health
    qc.self.takedamage = defs.DAMAGE_NO #  wil be reset upon return
    door_use()
    qc.self = oself
    
# 
# ================
# door_touch
# 
# Prints messages and opens key doors
# ================
# 

def door_touch(*qwp_extra):
    if qc.other.classname != 'player':
        return 
    if qc.self.owner.attack_finished > qc.time:
        return 
    qc.self.owner.attack_finished = qc.time + 2
    if qc.self.owner.message != None:
        qc.centerprint(qc.other, qc.self.owner.message)
        qc.other.sound(defs.CHAN_VOICE, 'misc/talk.wav', 1, defs.ATTN_NORM)
        
    #  key door stuff
    if not qc.self.items:
        return 
    #  FIXME: blink key on player's status bar
    if (qc.self.items & qc.other.items) != qc.self.items:
        if qc.self.owner.items == defs.IT_KEY1:
            if qc.world.worldtype == 2:
                qc.centerprint(qc.other, 'You need the silver keycard')
                qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
                
            elif qc.world.worldtype == 1:
                qc.centerprint(qc.other, 'You need the silver runekey')
                qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
                
            elif qc.world.worldtype == 0:
                qc.centerprint(qc.other, 'You need the silver key')
                qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
                
            
        else:
            if qc.world.worldtype == 2:
                qc.centerprint(qc.other, 'You need the gold keycard')
                qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
                
            elif qc.world.worldtype == 1:
                qc.centerprint(qc.other, 'You need the gold runekey')
                qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
                
            elif qc.world.worldtype == 0:
                qc.centerprint(qc.other, 'You need the gold key')
                qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
                
            
        return 
        
    qc.other.items -= qc.self.items
    qc.self.touch = subs.SUB_Null
    if qc.self.enemy:
        qc.self.enemy.touch = subs.SUB_Null #  get paired door
    door_use()
    
# 
# =============================================================================
# 
# SPAWNING FUNCTIONS
# 
# =============================================================================
# 

def spawn_field(fmins, fmaxs, *qwp_extra):
    trigger = engine.world
    t1 = Vector(0, 0, 0)
    t2 = Vector(0, 0, 0)
    trigger = qc.spawn()
    trigger.movetype = defs.MOVETYPE_NONE
    trigger.solid = defs.SOLID_TRIGGER
    trigger.owner = qc.self
    trigger.touch = door_trigger_touch
    t1 = fmins
    t2 = fmaxs
    qc.setsize(trigger, t1 - Vector(60, 60, 8), t2 + Vector(60, 60, 8))
    return (trigger)
    

def EntitiesTouching(e1, e2, *qwp_extra):
    if e1.mins.x > e2.maxs.x:
        return defs.FALSE
    if e1.mins.y > e2.maxs.y:
        return defs.FALSE
    if e1.mins.z > e2.maxs.z:
        return defs.FALSE
    if e1.maxs.x < e2.mins.x:
        return defs.FALSE
    if e1.maxs.y < e2.mins.y:
        return defs.FALSE
    if e1.maxs.z < e2.mins.z:
        return defs.FALSE
    return defs.TRUE
    
# 
# =============
# LinkDoors
# 
# 
# =============
# 

def LinkDoors(*qwp_extra):
    t = engine.world
    starte = engine.world
    cmins = Vector(0, 0, 0)
    cmaxs = Vector(0, 0, 0)
    if qc.self.enemy:
        return  #  already linked by another door
    if qc.self.spawnflags & 4:
        qc.self.owner = qc.self.enemy = qc.self
        return  #  don't want to link this door
        
    cmins = qc.self.mins
    cmaxs = qc.self.maxs
    starte = qc.self
    t = qc.self
    while 1:
        qc.self.owner = starte #  master door
        if qc.self.health:
            starte.health = qc.self.health
        if qc.self.targetname:
            starte.targetname = qc.self.targetname
        if qc.self.message != None:
            starte.message = qc.self.message
        t = qc.find(t, 'classname', qc.self.classname)
        if not t:
            qc.self.enemy = starte #  make the chain a loop
            #  shootable, fired, or key doors just needed the owner/enemy links,
            #  they don't spawn a field
            qc.self = qc.self.owner
            if qc.self.health:
                return 
            if qc.self.targetname:
                return 
            if qc.self.items:
                return 
            qc.self.owner.trigger_field = spawn_field(cmins, cmaxs)
            return 
            
        if EntitiesTouching(qc.self, t):
            if t.enemy:
                qc.objerror('cross connected doors')
            qc.self.enemy = t
            qc.self = t
            if t.mins.x < cmins.x:
                cmins %= Vector(t.mins.x, None, None)
            if t.mins.y < cmins.y:
                cmins %= Vector(None, t.mins.y, None)
            if t.mins.z < cmins.z:
                cmins %= Vector(None, None, t.mins.z)
            if t.maxs.x > cmaxs.x:
                cmaxs %= Vector(t.maxs.x, None, None)
            if t.maxs.y > cmaxs.y:
                cmaxs %= Vector(None, t.maxs.y, None)
            if t.maxs.z > cmaxs.z:
                cmaxs %= Vector(None, None, t.maxs.z)
            
        
    
# QUAKED func_door (0 .5 .8) ? START_OPEN x DOOR_DONT_LINK GOLD_KEY SILVER_KEY TOGGLE
# if two doors touch, they are assumed to be connected and operate as a unit.
# 
# TOGGLE causes the door to wait in both the start and end states for a trigger event.
# 
# START_OPEN causes the door to move to its destination when spawned, and operate in reverse.  It is used to temporarily or permanently close off an area when triggered (not usefull for touch or takedamage doors).
# 
# Key doors are allways wait -1.
# 
# "message"       is printed when the door is touched if it is a trigger door and it hasn't been fired yet
# "angle"         determines the opening direction
# "targetname" if set, no touch field will be spawned and a remote button or trigger field activates the door.
# "health"        if set, door must be shot open
# "speed"         movement speed (100 default)
# "wait"          wait before returning (3 default, -1 = never return)
# "lip"           lip remaining at end of move (8 default)
# "dmg"           damage to inflict when blocked (2 default)
# "sounds"
# 0)      no sound
# 1)      stone
# 2)      base
# 3)      stone chain
# 4)      screechy metal
# 

def func_door(*qwp_extra):
    if qc.world.worldtype == 0:
        engine.precache_sound('doors/medtry.wav')
        engine.precache_sound('doors/meduse.wav')
        qc.self.noise3 = 'doors/medtry.wav'
        qc.self.noise4 = 'doors/meduse.wav'
        
    elif qc.world.worldtype == 1:
        engine.precache_sound('doors/runetry.wav')
        engine.precache_sound('doors/runeuse.wav')
        qc.self.noise3 = 'doors/runetry.wav'
        qc.self.noise4 = 'doors/runeuse.wav'
        
    elif qc.world.worldtype == 2:
        engine.precache_sound('doors/basetry.wav')
        engine.precache_sound('doors/baseuse.wav')
        qc.self.noise3 = 'doors/basetry.wav'
        qc.self.noise4 = 'doors/baseuse.wav'
        
    else:
        engine.dprint('no worldtype set!\012')
        
    if qc.self.sounds == 0:
        engine.precache_sound('misc/null.wav')
        engine.precache_sound('misc/null.wav')
        qc.self.noise1 = 'misc/null.wav'
        qc.self.noise2 = 'misc/null.wav'
        
    if qc.self.sounds == 1:
        engine.precache_sound('doors/drclos4.wav')
        engine.precache_sound('doors/doormv1.wav')
        qc.self.noise1 = 'doors/drclos4.wav'
        qc.self.noise2 = 'doors/doormv1.wav'
        
    if qc.self.sounds == 2:
        engine.precache_sound('doors/hydro1.wav')
        engine.precache_sound('doors/hydro2.wav')
        qc.self.noise2 = 'doors/hydro1.wav'
        qc.self.noise1 = 'doors/hydro2.wav'
        
    if qc.self.sounds == 3:
        engine.precache_sound('doors/stndr1.wav')
        engine.precache_sound('doors/stndr2.wav')
        qc.self.noise2 = 'doors/stndr1.wav'
        qc.self.noise1 = 'doors/stndr2.wav'
        
    if qc.self.sounds == 4:
        engine.precache_sound('doors/ddoor1.wav')
        engine.precache_sound('doors/ddoor2.wav')
        qc.self.noise1 = 'doors/ddoor2.wav'
        qc.self.noise2 = 'doors/ddoor1.wav'
        
    subs.SetMovedir()
    qc.self.max_health = qc.self.health
    qc.self.solid = defs.SOLID_BSP
    qc.self.movetype = defs.MOVETYPE_PUSH
    qc.setorigin(qc.self, qc.self.origin)
    qc.self.setmodel(qc.self.model)
    qc.self.classname = 'door'
    qc.self.blocked = door_blocked
    qc.self.use = door_use
    if qc.self.spawnflags & DOOR_SILVER_KEY:
        qc.self.items = defs.IT_KEY1
    if qc.self.spawnflags & DOOR_GOLD_KEY:
        qc.self.items = defs.IT_KEY2
    if not qc.self.speed:
        qc.self.speed = 100
    if not qc.self.wait:
        qc.self.wait = 3
    if not qc.self.lip:
        qc.self.lip = 8
    if not qc.self.dmg:
        qc.self.dmg = 2
    qc.self.pos1 = qc.self.origin
    qc.self.pos2 = qc.self.pos1 + qc.self.movedir * (math.fabs(qc.self.movedir * qc.self.size) - qc.self.lip)
    #  DOOR_START_OPEN is to allow an entity to be lighted in the closed position
    #  but spawn in the open position
    if qc.self.spawnflags & DOOR_START_OPEN:
        qc.setorigin(qc.self, qc.self.pos2)
        qc.self.pos2 = qc.self.pos1
        qc.self.pos1 = qc.self.origin
        
    qc.self.state = defs.STATE_BOTTOM
    if qc.self.health:
        qc.self.takedamage = defs.DAMAGE_YES
        qc.self.th_die = door_killed
        
    if qc.self.items:
        qc.self.wait = -1
    qc.self.touch = door_touch
    #  LinkDoors can't be done until all of the doors have been spawned, so
    #  the sizes can be detected properly.
    qc.self.think = LinkDoors
    qc.self.nextthink = qc.self.ltime + 0.1
    
# 
# =============================================================================
# 
# SECRET DOORS
# 
# =============================================================================
# 
SECRET_OPEN_ONCE = 1 #  stays open
SECRET_1ST_LEFT = 2 #  1st move is left of arrow
SECRET_1ST_DOWN = 4 #  1st move is down from arrow
SECRET_NO_SHOOT = 8 #  only opened by trigger
SECRET_YES_SHOOT = 16 #  shootable even if targeted

def fd_secret_use(*qwp_extra):
    temp = 0
    qc.self.health = 10000
    #  exit if still moving around...
    if qc.self.origin != qc.self.oldorigin:
        return 
    qc.self.message = defs.string_null #  no more message
    subs.SUB_UseTargets() #  fire all targets / killtargets
    if not (qc.self.spawnflags & SECRET_NO_SHOOT):
        qc.self.th_pain = subs.SUB_Null
        qc.self.takedamage = defs.DAMAGE_NO
        
    qc.self.velocity = Vector(0, 0, 0)
    #  Make a sound, wait a little...
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise1, 1, defs.ATTN_NORM)
    qc.self.nextthink = qc.self.ltime + 0.1
    temp = 1 - (qc.self.spawnflags & SECRET_1ST_LEFT) #  1 or -1
    qc.makevectors(qc.self.mangle)
    if not qc.self.t_width:
        if qc.self.spawnflags & SECRET_1ST_DOWN:
            qc.self.t_width = math.fabs(qc.v_up * qc.self.size)
        else:
            qc.self.t_width = math.fabs(qc.v_right * qc.self.size)
        
    if not qc.self.t_length:
        qc.self.t_length = math.fabs(qc.v_forward * qc.self.size)
    if qc.self.spawnflags & SECRET_1ST_DOWN:
        qc.self.dest1 = qc.self.origin - qc.v_up * qc.self.t_width
    else:
        qc.self.dest1 = qc.self.origin + qc.v_right * (qc.self.t_width * temp)
    qc.self.dest2 = qc.self.dest1 + qc.v_forward * qc.self.t_length
    subs.SUB_CalcMove(qc.self.dest1, qc.self.speed, fd_secret_move1)
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise2, 1, defs.ATTN_NORM)
    
#  Wait after first movement...

def fd_secret_move1(*qwp_extra):
    qc.self.nextthink = qc.self.ltime + 1.0
    qc.self.think = fd_secret_move2
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
    
#  Start moving sideways w/sound...

def fd_secret_move2(*qwp_extra):
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise2, 1, defs.ATTN_NORM)
    subs.SUB_CalcMove(qc.self.dest2, qc.self.speed, fd_secret_move3)
    
#  Wait here until time to go back...

def fd_secret_move3(*qwp_extra):
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
    if not (qc.self.spawnflags & SECRET_OPEN_ONCE):
        qc.self.nextthink = qc.self.ltime + qc.self.wait
        qc.self.think = fd_secret_move4
        
    
#  Move backward...

def fd_secret_move4(*qwp_extra):
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise2, 1, defs.ATTN_NORM)
    subs.SUB_CalcMove(qc.self.dest1, qc.self.speed, fd_secret_move5)
    
#  Wait 1 second...

def fd_secret_move5(*qwp_extra):
    qc.self.nextthink = qc.self.ltime + 1.0
    qc.self.think = fd_secret_move6
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
    

def fd_secret_move6(*qwp_extra):
    qc.self.sound(defs.CHAN_VOICE, qc.self.noise2, 1, defs.ATTN_NORM)
    subs.SUB_CalcMove(qc.self.oldorigin, qc.self.speed, fd_secret_done)
    

def fd_secret_done(*qwp_extra):
    if not qc.self.targetname or qc.self.spawnflags & SECRET_YES_SHOOT:
        qc.self.health = 10000
        qc.self.takedamage = defs.DAMAGE_YES
        qc.self.th_pain = fd_secret_use
        qc.self.th_die = fd_secret_use
        
    qc.self.sound(defs.CHAN_NO_PHS_ADD + defs.CHAN_VOICE, qc.self.noise3, 1, defs.ATTN_NORM)
    

def secret_blocked(*qwp_extra):
    if qc.time < qc.self.attack_finished:
        return 
    qc.self.attack_finished = qc.time + 0.5
    qc.other.deathtype = 'squish'
    combat.T_Damage(qc.other, qc.self, qc.self, qc.self.dmg)
    
# 
# ================
# secret_touch
# 
# Prints messages
# ================
# 

def secret_touch(*qwp_extra):
    if qc.other.classname != 'player':
        return 
    if qc.self.attack_finished > qc.time:
        return 
    qc.self.attack_finished = qc.time + 2
    if qc.self.message:
        qc.centerprint(qc.other, qc.self.message)
        qc.other.sound(defs.CHAN_BODY, 'misc/talk.wav', 1, defs.ATTN_NORM)
        
    
# QUAKED func_door_secret (0 .5 .8) ? open_once 1st_left 1st_down no_shoot always_shoot
# Basic secret door. Slides back, then to the side. Angle determines direction.
# wait  = # of seconds before coming back
# 1st_left = 1st move is left of arrow
# 1st_down = 1st move is down from arrow
# always_shoot = even if targeted, keep shootable
# t_width = override WIDTH to move back (or height if going down)
# t_length = override LENGTH to move sideways
# "dmg"           damage to inflict when blocked (2 default)
# 
# If a secret door has a targetname, it will only be opened by it's botton or trigger, not by damage.
# "sounds"
# 1) medieval
# 2) metal
# 3) base
# 

def func_door_secret(*qwp_extra):
    if qc.self.sounds == 0:
        qc.self.sounds = 3
    if qc.self.sounds == 1:
        engine.precache_sound('doors/latch2.wav')
        engine.precache_sound('doors/winch2.wav')
        engine.precache_sound('doors/drclos4.wav')
        qc.self.noise1 = 'doors/latch2.wav'
        qc.self.noise2 = 'doors/winch2.wav'
        qc.self.noise3 = 'doors/drclos4.wav'
        
    if qc.self.sounds == 2:
        engine.precache_sound('doors/airdoor1.wav')
        engine.precache_sound('doors/airdoor2.wav')
        qc.self.noise2 = 'doors/airdoor1.wav'
        qc.self.noise1 = 'doors/airdoor2.wav'
        qc.self.noise3 = 'doors/airdoor2.wav'
        
    if qc.self.sounds == 3:
        engine.precache_sound('doors/basesec1.wav')
        engine.precache_sound('doors/basesec2.wav')
        qc.self.noise2 = 'doors/basesec1.wav'
        qc.self.noise1 = 'doors/basesec2.wav'
        qc.self.noise3 = 'doors/basesec2.wav'
        
    if not qc.self.dmg:
        qc.self.dmg = 2
    #  Magic formula...
    qc.self.mangle = qc.self.angles
    qc.self.angles = Vector(0, 0, 0)
    qc.self.solid = defs.SOLID_BSP
    qc.self.movetype = defs.MOVETYPE_PUSH
    qc.self.classname = 'door'
    qc.self.setmodel(qc.self.model)
    qc.setorigin(qc.self, qc.self.origin)
    qc.self.touch = secret_touch
    qc.self.blocked = secret_blocked
    qc.self.speed = 50
    qc.self.use = fd_secret_use
    if not qc.self.targetname or qc.self.spawnflags & SECRET_YES_SHOOT:
        qc.self.health = 10000
        qc.self.takedamage = defs.DAMAGE_YES
        qc.self.th_pain = fd_secret_use
        
    qc.self.oldorigin = qc.self.origin
    if not qc.self.wait:
        qc.self.wait = 5 #  5 seconds before closing
    


def qwp_reset_doors(*qwp_extra):
    global DOOR_START_OPEN
    global DOOR_DONT_LINK
    global DOOR_GOLD_KEY
    global DOOR_SILVER_KEY
    global DOOR_TOGGLE
    global SECRET_OPEN_ONCE
    global SECRET_1ST_LEFT
    global SECRET_1ST_DOWN
    global SECRET_NO_SHOOT
    global SECRET_YES_SHOOT
    DOOR_START_OPEN = 1
    DOOR_DONT_LINK = 4
    DOOR_GOLD_KEY = 8
    DOOR_SILVER_KEY = 16
    DOOR_TOGGLE = 32
    SECRET_OPEN_ONCE = 1
    SECRET_1ST_LEFT = 2
    SECRET_1ST_DOWN = 4
    SECRET_NO_SHOOT = 8
    SECRET_YES_SHOOT = 16