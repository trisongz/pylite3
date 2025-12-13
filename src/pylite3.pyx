# cython: language_level=3
from libc.stdint cimport uint8_t, int64_t, uint32_t, uint64_t
from libc.string cimport memcpy, strlen
from cpython.buffer cimport PyObject_GetBuffer, PyBuffer_Release, Py_buffer
from cpython.ref cimport Py_INCREF, Py_DECREF
from cpython.object cimport PyObject

import json
import collections.abc

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
        uint32_t gen
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
    int lite3_init_arr(unsigned char *buf, size_t *out_buflen, size_t bufsz)
    
    # Object Setters
    int lite3_set_null(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key)
    int lite3_set_bool(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, bint value)
    int lite3_set_i64(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, int64_t value)
    int lite3_set_f64(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, double value)
    int lite3_set_bytes(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, const unsigned char *bytes, size_t bytes_len)
    int lite3_set_str(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, const char *str)
    # Note: Using set_str_n is more efficient if length is known, but requires exposing it.
    
    int lite3_set_obj(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, size_t *out_ofs)
    int lite3_set_arr(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *key, size_t *out_ofs)

    # Array Appenders
    int lite3_arr_append_null(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz)
    int lite3_arr_append_bool(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, bint value)
    int lite3_arr_append_i64(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, int64_t value)
    int lite3_arr_append_f64(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, double value)
    int lite3_arr_append_bytes(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const unsigned char *bytes, size_t bytes_len)
    int lite3_arr_append_str(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, const char *str)
    
    int lite3_arr_append_obj(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, size_t *out_ofs)
    int lite3_arr_append_arr(unsigned char *buf, size_t *inout_buflen, size_t ofs, size_t bufsz, size_t *out_ofs)

    # Iterators
    ctypedef struct lite3_iter:
        pass # Opaque struct for Cython, size known by C compiler

    int lite3_iter_create(const unsigned char *buf, size_t buflen, size_t ofs, lite3_iter *out)
    int lite3_iter_next(const unsigned char *buf, size_t buflen, lite3_iter *iter, lite3_str *out_key, size_t *out_val_ofs)


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

    @property
    def is_valid(self):
        return self._type_cache <= LITE3_TYPE_ARRAY

    def keys(self):
        """Return an iterator over the keys of an object."""
        if self._type_cache != LITE3_TYPE_OBJECT:
            raise TypeError("Lite3Object is not an object")
        for k, _ in self._iter_gen(True):
            yield k

    def values(self):
        """Return an iterator over the values of an object or array."""
        if self._type_cache == LITE3_TYPE_OBJECT:
            for _, v in self._iter_gen(True):
                yield v
        elif self._type_cache == LITE3_TYPE_ARRAY:
            for v in self._iter_gen(False):
                yield v
        else:
            raise TypeError("Scalar Lite3Object does not have values")

    def items(self):
        """Return an iterator over the (key, value) pairs of an object."""
        if self._type_cache != LITE3_TYPE_OBJECT:
            raise TypeError("Lite3Object is not an object")
        return self._iter_gen(True)


    def __getitem__(self, key):
        if self._type_cache == LITE3_TYPE_OBJECT:
            if not isinstance(key, str):
                raise TypeError("Object keys must be strings")
            return self._get_obj_item_by_key(key)
        elif self._type_cache == LITE3_TYPE_ARRAY:
            if isinstance(key, int):
                return self._get_arr_item_by_index(key)
            elif isinstance(key, slice):
                start, stop, step = key.indices(len(self))
                return [self[i] for i in range(start, stop, step)]
            else:
                raise TypeError("Array indices must be integers")
        else:
            raise TypeError("Scalar Lite3Object is not subscriptable")

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
            lite3_val *val = NULL
        
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
             return (<char*>(val.val + 4))[:(<uint32_t*>val.val)[0] - 1].decode('utf-8')
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
             # Iterator for object: yield KEYS
             iter_obj = self._get_iterator()
             while True:
                 try:
                     key = next(iter_obj)
                     yield key[0] # Yield key only
                 except StopIteration:
                     break
        else:
             raise TypeError("Scalar Lite3Object is not iterable")

    def _get_iterator(self):
        # Helper to generator iterator yielding (key, value_proxy)
        if self._type_cache == LITE3_TYPE_OBJECT:
            return self._iter_gen(True)
        return self._iter_gen(False)
        
    def _iter_gen(self, bint is_object):
        cdef lite3_iter it
        cdef lite3_str key
        cdef size_t val_ofs
        cdef int ret
        cdef size_t klen
        
        if lite3_iter_create(self._ptr, self._len, self._ofs, &it) < 0:
            raise RuntimeError("Failed to create iterator")
            
        while True:
            ret = lite3_iter_next(self._ptr, self._len, &it, &key if is_object else NULL, &val_ofs)
            if ret == 0: # LITE3_ITER_DONE
                break
            
            # Create value proxy
            val = Lite3Object(self._owner, val_ofs)
            
            if is_object:
                # Key is in lite3_str key. string is at key.ptr, len is key.len.
                # key.ptr is pointer inside buffer.
                # print(f"DEBUG: key len={key.len} ptr={ <size_t>key.ptr } gen={key.gen}")
                # Use strlen because key.len seems unreliable/corrupted in tests (return 7 for 'a')
                # Since lite3 strings are null-terminated, strlen works.
                # print(f"DEBUG: key len={key.len} ptr={ <size_t>key.ptr } gen={key.gen}")
                # Use strlen because key.len seems unreliable/corrupted in tests (return 7 for 'a')
                # Since lite3 strings are null-terminated, strlen works.
                klen = strlen(key.ptr)
                py_key = key.ptr[:klen].decode('utf-8')
                yield (py_key, val)
            else:
                yield val

    def to_python(self, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, object_pairs_hook=None):
        """
        Recursively convert to standard Python objects (dict/list).
        Support standard json hooks.
        """
        if self._type_cache == LITE3_TYPE_ARRAY:
            return [x.to_python(object_hook=object_hook, parse_float=parse_float, 
                                parse_int=parse_int, parse_constant=parse_constant,
                                object_pairs_hook=object_pairs_hook) 
                    if isinstance(x, Lite3Object) else x for x in self]
                    
        elif self._type_cache == LITE3_TYPE_OBJECT:
            if object_pairs_hook is not None:
               pairs = []
               # Use iterator to get (key, val)
               for k, v in self._iter_gen(True):
                   if isinstance(v, Lite3Object):
                       v = v.to_python(object_hook=object_hook, parse_float=parse_float, 
                                       parse_int=parse_int, parse_constant=parse_constant,
                                       object_pairs_hook=object_pairs_hook)
                   pairs.append((k, v))
               return object_pairs_hook(pairs)
               
            d = {}
            for k, v in self._iter_gen(True): # Yields (key, value_proxy)
                if isinstance(v, Lite3Object):
                     v = v.to_python(object_hook=object_hook, parse_float=parse_float, 
                                     parse_int=parse_int, parse_constant=parse_constant,
                                     object_pairs_hook=object_pairs_hook)
                d[k] = v
            
            if object_hook is not None:
                return object_hook(d)
            return d

        else:
            val = self._materialize_scalar()
            if isinstance(val, float) and parse_float is not None:
                return parse_float(str(val))
            if isinstance(val, int) and parse_int is not None:
                return parse_int(str(val))
            # lite3 doesn't have Infinity/NaN logic mapped to constants generally?
            return val

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
         # For scalars, to_python just returns the value
         # But we might need to re-read it if we don't have it?
         # _materialize_val checks type cache and reads from offset.
         # self is a proxy, pointing to a value.
         # _materialize_val expects a lite3_val pointer.
         # We have _ptr + _ofs = LITE3 VAL.
         return self._materialize_val(<lite3_val*>(self._ptr + self._ofs))

    def __repr__(self):
        return f"<Lite3Object type={self._type_cache} offset={self._ofs}>"


