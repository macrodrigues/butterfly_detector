UFunc API
=========

.. sectionauthor:: Travis E. Oliphant

.. index::
   pair: ufunc; C-API


Constants
---------

.. c:var:: UFUNC_ERR_{HANDLER}

    ``{HANDLER}`` can be **IGNORE**, **WARN**, **RAISE**, or **CALL**

.. c:var:: UFUNC_{THING}_{ERR}

    ``{THING}`` can be **MASK**, **SHIFT**, or **FPE**, and ``{ERR}`` can
    be **DIVIDEBYZERO**, **OVERFLOW**, **UNDERFLOW**, and **INVALID**.

.. c:var:: PyUFunc_{VALUE}

    .. c:var:: PyUFunc_One

    .. c:var:: PyUFunc_Zero

    .. c:var:: PyUFunc_MinusOne

    .. c:var:: PyUFunc_ReorderableNone

    .. c:var:: PyUFunc_None

    .. c:var:: PyUFunc_IdentityValue


Macros
------

.. c:macro:: NPY_LOOP_BEGIN_THREADS

    Used in universal function code to only release the Python GIL if
    loop->obj is not true (*i.e.* this is not an OBJECT array
    loop). Requires use of :c:macro:`NPY_BEGIN_THREADS_DEF` in variable
    declaration area.

.. c:macro:: NPY_LOOP_END_THREADS

    Used in universal function code to re-acquire the Python GIL if it
    was released (because loop->obj was not true).


Functions
---------

.. c:function:: PyObject* PyUFunc_FromFuncAndData( \
        PyUFuncGenericFunction* func, void** data, char* types, int ntypes, \
        int nin, int nout, int identity, char* name, char* doc, int unused)

    Create a new broadcasting universal function from required variables.
    Each ufunc builds around the notion of an element-by-element
    operation. Each ufunc object contains pointers to 1-d loops
    implementing the basic functionality for each supported type.

    .. note::

       The *func*, *data*, *types*, *name*, and *doc* arguments are not
       copied by :c:func:`PyUFunc_FromFuncAndData`. The caller must ensure
       that the memory used by these arrays is not freed as long as the
       ufunc object is alive.

    :param func:
        Must to an array of length *ntypes* containing
        :c:type:`PyUFuncGenericFunction` items. These items are pointers to
        functions that actually implement the underlying
        (element-by-element) function :math:`N` times with the following
        signature:

        .. c:function:: void loopfunc(
                char** args, npy_intp* dimensions, npy_intp* steps, void* data)

            *args*

                An array of pointers to the actual data for the input and output
                arrays. The input arguments are given first followed by the output
                arguments.

            *dimensions*

                A pointer to the size of the dimension over which this function is
                looping.

            *steps*

                A pointer to the number of bytes to jump to get to the
                next element in this dimension for each of the input and
                output arguments.

            *data*

                Arbitrary data (extra arguments, function names, *etc.* )
                that can be stored with the ufunc and will be passed in
                when it is called.

            This is an example of a func specialized for addition of doubles
            returning doubles.

            .. code-block:: c

                static void
                double_add(char **args, npy_intp *dimensions, npy_intp *steps,
                   void *extra)
                {
                    npy_intp i;
                    npy_intp is1 = steps[0], is2 = steps[1];
                    npy_intp os = steps[2], n = dimensions[0];
                    char *i1 = args[0], *i2 = args[1], *op = args[2];
                    for (i = 0; i < n; i++) {
                        *((double *)op) = *((double *)i1) +
                                          *((double *)i2);
                        i1 += is1;
                        i2 += is2;
                        op += os;
                     }
                }

    :param data:
        Should be ``NULL`` or a pointer to an array of size *ntypes*
        . This array may contain arbitrary extra-data to be passed to
        the corresponding loop function in the func array.

    :param types:
       Length ``(nin + nout) * ntypes`` array of ``char`` encoding the
       `numpy.dtype.num` (built-in only) that the corresponding
       function in the ``func`` array accepts. For instance, for a comparison
       ufunc with three ``ntypes``, two ``nin`` and one ``nout``, where the
       first function accepts `numpy.int32` and the the second
       `numpy.int64`, with both returning `numpy.bool_`, ``types`` would
       be ``(char[]) {5, 5, 0, 7, 7, 0}`` since ``NPY_INT32`` is 5,
       ``NPY_INT64`` is 7, and ``NPY_BOOL`` is 0.

       The bit-width names can also be used (e.g. :c:data:`NPY_INT32`,
       :c:data:`NPY_COMPLEX128` ) if desired.

       :ref:`ufuncs.casting` will be used at runtime to find the first
       ``func`` callable by the input/output provided.

    :param ntypes:
        How many different data-type-specific functions the ufunc has implemented.

    :param nin:
        The number of inputs to this operation.

    :param nout:
        The number of outputs

    :param identity:

        Either :c:data:`PyUFunc_One`, :c:data:`PyUFunc_Zero`,
        :c:data:`PyUFunc_MinusOne`, or :c:data:`PyUFunc_None`.
        This specifies what should be returned when
        an empty array is passed to the reduce method of the ufunc.
        The special value :c:data:`PyUFunc_IdentityValue` may only be used with
        the :c:func:`PyUFunc_FromFuncAndDataAndSignatureAndIdentity` method, to
        allow an arbitrary python object to be used as the identity.

    :param name:
        The name for the ufunc as a ``NULL`` terminated string.  Specifying
        a name of 'add' or 'multiply' enables a special behavior for
        integer-typed reductions when no dtype is given. If the input type is an
        integer (or boolean) data type smaller than the size of the `numpy.int_`
        data type, it will be internally upcast to the `numpy.int_` (or
        `numpy.uint`) data type.

    :param doc:
        Allows passing in a documentation string to be stored with the
        ufunc.  The documentation string should not contain the name
        of the function or the calling signature as that will be
        dynamically determined from the object and available when
        accessing the **__doc__** attribute of the ufunc.

    :param unused:
        Unused and present for backwards compatibility of the C-API.

