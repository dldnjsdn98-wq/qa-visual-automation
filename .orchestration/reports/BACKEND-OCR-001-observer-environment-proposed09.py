import os


def child_environment(scratch):
    # Allowlist, never a copy of os.environ. Neither DB credentials, HOME,
    # PYTHONPATH nor .env discovery context is inherited by the child.
    result = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
    result.update(TEMP=scratch, TMP=scratch, HOME=scratch, USERPROFILE=scratch,
                  OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                  PYTHONDONTWRITEBYTECODE="1", PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK="True")
    for key in ("QA_OCR_MODEL_ROOT", "PADDLE_HOME", "PADDLE_PDX_CACHE_HOME"):
        if key in os.environ:
            result[key] = os.path.abspath(os.environ[key])
    return result