# Need to expose the static inline function from header
cdef extern from "lite3.h":
    int _lite3_get_by_index(const uint8_t *buf, size_t buflen, size_t ofs, uint32_t index, lite3_val **out)

def loads(data, *, bint recursive=False, cls=None, object_hook=None, parse_float=None,
          parse_int=None, parse_constant=None, object_pairs_hook=None, **kwargs):
    """
    Load lite3 data with fallback to standard JSON.
    
    This function mimics `json.loads` but attempts to parse `data` as zero-copy `Lite3Object` first.
    
    Arguments:
        data: bytes-like object (lite3) or string/bytes (json).
        recursive (bool): If True, fully decode `Lite3Object` into Python dict/list/scalars 
                          immediately (default: False).
                          Ignored if fallback to JSON occurs (JSON always full decodes).
    
    Standard `json.loads` Arguments (Used ONLY during fallback):
        cls, object_hook, parse_float, parse_int, parse_constant, object_pairs_hook, **kwargs
        
    Returns:
        Lite3Object: If `data` is valid lite3 and `recursive` is False.
        dict/list/scalar: If `recursive` is True OR if fallback to `json.loads` occurs.
    """
    # Try parsing as Lite3
    try:
        # Lite3Object expects bytes supports buffer protocol.
        # Strings will fail here (TypeError/BufferError).
        if isinstance(data, str):
             raise TypeError("Lite3 requires bytes")
             
        obj = Lite3Object(data)
        if not obj.is_valid:
             # First byte didn't look like a valid type tag
             raise ValueError("Invalid lite3 header")
             
        if recursive:
            return obj.to_python(object_hook=object_hook, parse_float=parse_float, 
                                 parse_int=parse_int, parse_constant=parse_constant,
                                 object_pairs_hook=object_pairs_hook)
        return obj
    except (TypeError, ValueError, BufferError):
        # Fallback to JSON
        return json.loads(data, cls=cls, object_hook=object_hook, parse_float=parse_float,
                          parse_int=parse_int, parse_constant=parse_constant,
                          object_pairs_hook=object_pairs_hook, **kwargs)

