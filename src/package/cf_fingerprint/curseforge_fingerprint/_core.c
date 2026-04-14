#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "fingerprint.h"

static PyObject *py_fingerprint(PyObject *self, PyObject *args) {
    const char *file_path;

    if (!PyArg_ParseTuple(args, "s", &file_path)) {
        return NULL;
    }

    Buffer buffer = get_file_contents(file_path);

    if (buffer.data == NULL) {
        PyErr_SetString(PyExc_FileNotFoundError,
                        "Cannot open file");
        return NULL;
    }

    if (buffer.size == 0) {
        buffer_free(&buffer);
        PyErr_SetString(PyExc_ValueError, "File is empty");
        return NULL;
    }

    uint32_t hash = compute_hash(&buffer);
    buffer_free(&buffer);

    return PyLong_FromUnsignedLong((unsigned long)hash);
}

static PyObject *py_fingerprint_bytes(PyObject *self, PyObject *args) {
    Py_buffer view;

    if (!PyArg_ParseTuple(args, "y*", &view)) {
        return NULL;
    }

    if (view.len == 0) {
        PyBuffer_Release(&view);
        PyErr_SetString(PyExc_ValueError, "Data is empty");
        return NULL;
    }

    Buffer buffer;
    buffer.data = (unsigned char *)view.buf;
    buffer.size = (long)view.len;

    uint32_t hash = compute_hash(&buffer);

    PyBuffer_Release(&view);

    return PyLong_FromUnsignedLong((unsigned long)hash);
}

static PyMethodDef module_methods[] = {
    {"fingerprint", py_fingerprint, METH_VARARGS,
     "fingerprint(file_path)\n\n"
     "Compute the CurseForge fingerprint of a file.\n\n"
     "Args:\n"
     "    file_path (str): Path to the file to fingerprint.\n\n"
     "Returns:\n"
     "    int: The fingerprint value as an unsigned 32-bit integer.\n\n"
     "Raises:\n"
     "    FileNotFoundError: If the file cannot be opened.\n"
     "    ValueError: If the file is empty."},
    {"fingerprint_bytes", py_fingerprint_bytes, METH_VARARGS,
     "fingerprint_bytes(data)\n\n"
     "Compute the CurseForge fingerprint of in-memory bytes data.\n\n"
     "Args:\n"
     "    data (bytes): The byte data to fingerprint.\n\n"
     "Returns:\n"
     "    int: The fingerprint value as an unsigned 32-bit integer.\n\n"
     "Raises:\n"
     "    TypeError: If the argument is not a bytes-like object.\n"
     "    ValueError: If the data is empty."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef core_module = {
    PyModuleDef_HEAD_INIT,
    "_core",
    "CurseForge Fingerprint C Extension Module\n\n"
    "This module provides native C implementations for computing\n"
    "CurseForge-compatible file fingerprints using a MurmurHash3\n"
    "variant algorithm. Whitespace characters (Tab, LF, CR, Space)\n"
    "are filtered before computing the hash.\n\n"
    "Functions:\n"
    "    fingerprint(file_path) -- Compute fingerprint of a file.\n"
    "    fingerprint_bytes(data) -- Compute fingerprint of bytes data.",
    -1,
    module_methods
};

PyMODINIT_FUNC PyInit__core(void) {
    return PyModule_Create(&core_module);
}
