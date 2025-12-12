# cython: language_level=3
from libc.stdint cimport uint8_t, int64_t, uint32_t, uint64_t
from libc.string cimport memcpy, strlen
from cpython.buffer cimport PyObject_GetBuffer, PyBuffer_Release, Py_buffer
from cpython.ref cimport Py_INCREF, Py_DECREF
from cpython.object cimport PyObject

import json

cdef extern from "lite3.h":
    ctypedef unsigned char uint8_t
    
    # Use 'enum lite3_type' effectively by tricking Cython to use the right name or just 'enum'
    cdef enum lite3_type:
        LITE3_TYPE_NULL
        LITE3_TYPE_BOOL
        LITE3_TYPE_I64
        LITE3_TYPE_F64
        LITE3_TYPE_BYTES
        LITE3_TYPE_STRING
        LITE3_TYPE_OBJECT
        LITE3_TYPE_ARRAY
        LITE3_TYPE_INVALID

    ctypedef struct lite3_val:
        uint8_t type
        uint8_t val[]

    ctypedef struct lite3_str:
        uint32_t len
        const char *ptr

    ctypedef struct lite3_bytes:
        uint32_t len
        const unsigned char *ptr

    ctypedef struct lite3_key_data:
        uint32_t hash
        uint32_t size

    lite3_key_data lite3_get_key_data(const char *key)

    # Note: lite3_count takes non-const buf in header but treats as const usually
    int lite3_count(unsigned char *buf, size_t buflen, size_t ofs, uint32_t *out)
    
    # Generic get implementation (avoid macro with return statement)
    # The actual implementation function is lite3_get_impl
    int lite3_get_impl(const uint8_t *buf, size_t buflen, size_t ofs, const char *key, lite3_key_data key_data, lite3_val **out)
    
    # Array getters by index
    int lite3_arr_get_bool(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, bint *out)
    int lite3_arr_get_i64(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, int64_t *out)
    int lite3_arr_get_f64(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, double *out)
    int lite3_arr_get_str(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, lite3_str *out)
    int lite3_arr_get_bytes(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, lite3_bytes *out)
    int lite3_arr_get_obj(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, size_t *out_ofs)
    int lite3_arr_get_arr(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, size_t *out_ofs)

    # Helper to check type/existence
    lite3_type lite3_get_type(const uint8_t *buf, size_t buflen, size_t ofs, const char *key)

    # Writer API
    # Using macros from header, so signature must match macro (no key_data passed explicitly)
    int lite3_init_obj(unsigned char *buf, size_t *out_buflen, size_t bufsz)
    int lite3_set_i64(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, int64_t value)
    int lite3_set_str(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, const char *str)