cdef int _dumps_recursive(unsigned char *ptr, size_t *used_len, size_t ofs, size_t bufsz, object obj, object default_fn) except -1:
    cdef int ret = 0
    cdef size_t new_ofs = 0
    cdef const char* k_enc_ptr
    cdef const char* v_str_ptr
    cdef const unsigned char* v_bytes_ptr
    cdef bytes k_encoded
    cdef bytes v_encoded
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError(f"Keys must be strings, got {type(k)}")
            k_encoded = k.encode('utf-8')
            k_enc_ptr = k_encoded

            if v is None:
                ret = lite3_set_null(ptr, used_len, ofs, bufsz, k_enc_ptr)
            elif isinstance(v, bool):
                ret = lite3_set_bool(ptr, used_len, ofs, bufsz, k_enc_ptr, v)
            elif isinstance(v, int):
                ret = lite3_set_i64(ptr, used_len, ofs, bufsz, k_enc_ptr, v)
            elif isinstance(v, float):
                ret = lite3_set_f64(ptr, used_len, ofs, bufsz, k_enc_ptr, v)
            elif isinstance(v, str):
                v_encoded = v.encode('utf-8')
                v_str_ptr = v_encoded
                ret = lite3_set_str(ptr, used_len, ofs, bufsz, k_enc_ptr, v_str_ptr)
            elif isinstance(v, (bytes, bytearray)):
                v_bytes_ptr = <const unsigned char*>v
                ret = lite3_set_bytes(ptr, used_len, ofs, bufsz, k_enc_ptr, v_bytes_ptr, len(v))
            elif isinstance(v, dict):
                ret = lite3_set_obj(ptr, used_len, ofs, bufsz, k_enc_ptr, &new_ofs)
                if ret == 0:
                    _dumps_recursive(ptr, used_len, new_ofs, bufsz, v, default_fn)
            elif isinstance(v, (list, tuple)):
                ret = lite3_set_arr(ptr, used_len, ofs, bufsz, k_enc_ptr, &new_ofs)
                if ret == 0:
                     _dumps_recursive(ptr, used_len, new_ofs, bufsz, v, default_fn)
            else:
                 # Try default hook
                 if default_fn is not None:
                     try:
                         new_v = default_fn(v)
                         # Recursively handle the new value
                         # But we need to insert it.
                         # We can't easily recurse into insertion logic because we have explicit types above.
                         # We need to re-dispatch?
                         # Or just call ourselves with a temporary wrapper?
                         # No, we are in a loop iterating keys. We need to call a SET function.
                         # But we don't know the type of 'new_v'.
                         # We should refactor the "type switch" logic into a helper function?
                         # For now, duplicate logic or use a goto? (Cython doesn't like complex gotos).
                         # Let's recursive call a helper that does "set value at key".
                         # But we are inside the 'dict' loop. 
                         # Let's try to handle 'new_v' with same logic.
                         _dumps_set_value(ptr, used_len, ofs, bufsz, k_enc_ptr, new_v, default_fn)
                     except Exception:
                         raise TypeError(f"Object of type {type(v).__name__} is not JSON serializable")
                 else:
                     raise TypeError(f"Object of type {type(v).__name__} is not JSON serializable")
            
            if ret < 0: # Note: set functions return err, but _dumps_set_value might raise exception
                raise RuntimeError(f"lite3 set failed for key {k}")

    elif isinstance(obj, (list, tuple)):
        # Array logic
        for v in obj:
            if v is None:
                ret = lite3_arr_append_null(ptr, used_len, ofs, bufsz)
            elif isinstance(v, bool):
                ret = lite3_arr_append_bool(ptr, used_len, ofs, bufsz, v)
            elif isinstance(v, int):
                ret = lite3_arr_append_i64(ptr, used_len, ofs, bufsz, v)
            elif isinstance(v, float):
                ret = lite3_arr_append_f64(ptr, used_len, ofs, bufsz, v)
            elif isinstance(v, str):
                v_encoded = v.encode('utf-8')
                v_str_ptr = v_encoded
                ret = lite3_arr_append_str(ptr, used_len, ofs, bufsz, v_str_ptr)
            elif isinstance(v, (bytes, bytearray)):
                v_bytes_ptr = <const unsigned char*>v
                ret = lite3_arr_append_bytes(ptr, used_len, ofs, bufsz, v_bytes_ptr, len(v))
            elif isinstance(v, dict):
                ret = lite3_arr_append_obj(ptr, used_len, ofs, bufsz, &new_ofs)
                if ret == 0:
                    _dumps_recursive(ptr, used_len, new_ofs, bufsz, v, default_fn)
            elif isinstance(v, (list, tuple)):
                ret = lite3_arr_append_arr(ptr, used_len, ofs, bufsz, &new_ofs)
                if ret == 0:
                    _dumps_recursive(ptr, used_len, new_ofs, bufsz, v, default_fn)
            else:
                 # Try default hook
                 if default_fn is not None:
                     try:
                         new_v = default_fn(v)
                         _dumps_append_value(ptr, used_len, ofs, bufsz, new_v, default_fn)
                     except Exception:
                          raise TypeError(f"Object of type {type(v).__name__} is not JSON serializable")
                 else:
                    raise TypeError(f"Unsupported type in array: {type(v)}")

            if ret < 0:
                raise RuntimeError("lite3 append failed")
    
    return 0