.. c:function:: PyObject* PyUFunc_FromFuncAndDataAndSignature( \
        PyUFuncGenericFunction* func, void** data, char* types, int ntypes, \
        int nin, int nout, int identity, char* name, char* doc, int unused, char *signature)

   This function is very similar to PyUFunc_FromFuncAndData above, but has
   an extra *signature* argument, to define a
   :ref:`generalized universal functions <c-api.generalized-ufuncs>`.
   Similarly to how ufuncs are built around an element-by-element operation,
   gufuncs are around subarray-by-subarray operations, the
   :ref:`signature <details-of-signature>` defining the subarrays to operate on.

   :param signature:
        The signature for the new gufunc. Setting it to NULL is equivalent
        to calling PyUFunc_FromFuncAndData. A copy of the string is made,
        so the passed in buffer can be freed.

.. c:function:: PyObject* PyUFunc_FromFuncAndDataAndSignatureAndIdentity( \
        PyUFuncGenericFunction *func, void **data, char *types, int ntypes, \
        int nin, int nout, int identity, char *name, char *doc, int unused, \
        char *signature, PyObject *identity_value)

   This function is very similar to `PyUFunc_FromFuncAndDataAndSignature` above,
   but has an extra *identity_value* argument, to define an arbitrary identity
   for the ufunc when ``identity`` is passed as ``PyUFunc_IdentityValue``.

   :param identity_value:
        The identity for the new gufunc. Must be passed as ``NULL`` unless the
        ``identity`` argument is ``PyUFunc_IdentityValue``. Setting it to NULL
        is equivalent to calling PyUFunc_FromFuncAndDataAndSignature.


.. c:function:: int PyUFunc_RegisterLoopForType( \
        PyUFuncObject* ufunc, int usertype, PyUFuncGenericFunction function, \
        int* arg_types, void* data)

    This function allows the user to register a 1-d loop with an
    already- created ufunc to be used whenever the ufunc is called
    with any of its input arguments as the user-defined
    data-type. This is needed in order to make ufuncs work with
    built-in data-types. The data-type must have been previously
    registered with the numpy system. The loop is passed in as
    *function*. This loop can take arbitrary data which should be
    passed in as *data*. The data-types the loop requires are passed
    in as *arg_types* which must be a pointer to memory at least as
    large as ufunc->nargs.

