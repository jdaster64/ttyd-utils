#! /usr/bin/python3.4

# Jonathan Aldrich 2017-03-31
"""RNG prediction / manipulation utilities for various games.

Usage:
  rngutil GAME MODE ARGS

Games:
  sm64 (SM64); ttyd (PM:TTYD); pm, spm (PM64 / SPM); pit, bis (PiT / BIS)
Modes / Args:
  -d initial_state final_state (limit): 
    Finds the number of RNG calls between states.
    Stops checking after limit calls, or 32768 if no limit is specified.
  -a initial_state num (range):
    Advances the RNG state forward / back num times.
    If range is specified, also gives the value returned by rand[0, range).
  -n initial_state range val (val2) (limit)
    Determines how many calls needed for rand[0, range) to return
    a value in range [val, val2], or val exactly if no val2 is specified.
    Stops checking after limit calls, or 32768 if no limit is specified.
  -z range val (val2) (limit)
    Randomly tries to find the best starting state to produce the longest
    run of states where rand[0, range) is in range [val, val2].
    Stops checking after limit calls, or 99999 if no limit is specified.
  -i state (For LCG random functions only):
    Returns the distance between the given state and the RNG's starting state."""

import math
import random
import sys

gGameSynonyms = {
    "sm64": ["sm64", "sm", "64"],
    "pm64": ["pm", "pm64", "spm"],
    "ttyd": ["ttyd", "pm2"],
    "ml23": ["ml", "ml2", "ml3", "mlrpg2", "mlrpg3",
             "mlbis", "bis", "mlpit", "pit"]
}
gModeSynonyms = {
    "distance": ["find", "f", "-f", "distance", "d", "-d"],
    "advance": ["advance", "add", "a", "-a", "adv"],
    "nearest": ["nearest", "next", "n", "-n",
                "result", "rand", "range", "r", "-r"],
    "freeze": ["freeze", "fr", "frz", "z", "-z"],
    "index": ["index", "position", "i", "-i"],
    "help": ["help", "h", "-h"]
}

# Finds the distance of a full-period 32-bit LCG where LCG(s) = a * s + c.
def _LcgDistance(final_state, a, c, start_state):
    candidate_state = start_state
    idx = 0
    for bit in range(32):
        if (final_state - (a * candidate_state + c)) % (2<<bit) == 0:
            candidate_state = (a * candidate_state + c) % 2**32
            idx += 2**bit
        c = (a * c + c) % 2**32
        a = (a * a) % 2**32
    return idx

class RngBase:
    """Generic base class for wrappers to game RNG functions."""
    
    # Advances the state as determined by a game's specific RNG function.
    def Increment(self, state):
        pass
        
    # Inverse of Increment; i.e. Increment(result) = `state`.
    def Decrement(self, state):
        pass
    
    # Given a state, returns a value in [0, rn) as determined by
    # a specific game's RNG. Will optionally increment `state` beforehand.
    def Rand(self, state, rn, increment=False):
        pass
        
class SuperMario64Rng(RngBase):
    """Represents the RNG functions used in Super Mario 64."""
    
    # Helper performing a repeated step in the inverse RNG advance function.
    def _s4_to_s6(self, s4):
        return ((s4 >> 1) ^ 0xff80) ^ (0x8180 if s4 & 1 == 1 else 0x1ff4)
    
    # Advances the state as determined by a game's specific RNG function.
    def Increment(self, state):
        state = state % 2**16
        if state == 21674: return 0
        if state == 22026: return 57460
        s1 = (state & 0xff) << 8
        s2 = state ^ s1
        s3 = ((s2 & 0xff) << 8) + (s2 >> 8)
        s4 = ((s2 & 0xff) << 1) ^ s3
        s5 = (s4 >> 1) ^ 0xff80
        s0 = s5 ^ (0x8180 if s4 & 1 == 1 else 0x1ff4)
        return s0
        
    # Inverse of Increment; i.e. Increment(result) = `state`.
    def Decrement(self, state):
        state = state % 2**16
        if state == 0: return 21674
        s0 = state
        s4 = ((s0 ^ 0xe074) & 0x7fff) << 1
        if self._s4_to_s6(s4) != s0: s4 = (((s0 ^ 0xe074) & 0x7fff) << 1) + 1
        if self._s4_to_s6(s4) != s0: s4 = (((s0 ^ 0x7e00) & 0x7fff) << 1)
        if self._s4_to_s6(s4) != s0: s4 = (((s0 ^ 0x7e00) & 0x7fff) << 1) + 1
        if self._s4_to_s6(s4) != s0: return 0
        s2 = s4 & 0xfe00
        s2 += ((s2 >> 7) ^ s4) & 0x100
        s2 = (((s4 ^ (s2 >> 7)) & 0xff) << 8) + (s2 >> 8)
        s0 = s2 & 0xff
        s0 += (s2 & 0xff00) ^ (s0 << 8)
        return s0
    
    # Given a state, returns a value in [0, rn) as determined by
    # a specific game's RNG. Will optionally increment `state` beforehand.
    def Rand(self, state, rn, increment=False):
        state = state % 2**16
        if increment: state = self.Increment(state)
        return state * rn // 65536