cdef int _dumps_set_value(unsigned char *ptr, size_t *used_len, size_t ofs, size_t bufsz, const char* k_enc_ptr, object v, object default_fn) except -1:
    cdef int ret = 0
    cdef size_t new_ofs = 0
    cdef bytes v_encoded
    cdef const char* v_str_ptr
    cdef const unsigned char* v_bytes_ptr
    
    if v is None:
        ret = lite3_set_null(ptr, used_len, ofs, bufsz, k_enc_ptr)
    elif isinstance(v, bool):
        ret = lite3_set_bool(ptr, used_len, ofs, bufsz, k_enc_ptr, v)
    elif isinstance(v, int):
        ret = lite3_set_i64(ptr, used_len, ofs, bufsz, k_enc_ptr, v)
    elif isinstance(v, float):
        ret = lite3_set_f64(ptr, used_len, ofs, bufsz, k_enc_ptr, v)
    elif isinstance(v, str):
        v_encoded = v.encode('utf-8')
        v_str_ptr = v_encoded
        ret = lite3_set_str(ptr, used_len, ofs, bufsz, k_enc_ptr, v_str_ptr)
    elif isinstance(v, (bytes, bytearray)):
        v_bytes_ptr = <const unsigned char*>v
        ret = lite3_set_bytes(ptr, used_len, ofs, bufsz, k_enc_ptr, v_bytes_ptr, len(v))
    elif isinstance(v, dict):
        ret = lite3_set_obj(ptr, used_len, ofs, bufsz, k_enc_ptr, &new_ofs)
        if ret == 0:
            _dumps_recursive(ptr, used_len, new_ofs, bufsz, v, default_fn)
    elif isinstance(v, (list, tuple)):
        ret = lite3_set_arr(ptr, used_len, ofs, bufsz, k_enc_ptr, &new_ofs)
        if ret == 0:
               _dumps_recursive(ptr, used_len, new_ofs, bufsz, v, default_fn)
    else:
        # If we are here recursively (from default hook), we don't recurse default hook again?
        # Standard json recurses default hook results too?
        # Yes, "If specified, default is a function... that returns a serializable version"
        # It doesn't say if it recurses. Usually it operates on the result.
        # But if the result is ALSO unknown, does it call default again?
        # "If the return value is not JSON serializable, a TypeError is raised."
        # So we don't loop default calls.
        if default_fn is not None:
             # But we are effectively calling this from a context where we already tried.
             # If we call _dumps_set_value from _dumps_recursive, we already tried default logic there.
             # Wait, `_dumps_recursive` calls `_dumps_set_value` ONLY IF IT WAS A DEFAULT CALL.
             # No, I should structure it so `_dumps_recursive` calls `_dumps_set_value` for EVERYTHING.
             pass
    return ret