.. c:function:: int PyUFunc_RegisterLoopForDescr( \
        PyUFuncObject* ufunc, PyArray_Descr* userdtype, \
        PyUFuncGenericFunction function, PyArray_Descr** arg_dtypes, void* data)

   This function behaves like PyUFunc_RegisterLoopForType above, except
   that it allows the user to register a 1-d loop using PyArray_Descr
   objects instead of dtype type num values. This allows a 1-d loop to be
   registered for structured array data-dtypes and custom data-types
   instead of scalar data-types.

.. c:function:: int PyUFunc_ReplaceLoopBySignature( \
        PyUFuncObject* ufunc, PyUFuncGenericFunction newfunc, int* signature, \
        PyUFuncGenericFunction* oldfunc)

    Replace a 1-d loop matching the given *signature* in the
    already-created *ufunc* with the new 1-d loop newfunc. Return the
    old 1-d loop function in *oldfunc*. Return 0 on success and -1 on
    failure. This function works only with built-in types (use
    :c:func:`PyUFunc_RegisterLoopForType` for user-defined types). A
    signature is an array of data-type numbers indicating the inputs
    followed by the outputs assumed by the 1-d loop.

.. c:function:: int PyUFunc_GenericFunction( \
        PyUFuncObject* self, PyObject* args, PyObject* kwds, PyArrayObject** mps)

    A generic ufunc call. The ufunc is passed in as *self*, the arguments
    to the ufunc as *args* and *kwds*. The *mps* argument is an array of
    :c:type:`PyArrayObject` pointers whose values are discarded and which
    receive the converted input arguments as well as the ufunc outputs
    when success is returned. The user is responsible for managing this
    array and receives a new reference for each array in *mps*. The total
    number of arrays in *mps* is given by *self* ->nin + *self* ->nout.

    Returns 0 on success, -1 on error.

.. c:function:: int PyUFunc_checkfperr(int errmask, PyObject* errobj)

    A simple interface to the IEEE error-flag checking support. The
    *errmask* argument is a mask of :c:data:`UFUNC_MASK_{ERR}` bitmasks
    indicating which errors to check for (and how to check for
    them). The *errobj* must be a Python tuple with two elements: a
    string containing the name which will be used in any communication
    of error and either a callable Python object (call-back function)
    or :c:data:`Py_None`. The callable object will only be used if
    :c:data:`UFUNC_ERR_CALL` is set as the desired error checking
    method. This routine manages the GIL and is safe to call even
    after releasing the GIL. If an error in the IEEE-compatible
    hardware is determined a -1 is returned, otherwise a 0 is
    returned.

.. c:function:: void PyUFunc_clearfperr()

    Clear the IEEE error flags.

.. c:function:: void PyUFunc_GetPyValues( \
        char* name, int* bufsize, int* errmask, PyObject** errobj)

    Get the Python values used for ufunc processing from the
    thread-local storage area unless the defaults have been set in
    which case the name lookup is bypassed. The name is placed as a
    string in the first element of *\*errobj*. The second element is
    the looked-up function to call on error callback. The value of the
    looked-up buffer-size to use is passed into *bufsize*, and the
    value of the error mask is placed into *errmask*.


Generic functions
-----------------

At the core of every ufunc is a collection of type-specific functions
that defines the basic functionality for each of the supported types.
These functions must evaluate the underlying function :math:`N\geq1`
times. Extra-data may be passed in that may be used during the
calculation. This feature allows some general functions to be used as
these basic looping functions. The general function has all the code
needed to point variables to the right place and set up a function
call. The general function assumes that the actual function to call is
passed in as the extra data and calls it with the correct values. All
of these functions are suitable for placing directly in the array of
functions stored in the functions member of the PyUFuncObject
structure.