class PaperMario64Rng(RngBase):
    """Represents the RNG functions used in Paper Mario & Super Paper Mario."""
    
    # Advances the state as determined by a game's specific RNG function.
    def Increment(self, state):
        state = state % 2**32
        return (0x5D588B65 * state + 1) % 2**32
        
    # Inverse of Increment; i.e. Increment(result) = `state`.
    def Decrement(self, state):
        state = state % 2**32
        return (0x6A76AE6D * state + 0x95895193) % 2**32
    
    # Given a state, returns a value in [0, rn) as determined by
    # a specific game's RNG. Will optionally increment `state` beforehand.
    def Rand(self, state, rn, increment=False):
        state = state % 2**32
        if increment: state = self.Increment(state)
        if rn == 2:
            anti_range = 0xffffffff // 1001
            fin = state // anti_range
            if fin >= 1001:
                return self.Rand(self.Increment(state), rn)
            return 1 if fin < 501 else 0
        elif rn == 101:
            anti_range = 0xffffffff // 1010
            fin = state // anti_range
            if fin >= 1010:
                return self.Rand(self.Increment(state), rn)
            return 0x66666667*fin//2**34
        else:
            anti_range = 0xffffffff // rn
            fin = state // anti_range
            if fin > rn - 1:
                return self.Rand(self.Increment(state), rn)
            return fin

class PaperMarioTtydRng(RngBase):
    """Represents the RNG functions used in Paper Mario: TTYD."""
    
    # Advances the state as determined by a game's specific RNG function.
    def Increment(self, state):
        state = state % 2**32
        return (0x41C64E6D * state + 0x3039) % 2**32
        
    # Inverse of Increment; i.e. Increment(result) = `state`.
    def Decrement(self, state):
        state = state % 2**32
        return (0xEEB9EB65 * state + 0xFC77A683) % 2**32
    
    # Given a state, returns a value in [0, rn) as determined by
    # a specific game's RNG. Will optionally increment `state` beforehand.
    def Rand(self, state, rn, increment=False):
        state = state % 2**32
        if increment: state = self.Increment(state)
        return ((state >> 16) & 0x7fff) % rn
        
    # Returns the number of calls between initial_state and state.
    def DistanceDirect(self, state, initial_state=1):
        return _LcgDistance(state, 0x41C64E6D, 0x3039, initial_state)

class MarioAndLuigi2Rng(RngBase):
    """Represents the RNG functions used in the DS Mario & Luigi games."""
    
    # Advances the state as determined by a game's specific RNG function.
    def Increment(self, state):
        state = state % 2**16
        if state == 0: return 0x3ff3
        return (((state * 41) >> 1) & 0x7fff) + 0x8000 * (state & 1)
        
    # Inverse of Increment; i.e. Increment(result) = `state`.
    def Decrement(self, state):
        state = state % 2**16
        x = state % 0x10000
        for z in range(0,41): 
            ix = math.ceil(((x&0x7fff)+(z*0x10000))/20.5)&0xffff 
            if self.Increment(int(ix)) == x: return ix 
        return -1
    
    # Given a state, returns a value in [0, rn) as determined by
    # a specific game's RNG. Will optionally increment `state` beforehand.
    def Rand(self, state, rn, increment=False):
        state = state % 2**16
        if increment: state = self.Increment(state)
        return state % rn

def _Distance(rng, initial_state, final_state, max_calls):
    if rng.DistanceDirect:
        distance = rng.DistanceDirect(final_state, initial_state)
        if distance * 3 / 2 > 2**32:
            distance = distance - 2**32
        print("Num calls: %i" % (distance))
        return
    fwd = initial_state
    bck = initial_state
    for x in range(1, max_calls+1):
        fwd = rng.Increment(fwd)
        bck = rng.Decrement(bck)
        if (fwd == final_state):
            print("Num calls: +%i" % (x))
            return
        if (bck == final_state):
            print("Num calls: -%i" % (x))
            return
    print("More than %i calls away." % (max_calls))
  