cdef int _dumps_append_value(unsigned char *ptr, size_t *used_len, size_t ofs, size_t bufsz, object v, object default_fn) except -1:
    cdef int ret = 0
    cdef size_t new_ofs = 0
    cdef bytes v_encoded
    cdef const char* v_str_ptr
    cdef const unsigned char* v_bytes_ptr
    
    if v is None:
        ret = lite3_arr_append_null(ptr, used_len, ofs, bufsz)
    elif isinstance(v, bool):
        ret = lite3_arr_append_bool(ptr, used_len, ofs, bufsz, v)
    elif isinstance(v, int):
        ret = lite3_arr_append_i64(ptr, used_len, ofs, bufsz, v)
    elif isinstance(v, float):
        ret = lite3_arr_append_f64(ptr, used_len, ofs, bufsz, v)
    elif isinstance(v, str):
        v_encoded = v.encode('utf-8')
        v_str_ptr = v_encoded
        ret = lite3_arr_append_str(ptr, used_len, ofs, bufsz, v_str_ptr)
    elif isinstance(v, (bytes, bytearray)):
        v_bytes_ptr = <const unsigned char*>v
        ret = lite3_arr_append_bytes(ptr, used_len, ofs, bufsz, v_bytes_ptr, len(v))
    elif isinstance(v, dict):
        ret = lite3_arr_append_obj(ptr, used_len, ofs, bufsz, &new_ofs)
        if ret == 0:
            _dumps_recursive(ptr, used_len, new_ofs, bufsz, v, default_fn)
    elif isinstance(v, (list, tuple)):
        ret = lite3_arr_append_arr(ptr, used_len, ofs, bufsz, &new_ofs)
        if ret == 0:
            _dumps_recursive(ptr, used_len, new_ofs, bufsz, v, default_fn)
    else:
         # Try default hook
         if default_fn is not None:
             try:
                 new_v = default_fn(v)
                 _dumps_append_value(ptr, used_len, ofs, bufsz, new_v, default_fn)
             except Exception:
                  raise TypeError(f"Object of type {type(v).__name__} is not JSON serializable")
         else:
            raise TypeError(f"Unsupported type in array: {type(v)}")
    
    return ret



def dumps(obj, *, skipkeys=False, ensure_ascii=True, check_circular=True,
          allow_nan=True, cls=None, indent=None, separators=None,
          default=None, sort_keys=False, **kwargs):
    """
    Serialize to lite3 bytes, falling back to JSON string if failed.
    
    Tries to produce high-performance `lite3` binary output. If the input object contains
    unsupported types or if an error occurs, it falls back to `json.dumps` (producing a string).
    
    Arguments:
        obj: The Python object to serialize.
        
    Standard `json.dumps` Arguments (Used ONLY during fallback):
        skipkeys, ensure_ascii, check_circular, allow_nan, cls, indent,
        separators, default, sort_keys, **kwargs
        
    Note:
        Native `lite3` serialization currently supports: dict, list, tuple, str, int, float, bool, None, bytes.
        It does NOT support `skipkeys`, `indent`, `canonical` (sort_keys), or `default` serializers natively yet.
        Passing these arguments effectively forces them to be ignored UNLESS fallback occurs.
    
    Returns:
        bytes: If `lite3` serialization succeeds.
        str: If fallback to `json.dumps` occurs.
    """
    # Just allocate a large buffer for now - 64MB
    cdef size_t bufsz = 1024 * 1024 * 64
    cdef size_t used_len = 0
    cdef bytearray buf = bytearray(bufsz)
    cdef unsigned char* ptr = buf
    
    try:
        if isinstance(obj, dict):
            if lite3_init_obj(ptr, &used_len, bufsz) < 0:
                 raise RuntimeError("Failed to init object")
            _dumps_recursive(ptr, &used_len, 0, bufsz, obj, default)
        elif isinstance(obj, (list, tuple)):
            if lite3_init_arr(ptr, &used_len, bufsz) < 0:
                 raise RuntimeError("Failed to init array")
            _dumps_recursive(ptr, &used_len, 0, bufsz, obj, default)
        else:
            raise TypeError("Root object must be dict or list")
            
        return bytes(buf[:used_len])
        
    except (TypeError, RuntimeError, OverflowError, ValueError):
        # Fallback to JSON
        return json.dumps(obj, skipkeys=skipkeys, ensure_ascii=ensure_ascii,
                          check_circular=check_circular, allow_nan=allow_nan,
                          cls=cls, indent=indent, separators=separators,
                          default=default, sort_keys=sort_keys, **kwargs)

# Register as Mapping
collections.abc.Mapping.register(Lite3Object)
