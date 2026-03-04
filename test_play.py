print("Starting script...")
import numpy as np
import tempfile
print("Importing openfisca...")
from openfisca_core import periods
from openfisca_core.data_storage.on_disk_storage import OnDiskStorageZarr

print("Starting test...")
temp_dir = tempfile.mkdtemp()
try:
    print("Initializing Zarr Storage...")
    storage = OnDiskStorageZarr(temp_dir)
    print("Storage initialized successfully.")

    array = np.array([1, 2, 3])
    period = periods.Period(("year", periods.Instant((2017, 1, 1)), 1))

    print("Testing put...")
    storage.put(array, period)
    print("put() success.")

    print("Testing get...")
    retrieved = storage.get(period)
    print("get() success. retrieved=", retrieved)

except Exception as e:
    print("ERROR:", e)
finally:
    import shutil
    shutil.rmtree(temp_dir)
    print("Done.")
