"""Utility class for retrieving data from binary memory dumps."""
# Jonathan Aldrich 2016-09-03

import ctypes  # for raw bytes -> floating-point conversion

# Custom error class.
class BinaryDumpError(Exception):
    def __init__(self, message=""):
        self.message = message
        
# Memory region struct.
class _MemoryRegion(object):
    def __init__(self, data, offset):
        self.data = data       # bytes
        self.offset = offset   # starting offset (int)

# Memory dump class.
class BinaryDump(object):
    def __init__(self, big_endian=False, ptr_bytes=4):
        self.mem = []  # List of _MemoryRegions.
        self.be = big_endian
        self.ptrsize = ptr_bytes
        
    def _list_blocks(self):
        bl = ""
        for region in self.mem:
            if bl: bl += "\n"
            bl += "0x%08x: %d bytes" % (region.offset, len(region.data))
        return bl
        
    def _str_representation(self):
        s = "<BinaryDump obj>"
        bl = self._list_blocks()
        if bl: s += ", Blocks:\n%s" % bl
        return s
    
    def __str__(self):
        return self._str_representation()
    
    def __repr__(self):
        return self._str_representation()
        
    def register_block(self, data, offset=0, regions=None):
        blocks = []
        if regions is None:
            blocks.append(_MemoryRegion(data, offset))
        else:
            for t in regions:
                if t[1] < t[0] or t[1] >= len(data) or t[0] < 0:
                    raise BinaryDumpError("Bounds error on region: %s" % t)
                    return
                blocks.append(_MemoryRegion(data[t[0]:t[1]], t[2]))
        for b in blocks:
            self.mem.append(b)
    
    def register_file(self, filename, offset=0, regions=None):
        data = open(filename, "rb").read()
        self.register_block(data, offset, regions)
        
    def _read_byte(self, offset):
        for block in self.mem:
            if offset >= block.offset and offset < block.offset + len(block.data):
                return block.data[offset - block.offset]
        raise BinaryDumpError("Read from unmapped offset: 0x%x" % offset)
        
    def _read_contiguous_bytes(self, offset, sz):
        for block in self.mem:
            if offset >= block.offset and offset+sz <= block.offset + len(block.data):
                return block.data[offset-block.offset : offset-block.offset+sz]
        # Don't error out; couldn't read block contiguously.
        return None
        
    def _read_integer(self, offset, sz=1):
        if sz < 1:
            raise BinaryDumpError("Cannot read an integer of non-positive length.")
        res = 0
        for x in range(0,sz):
            d = x if self.be else sz-1-x
            res = 256 * res + self._read_byte(offset + d)
        return res
        
    def _read_indirect_offsets(self, offset, indirect, indirect_offset):
        for d in indirect:
            offset = self._read_integer(offset + d, self.ptrsize)
        return offset + indirect_offset
        
    def read_u8(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        return self._read_byte(offset)
        
    def read_u16(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        return self._read_integer(offset, 2)
        
    def read_u32(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        return self._read_integer(offset, 4)
        
    def read_u64(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        return self._read_integer(offset, 8)
        
    def read_s8(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        u = self.read_u8(offset)
        return u if u < (1<<7) else u - (1<<8)
        
    def read_s16(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        u = self.read_u16(offset)
        return u if u < (1<<15) else u - (1<<16)
        
    def read_s32(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        u = self.read_u32(offset)
        return u if u < (1<<31) else u - (1<<32)
        
    def read_s64(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        u = self.read_u64(offset)
        return u if u < (1<<63) else u - (1<<64)
        
    def read_float(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        u = self.read_u32(offset)
        cp = ctypes.pointer(ctypes.c_uint32(u))
        fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_float))
        return fp.contents.value
        
    def read_double(self, offset, indirect=None, indirect_offset=0):
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        u = self.read_u64(offset)
        cp = ctypes.pointer(ctypes.c_uint64(u))
        fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_double))
        return fp.contents.value
        
    def read_char(self, offset, indirect=None, indirect_offset=0):
        """Reads a single byte and returns it in bytestring format."""
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        return bytes([self._read_byte(offset)])
        
    def read_cstring(self, offset, indirect=None, indirect_offset=0):
        """Reads a zero-terminated string of bytes."""
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        bs = b""
        d = 0
        while True:
            b = self._read_byte(offset + d)
            if b == 0: break
            bs += bytes([b])
            d += 1
        return bs
        
    def read_bytes(self, count, offset, indirect=None, indirect_offset=0):
        """Reads a string of bytes of length count."""
        if indirect is not None: offset = self._read_indirect_offsets(offset, indirect, indirect_offset)
        # First try reading as one contiguous block, since that's much faster.
        bs = self._read_contiguous_bytes(offset, count)
        if bs:
            return bs
        # Else, read one byte at a time. (TODO: speed up later if necessary)
        bs = b""
        d = 0
        for x in range(count):
            b = self._read_byte(offset + d)
            bs += bytes([b])
            d += 1
        return bs