cdef class Lite3Object:
    """
    Lazy proxy for Lite3 data.
    """
    cdef:
        object _owner      # Keep the underlying buffer alive
        const uint8_t* _ptr # Raw pointer to the start of the buffer
        size_t _len        # Total length of the buffer
        size_t _ofs        # Offset of THIS object/element within the buffer
        lite3_type _type_cache # Cache the type of this element to avoid re-calls

    def __init__(self, data, size_t offset=0, lite3_type type_hint=LITE3_TYPE_INVALID):
        """
        Internal constructor. Use loads() or internal creation.
        """
        # We expect 'data' to be a bytes-like object (or our _owner)
        self._owner = data
        
        cdef Py_buffer pybuf
        PyObject_GetBuffer(data, &pybuf, 0) # Simple buffer request
        self._ptr = <const uint8_t*>pybuf.buf
        self._len = <size_t>pybuf.len
        PyBuffer_Release(&pybuf)
        
        self._ofs = offset
        
        if type_hint == LITE3_TYPE_INVALID:
            # Detect type from the byte at offset
            if self._ofs < self._len:
                # Type tag is the first byte, unless it's implicit in a node?
                # Actually, lite3 values are tagged.
                # But for root, or results from get_obj, we point to the start of the value?
                # Wait, lite3_get_obj returns offset of the VALUE (tag + payload)?
                # No, lite3_val struct includes type.
                # So the byte at _ofs IS the type tag.
                self._type_cache = <lite3_type>(self._ptr[self._ofs])
            else:
                self._type_cache = LITE3_TYPE_INVALID
        else:
            self._type_cache = type_hint

    @property
    def is_null(self):
        return self._type_cache == LITE3_TYPE_NULL

    @property
    def is_bool(self):
        return self._type_cache == LITE3_TYPE_BOOL

    @property
    def is_int(self):
        return self._type_cache == LITE3_TYPE_I64
        
    @property
    def is_float(self):
        return self._type_cache == LITE3_TYPE_F64
        
    @property
    def is_str(self):
        return self._type_cache == LITE3_TYPE_STRING
        
    @property
    def is_bytes(self):
        return self._type_cache == LITE3_TYPE_BYTES
        
    @property
    def is_object(self):
        return self._type_cache == LITE3_TYPE_OBJECT

    @property
    def is_array(self):
        return self._type_cache == LITE3_TYPE_ARRAY

    def __getitem__(self, key):
        if self._type_cache == LITE3_TYPE_OBJECT:
            if not isinstance(key, str):
                raise TypeError("Object keys must be strings")
            return self._get_obj_item_by_key(key)
        elif self._type_cache == LITE3_TYPE_ARRAY:
            if isinstance(key, int):
                return self._get_arr_item_by_index(key)
            elif isinstance(key, slice):
                # TODO: Implement slicing
                raise NotImplementedError("Slicing not yet supported")
            else:
                raise TypeError("Array indices must be integers")
        else:
            raise TypeError("Scalar Lite3Object is validation NOT subscriptable")

    cdef object _get_obj_item_by_key(self, str key):
        cdef:
            bytes k_bytes = key.encode('utf-8')
            const char* k_cstr = k_bytes
            lite3_val *val = NULL
            int ret
        
        # We need to use generic lite3_get to find the value pointer
        # Manually compute key data hash to avoid macro expansion issues
        cdef lite3_key_data kd = lite3_get_key_data(k_cstr)
        ret = lite3_get_impl(self._ptr, self._len, self._ofs, k_cstr, kd, &val)
        if ret < 0:
            raise KeyError(key) # Or more specific error based on errno?

        # Now we have a pointer to the value inside the buffer.
        # We need to determine its type and return appropriate Python object or Proxy.
        return self._materialize_val(val)

    cdef object _get_arr_item_by_index(self, int index):
        cdef:
            uint32_t idx = <uint32_t>index
            int ret
            int64_t i_val
            double f_val
            bint b_val
            lite3_str s_val
            lite3_bytes by_val
            size_t sub_ofs
        
        # Check bounds? lite3 functions do it.
        # But for 'len' check we can do it in Python to be nicer?
        # Let's rely on C API for now or cached len.
        
        # We don't know the type at the index easily without retrieving it?
        # Actually lite3_arr_get_* assumes we know the type.
        # But we don't.
        # We need a generic "get by index" for arrays.
        # lite3.h did not expose `lite3_arr_get` (generic). 
        # But `_lite3_get_by_index` was in the header! It's static inline.
        # I can wrap it in a C helper or assume I can access it?
        # Static inline functions ARE visible to Cython if I declare them!
        # Re-checking header... `_lite3_get_by_index` is there.
        # I will declare `_lite3_get_by_index` in the extern block.
        
        cdef lite3_val *val = NULL
        ret = _lite3_get_by_index(self._ptr, self._len, self._ofs, idx, &val)
        if ret < 0:
             raise IndexError(f"List index out of range: {index}")
             
        return self._materialize_val(val)

    cdef object _materialize_val(self, lite3_val *val):
        # Convert a single lite3_val* to Python/Proxy
        cdef lite3_type t = <lite3_type>val.type
        cdef size_t sub_ofs = <size_t>(<uint8_t*>val - self._ptr)
        
        if t == LITE3_TYPE_NULL:
            return None
        elif t == LITE3_TYPE_BOOL:
             # val->val is uint8_t[]
             return bool((<uint8_t*>val.val)[0])
        elif t == LITE3_TYPE_I64:
             return (<int64_t*>val.val)[0]
        elif t == LITE3_TYPE_F64:
             return (<double*>val.val)[0]
        elif t == LITE3_TYPE_STRING:
             # We need to perform string copy
             # Struct layout for STRING is (len (4 bytes), chars...)
             # But let's use the layout from header if possible or manual
             # lite3_type_sizes[STRING] is 4.
             # So val.val starts with 4-byte len?
             # Let's look at `lite3_val_str` or similar logic in header.
             # `lite3_get_str` does `memcpy(&out->len, val->val, ...)`
             # So yes, first 4 bytes at val->val is len.
             # Then chars follow.
             return (<char*>(val.val + 4))[:(<uint32_t*>val.val)[0] - 1].decode('utf-8')
             # Note: -1 because simple C-string length includes NULL?
             # Header says: `lite3_set_str` includes NULL. `lite3_get_str` decrements length.
        elif t == LITE3_TYPE_BYTES:
             return (<unsigned char*>(val.val + 4))[:(<uint32_t*>val.val)[0]]
        elif t == LITE3_TYPE_OBJECT:
             return Lite3Object(self._owner, sub_ofs, LITE3_TYPE_OBJECT)
        elif t == LITE3_TYPE_ARRAY:
             return Lite3Object(self._owner, sub_ofs, LITE3_TYPE_ARRAY)
        else:
             raise ValueError(f"Unknown type: {t}")

    def __len__(self):
        cdef uint32_t count = 0
        if self._type_cache in (LITE3_TYPE_OBJECT, LITE3_TYPE_ARRAY):
            if lite3_count(<unsigned char*>self._ptr, self._len, self._ofs, &count) == 0:
                return count
        return 0

    def __iter__(self):
        if self._type_cache == LITE3_TYPE_ARRAY:
             # Iterator for array: yield items
             for i in range(len(self)):
                 yield self[i]
        elif self._type_cache == LITE3_TYPE_OBJECT:
             # Spec requires yielding KEYS.
             # We don't have a public API for iterating keys yet.
             # We will raise NotImplementedError for now.
             raise NotImplementedError("Iterating keys of Lite3Object is not yet supported")
        else:
             raise TypeError("Scalar Lite3Object is not iterable")

    def to_python(self):
        """
        Recursively convert to standard Python objects (dict/list).
        PRO-TIP: Use as_dict() or as_list() for clarity if type is known.
        """
        if self._type_cache == LITE3_TYPE_ARRAY:
            return [x.to_python() if isinstance(x, Lite3Object) else x for x in self]
        elif self._type_cache == LITE3_TYPE_OBJECT:
            # We can't iterate keys yet! So we can't dump to dict!
            # This is a blocker for to_python() on Objects.
            raise NotImplementedError("Cannot convert Object to dict (key iteration missing)")
        else:
            return self._materialize_scalar()

    def as_dict(self):
        """Reflect access as dict (recursive)"""
        if self._type_cache != LITE3_TYPE_OBJECT:
             raise TypeError("Not an object")
        return self.to_python()
        
    def as_list(self):
        """Reflect access as list (recursive)"""
        if self._type_cache != LITE3_TYPE_ARRAY:
             raise TypeError("Not an array")
        return self.to_python()

    cdef object _materialize_scalar(self):
         # For scalars, to_python just returns the value (which is already Python)
         # But for internal use
         pass

    def __repr__(self):
        return f"<Lite3Object type={self._type_cache} offset={self._ofs}>"


