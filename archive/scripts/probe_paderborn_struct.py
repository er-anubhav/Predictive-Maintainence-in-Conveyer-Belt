import os, scipy.io as sio

drive_dir = "/content/drive/MyDrive/SIH26008_ML"
fpath = f"{drive_dir}/raw/paderborn/K001/N15_M07_F10_K001_20.mat"
data = sio.loadmat(fpath)
top_key = [k for k in data.keys() if not k.startswith("__")][0]
print("Top key:", top_key)
struct = data[top_key]
print("Struct dtype names:", struct.dtype.names)
for name in struct.dtype.names:
    val = struct[name][0, 0]
    print(f"  Field {name}: type={type(val)}, shape={getattr(val, 'shape', None)}, dtype={getattr(val, 'dtype', None)}")
    if name == 'Y':
        print("    Y entries:", val.dtype.names if hasattr(val, 'dtype') else 'no names')
        for i in range(val.shape[1]):
            item = val[0, i]
            print(f"      Channel {i}: names={item.dtype.names}")
            for fn in item.dtype.names:
                f_val = item[fn]
                print(f"        {fn}: shape={f_val.shape}, val={f_val[0,0] if f_val.size < 5 else 'large array'}")
