"""Class for viewing, retrieving and mutating data in binary memory dumps."""
# Jonathan Aldrich 2020-12-15

import ctypes  # for floating-point conversions
import enum    # for enumerations

# Custom error class.
class BDError(Exception):
    def __init__(self, message=""):
        self.message = message

# Enumeration of supported primitive types.
class BDType(enum.Enum):
    INVALID = 0
    S8 = 1
    S16 = 2
    S32 = 3
    S64 = 4
    U8 = 5
    U16 = 6
    U32 = 7
    U64 = 8
    FLOAT = 9
    DOUBLE = 10
    CSTRING = 11
    BYTES = 12
    POINTER = 13

# Represents a view into a BDStore.
# TODO: Add __repr__ function for printing the view to a string?
class BDView(object):
    def __init__(self, datastore, address):
        self.dat = datastore
        self.address = address
        
    # Functions that read from memory.
        
    def _read_byte(self, offset):
        """Reads a single byte from the underlying BDStore at address + offset."""
        offset += self.address
        for b in self.dat.mem:
            if offset >= b.offset and offset < b.offset + len(b.data):
                return b.data[offset - b.offset]
        raise BDError("Read from unmapped offset: 0x%x" % offset)
    
    def _read_bytes(self, offset, size=1):
        """Reads `size` bytes from the underlying BDStore at address + offset."""
        if size < 1:
            raise BDError("Cannot read an integer of non-positive length.")
        offset += self.address
        # Attempt to read bytes contiguously, if possible.
        for b in self.dat.mem:
            if offset >= b.offset and offset + size <= b.offset + len(b.data):
                return bytes(b.data[offset - b.offset : offset - b.offset + size])
        # Otherwise, try to read bytes one at a time (much slower).
        bs = b""
        offset -= self.address
        for x in range(size):
            b = self._read_byte(offset + x)
            bs += bytes([b])
        return bs
            
    def _read_bytes_endian(self, offset, size=1, big_endian=True):
        """Reads `size` bytes from the underlying BDStore at address + offset,
           flipping the byte order to the desired endianness."""
        bs = self._read_bytes(offset, size)
        if self.dat.big_endian == big_endian:
            return bs
        else:
            return bs[::-1]
            
    def _read_integer(self, offset, size=1, signed=False):
        """Reads an arbitrary-size integer value from the underlying BDStore
           at address + offset, respecting the BDStore's endianness."""
        bs = self._read_bytes_endian(offset, size, big_endian=True)
        res = 0
        for x in range(size):
            res = 256 * res + bs[x]
        if res >= (1 << (size*8 - 1)) and signed:
            res -= (1 << size*8)
        return res
            
    def rs8(self, offset=0):
        return self._read_integer(offset, size=1, signed=True)
        
    def rs16(self, offset=0):
        return self._read_integer(offset, size=2, signed=True)
        
    def rs32(self, offset=0):
        return self._read_integer(offset, size=4, signed=True)
        
    def rs64(self, offset=0):
        return self._read_integer(offset, size=8, signed=True)
        
    def ru8(self, offset=0):
        return self._read_integer(offset, size=1, signed=False)
        
    def ru16(self, offset=0):
        return self._read_integer(offset, size=2, signed=False)
        
    def ru32(self, offset=0):
        return self._read_integer(offset, size=4, signed=False)
        
    def ru64(self, offset=0):
        return self._read_integer(offset, size=8, signed=False)
        
    def rf32(self, offset=0):
        u = self.ru32(offset)
        cp = ctypes.pointer(ctypes.c_uint32(u))
        fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_float))
        return fp.contents.value
        
    def rf64(self, offset=0):
        u = self.ru64(offset)
        cp = ctypes.pointer(ctypes.c_uint64(u))
        fp = ctypes.cast(cp, ctypes.POINTER(ctypes.c_double))
        return fp.contents.value
        
    def rfloat(self, offset=0):
        return self.rf32(offset)
    
    def rdouble(self, offset=0):
        return self.rf64(offset)
    
    def rcstring(self, offset=0):
        bs = b""
        while True:
            b = self._read_byte(offset)
            if b == 0: break
            bs += bytes([b])
            offset += 1
        return bs
    
    def rbytes(self, count, offset=0):
        return self._read_bytes(offset, count)
    
    def rptr(self, offset=0):
        return self._read_integer(offset, size=self.dat.ptrsize, signed=False)
    
    def read(self, type, offset=0):
        return {
            BDType.S8       : self.rs8,
            BDType.S16      : self.rs16,
            BDType.S32      : self.rs32,
            BDType.S64      : self.rs64,
            BDType.U8       : self.ru8,
            BDType.U16      : self.ru16,
            BDType.U32      : self.ru32,
            BDType.U64      : self.ru64,
            BDType.FLOAT    : self.rf32,
            BDType.DOUBLE   : self.rf64,
            BDType.CSTRING  : self.rcstring,
            BDType.POINTER  : self.rptr
        }[type](offset)
    
    # Functions that write to memory.
    
    def _write_byte(self, byte, offset):
        """Writes a single byte to the underlying BDStore at address + offset."""
        offset += self.address
        for b in self.dat.mem:
            if offset >= b.offset and offset < b.offset + len(b.data):
                b.data[offset - b.offset] = byte
                return
        raise BDError("Write to unmapped offset: 0x%x" % offset)
    
    def _write_bytes(self, bs, offset):
        """Writes a byte string to the underlying BDStore at address + offset."""
        offset += self.address
        # Attempt to write bytes contiguously, if possible.
        for b in self.dat.mem:
            if offset >= b.offset and offset + len(bs) <= b.offset + len(b.data):
                for x in range(len(bs)):
                    b.data[offset - b.offset + x] = bs[x]
                return
        # Otherwise, try to write bytes one at a time (much slower).
        offset -= self.address
        for b in bs:
            self._write_byte(b, offset + x)
        return bs
            
    def _write_bytes_endian(self, bs, offset, big_endian=True):
        """Writes a byte string to the underlying BDStore at address + offset,
           flipping the byte order to the desired endianness."""
        if self.dat.big_endian == big_endian:
            self._write_bytes(bs, offset)
        else:
            self._write_bytes(bs[::-1], offset)
            
    def _write_integer(self, value, offset, size=1):
        """Writes an arbitrary-size integer value to the underlying BDStore
           at address + offset, respecting the BDStore's endianness."""
        bs = b""
        value &= 2 ** (size*8) - 1
        for _ in range(size):
            bs += bytes([value & 0xff])
            value >>= 8
        self._write_bytes_endian(bs, offset, big_endian=False)
    
    def w8(self, value, offset=0):
        self._write_integer(value, offset, size=1)
    
    def w16(self, value, offset=0):
        self._write_integer(value, offset, size=2)
    
    def w32(self, value, offset=0):
        self._write_integer(value, offset, size=4)
    
    def w64(self, value, offset=0):
        self._write_integer(value, offset, size=8)
    
    def wf32(self, value, offset=0):
        cp = ctypes.pointer(ctypes.c_float(value))
        up = ctypes.cast(cp, ctypes.POINTER(ctypes.c_uint32))
        self._write_integer(up.contents.value, offset, size=4)    
    
    def wf64(self, value, offset=0):
        cp = ctypes.pointer(ctypes.c_double(value))
        up = ctypes.cast(cp, ctypes.POINTER(ctypes.c_uint64))
        self._write_integer(up.contents.value, offset, size=8)    
    
    def wfloat(self, value, offset=0):
        self.wf32(value, offset)
    
    def wdouble(self, value, offset=0):
        self.wf64(value, offset)
    
    def wbytes(self, value, offset=0):
        self._write_bytes(value, offset)
    
    def wptr(self, value, offset=0):
        self._write_integer(value, offset, size=self.dat.ptrsize)
    
    def write(self, type, value, offset=0):
        return {
            BDType.S8       : self.w8,
            BDType.S16      : self.w16,
            BDType.S32      : self.w32,
            BDType.S64      : self.w64,
            BDType.U8       : self.w8,
            BDType.U16      : self.w16,
            BDType.U32      : self.w32,
            BDType.U64      : self.w64,
            BDType.FLOAT    : self.wf32,
            BDType.DOUBLE   : self.wf64,
            BDType.BYTES    : self.wbytes,
            BDType.POINTER  : self.wptr
        }[type](value, offset)
    
    # Functions that return new BDViews relative to this BDView.
    
    def offset(self, o):
        """Returns a new BDView at this view's address + the given offset."""
        return BDView(self.dat, self.address + o)
    
    def at(self, o):
        """Returns a new BDView at this view's address + the given offset."""
        return self.offset(o)
    
    def indirect(self, o):
        """Returns a new BDView at the address specified by rptr(offset)."""
        return BDView(self.dat, self.rptr(o))
        
    def __getitem__(self, key):
        """Returns a new BDView at the address specified by rptr(offset)."""
        return self.indirect(key)
       