.. c:function:: void PyUFunc_f_f_As_d_d( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_d_d( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_f_f( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_g_g( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_F_F_As_D_D( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_F_F( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_D_D( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_G_G( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_e_e( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_e_e_As_f_f( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_e_e_As_d_d( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

    Type specific, core 1-d functions for ufuncs where each
    calculation is obtained by calling a function taking one input
    argument and returning one output. This function is passed in
    ``func``. The letters correspond to dtypechar's of the supported
    data types ( ``e`` - half, ``f`` - float, ``d`` - double,
    ``g`` - long double, ``F`` - cfloat, ``D`` - cdouble,
    ``G`` - clongdouble). The argument *func* must support the same
    signature. The _As_X_X variants assume ndarray's of one data type
    but cast the values to use an underlying function that takes a
    different data type. Thus, :c:func:`PyUFunc_f_f_As_d_d` uses
    ndarrays of data type :c:data:`NPY_FLOAT` but calls out to a
    C-function that takes double and returns double.

.. c:function:: void PyUFunc_ff_f_As_dd_d( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_ff_f( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_dd_d( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_gg_g( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_FF_F_As_DD_D( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_DD_D( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_FF_F( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_GG_G( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_ee_e( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_ee_e_As_ff_f( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_ee_e_As_dd_d( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

    Type specific, core 1-d functions for ufuncs where each
    calculation is obtained by calling a function taking two input
    arguments and returning one output. The underlying function to
    call is passed in as *func*. The letters correspond to
    dtypechar's of the specific data type supported by the
    general-purpose function. The argument ``func`` must support the
    corresponding signature. The ``_As_XX_X`` variants assume ndarrays
    of one data type but cast the values at each iteration of the loop
    to use the underlying function that takes a different data type.

.. c:function:: void PyUFunc_O_O( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

.. c:function:: void PyUFunc_OO_O( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

    One-input, one-output, and two-input, one-output core 1-d functions
    for the :c:data:`NPY_OBJECT` data type. These functions handle reference
    count issues and return early on error. The actual function to call is
    *func* and it must accept calls with the signature ``(PyObject*)
    (PyObject*)`` for :c:func:`PyUFunc_O_O` or ``(PyObject*)(PyObject *,
    PyObject *)`` for :c:func:`PyUFunc_OO_O`.

.. c:function:: void PyUFunc_O_O_method( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

    This general purpose 1-d core function assumes that *func* is a string
    representing a method of the input object. For each
    iteration of the loop, the Python object is extracted from the array
    and its *func* method is called returning the result to the output array.

.. c:function:: void PyUFunc_OO_O_method( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

    This general purpose 1-d core function assumes that *func* is a
    string representing a method of the input object that takes one
    argument. The first argument in *args* is the method whose function is
    called, the second argument in *args* is the argument passed to the
    function. The output of the function is stored in the third entry
    of *args*.

.. c:function:: void PyUFunc_On_Om( \
        char** args, npy_intp* dimensions, npy_intp* steps, void* func)

    This is the 1-d core function used by the dynamic ufuncs created
    by umath.frompyfunc(function, nin, nout). In this case *func* is a
    pointer to a :c:type:`PyUFunc_PyFuncData` structure which has definition

    .. c:type:: PyUFunc_PyFuncData

       .. code-block:: c

           typedef struct {
               int nin;
               int nout;
               PyObject *callable;
           } PyUFunc_PyFuncData;

    At each iteration of the loop, the *nin* input objects are extracted
    from their object arrays and placed into an argument tuple, the Python
    *callable* is called with the input arguments, and the nout
    outputs are placed into their object arrays.


Importing the API
-----------------

.. c:var:: PY_UFUNC_UNIQUE_SYMBOL

.. c:var:: NO_IMPORT_UFUNC

.. c:function:: void import_ufunc(void)

    These are the constants and functions for accessing the ufunc
    C-API from extension modules in precisely the same way as the
    array C-API can be accessed. The ``import_ufunc`` () function must
    always be called (in the initialization subroutine of the
    extension module). If your extension module is in one file then
    that is all that is required. The other two constants are useful
    if your extension module makes use of multiple files. In that
    case, define :c:data:`PY_UFUNC_UNIQUE_SYMBOL` to something unique to
    your code and then in source files that do not contain the module
    initialization function but still need access to the UFUNC API,
    define :c:data:`PY_UFUNC_UNIQUE_SYMBOL` to the same name used previously
    and also define :c:data:`NO_IMPORT_UFUNC`.

    The C-API is actually an array of function pointers. This array is
    created (and pointed to by a global variable) by import_ufunc. The
    global variable is either statically defined or allowed to be seen
    by other files depending on the state of
    :c:data:`PY_UFUNC_UNIQUE_SYMBOL` and :c:data:`NO_IMPORT_UFUNC`.

.. index::
   pair: ufunc; C-API