# Need to expose the static inline function from header
cdef extern from "lite3.h":
    int _lite3_get_by_index(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, lite3_val **out)

def loads(data, bint recursive=False):
    """
    Load lite3 data.
    
    Args:
        data: bytes-like object containing lite3 encoded data.
        recursive: If True, fully decode into Python dict/list/scalars immediately.
                   If False (default), return a lazy Lite3Object proxy.
    """
    obj = Lite3Object(data)
    if recursive:
        return obj.to_python()
    return obj

def dumps(obj):
    """
    Serialize a Python dict into lite3 bytes.
    Currently only supports flat dicts with int/str values for testing.
    """
    cdef size_t bufsz = 1024 * 1024 # 1MB buffer for now
    cdef bytearray buf = bytearray(bufsz)
    cdef unsigned char* ptr = buf
    cdef size_t used_len = 0
    cdef int ret
    cdef const char* k_ptr
    cdef const char* v_ptr
    cdef bytes k_enc
    cdef bytes v_enc

    # Initialize generic object
    if lite3_init_obj(ptr, &used_len, bufsz) < 0:
        raise RuntimeError("Failed to init lite3 object")

    if not isinstance(obj, dict):
        raise TypeError("Input must be a dict")

    for k, v in obj.items():
        if not isinstance(k, str):
             raise TypeError("Keys must be strings")
        
        k_enc = k.encode('utf-8')
        k_ptr = k_enc
        
        if isinstance(v, int):
            if lite3_set_i64(ptr, &used_len, 0, bufsz, k_ptr, v) < 0:
                 raise RuntimeError(f"Failed to set int key {k}")
        elif isinstance(v, str):
            v_enc = v.encode('utf-8')
            v_ptr = v_enc
            if lite3_set_str(ptr, &used_len, 0, bufsz, k_ptr, v_ptr) < 0:
                 raise RuntimeError(f"Failed to set str key {k}")
        else:
            # Skip unsupported for now
            pass
            
    return buf[:used_len]