# A single range of read/write memory stored in a BDStore.
class BDRange(object):
    def __init__(self, data, offset, bounds=None):
        """Constructs a BDRange from an external data source.
        
        Args:
        - data (bytes) - The data to be stored in this range.
        - offset (int) - The offset used to reference this range in a BDStore.
        - bounds (tuple of 2 ints) - Optional; if provided, will construct
          the range from a slice of the provided data (if the second value is
          0, uses a left-sided slice; e.g. (-4, 0) -> data[-4:]).
        """
        if not bounds:
            self.data = bytearray(data)
        elif len(bounds) == 2:
            if bounds[1]:
                self.data = bytearray(data[bounds[0]:bounds[1]])
            else:
                self.data = bytearray(data[bounds[0]:])
        else:
            raise BDError("BDRange bounds must be a 2-tuple of integers:" + 
                str(bounds))
        self.offset = offset
        
# The main class meant for public interface; holds a list of BDRanges,
# each representing a read/writable range of memory starting at a given offset.
class BDStore(object):
    def __init__(self, big_endian=False, ptrsize=4):
        self.mem = []  # List of BDRanges.
        self.big_endian = big_endian
        self.ptrsize = ptrsize
        
    def _list_ranges(self):
        bss = []
        max_offset = max([b.offset + len(b.data) for b in self.mem])
        max_digits = max(8, len(hex(max_offset))-2)
        for b in self.mem:
            # Print the start and end offset of the range.
            bs = "{start:0{digits:d}x} {end:0{digits:d}x} ".format(
                digits=max_digits, start=b.offset, end=b.offset + len(b.data))
            # Print a preivew of bytes in the range.
            if len(b.data) <= 16:
                # If the range is short, print the entire range.
                bs += " ".join(["%02x" % ch for ch in b.data])
            else:
                # Else, print the first few bytes and the last few bytes.
                bs += " ".join(["%02x" % ch for ch in b.data[:10]])
                bs += " ..... "
                bs += " ".join(["%02x" % ch for ch in b.data[-4:]])
            bss.append(bs)
        return "\n".join(bss)
        
    def _str_representation(self):
        s = "<BDStore obj>"
        bl = self._list_ranges()
        if bl: s += ", Ranges:\n%s" % bl
        return s
    
    def __str__(self):
        return self._str_representation()
    
    def __repr__(self):
        return self._str_representation()
        
    def view(self, address):
        """Returns a BDView on this store at a given address."""
        return BDView(self, address)
        
    def at(self, address):
        """Returns a BDView on this store at a given address."""
        return BDView(self, address)
    
    def RegisterData(self, data, offset=0, ranges=None):
        """Registers the provided data as one or more BDRanges.
        
        Args:
        - data (bytes) - The data to create ranges over.
        - offset (int) - The offset used to reference this data's range.
        - ranges (list of (offset, bounds-start, bounds-end) tuples) - Optional;
          if provided, will construct multiple ranges over the data.
          
        Will throw an error if the mapped offsets of a newly created range
        overlaps any existing range's mapped offsets.
        """
        bdranges = []
        if ranges is None:
            bdranges.append(BDRange(data, offset))
        else:
            for t in ranges:
                if len(t) != 3:
                    raise BDError(
                        "'ranges' must be a list of tuples of the form "
                        "(offset, bounds-start, bounds-end).")
                bdranges.append(BDRange(data, t[0], (t[1], t[2])))
        for b in bdranges:
            if len(b.data) < 1:
                continue
            for bb in self.mem:
                # If ranges overlap, throw error.
                if (b.offset < bb.offset + len(bb.data) and
                    bb.offset < b.offset + len(b.data)):
                   raise BDError("Cannot create overlapping BDRanges.")
            self.mem.append(b)

    def RegisterFile(self, filename, offset=0, ranges=None):
        """Registers the provided file's data as one or more BDRanges.
        
        Args:
        - filename (str) - The filename whose data to create ranges over.
        - offset (int) - The offset used to reference this data's range.
        - ranges (list of (offset, bounds-start, bounds-end) tuples) - Optional;
          if provided, will construct multiple ranges over the data.
          
        Will throw an error if the mapped offsets of a newly created range
        overlaps any existing range's mapped offsets.
        """
        data = open(filename, "rb").read()
        self.RegisterData(data, offset, ranges)