def _Advance(rng, state, num_calls, rn):
    if num_calls >= 0:
        for _ in range(0, num_calls):
            state = rng.Increment(state)
    else:
        for _ in range(0, -num_calls):
            state = rng.Decrement(state)
    if rn != None and rn > 0:
        print("Final state: 0x%08x, rand(range): %i" %
                (state, rng.Rand(state, rn)))
    else:
        print("Final state: 0x%08x" % (state))

def _Nearest(rng, state, rn, low, high, max_calls):
    for x in range(1, max_calls+1):
        state = rng.Increment(state)
        dec = rng.Rand(state, rn)
        if dec >= low and dec <= high:
            print("Num calls: %i, Final state: 0x%08x" % (x, state))
            return
    print("More than %i calls away." % (max_calls))
    
def _Freeze(rng, bits, rn, low, high, max_calls):
    bstate = 0
    bcount = 0
    for x in range(max_calls):
        state = random.randrange(2**bits)
        state_nx = state
        count = 0
        while True:
            state_nx = rng.Increment(state_nx)
            dec = rng.Rand(state_nx, rn)
            if dec < low or dec > high:
                break
            count += 1
        if count > bcount:
            bstate = state
            bcount = count
    print("Best frozen state / length: 0x%08x (%i calls)." % (bstate, bcount))
    
def _Index(rng, state):
    if not rng.DistanceDirect:
        print("Direct index not supported for non-LCG RNG functions.")
        return
    index = rng.DistanceDirect(state)
    print("Index of state 0x%08x: %i" % (state, index))
    
def main(argc, argv):
    if argc < 3:
        print(__doc__)
        return
    if argv[0] in gModeSynonyms["help"]:
        print(__doc__)
        return
        
    # Select the RNG implementation based on the game parameter.
    rng = None
    bits = 0
    if argv[0] in gGameSynonyms["sm64"]:
        rng = SuperMario64Rng()
        bits = 16
    if argv[0] in gGameSynonyms["pm64"]:
        rng = PaperMario64Rng()
        bits = 32
    if argv[0] in gGameSynonyms["ttyd"]:
        rng = PaperMarioTtydRng()
        bits = 32
    if argv[0] in gGameSynonyms["ml23"]:
        rng = MarioAndLuigi2Rng()
        bits = 16
    if not rng:
        print(__doc__)
        return
        
    # Call one of the main functions based on the mode parameter.
    if argv[1] in gModeSynonyms["distance"]:
        if argc < 4:  # doesn't have enough arguments
            print(__doc__)
            return
        max_calls = 32768
        if argc > 4: max_calls = int(argv[4], 0)  # opt. limit
        _Distance(rng, int(argv[2], 0), int(argv[3], 0), max_calls)
        return
    if argv[1] in gModeSynonyms["advance"]:
        if argc < 4:  # doesn't have enough arguments
            print(__doc__)
            return
        rn = None
        if argc > 4: rn = int(argv[4], 0)  # opt. range
        _Advance(rng, int(argv[2], 0), int(argv[3], 0), rn)
        return
    if argv[1] in gModeSynonyms["nearest"]:
        if argc < 5:  # doesn't have enough arguments
            print(__doc__)
            return
        end_range = int(argv[4], 0)
        max_calls = 32768
        if argc > 6: max_calls = int(argv[6], 0)  # opt. limit
        if argc > 5: end_range = int(argv[5], 0)  # opt. range end
        _Nearest(rng, int(argv[2], 0), int(argv[3], 0), int(argv[4], 0),
                 end_range, max_calls)
        return
    if argv[1] in gModeSynonyms["freeze"]:
        if argc < 4:  # doesn't have enough arguments
            print(__doc__)
            return
        end_range = int(argv[3], 0)
        max_calls = 99999
        if argc > 5: max_calls = int(argv[5], 0)  # opt. limit
        if argc > 4: end_range = int(argv[4], 0)  # opt. range end
        _Freeze(rng, bits, int(argv[2], 0), int(argv[3], 0),
                end_range, max_calls)
        return
    if argv[1] in gModeSynonyms["index"]:
        _Index(rng, int(argv[2], 0))
        return
    print(__doc__)

if __name__ == "__main__":
  main(len(sys.argv) - 1, sys.argv[1:])