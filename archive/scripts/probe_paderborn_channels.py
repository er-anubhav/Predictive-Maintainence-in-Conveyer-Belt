import os, scipy.io as sio

drive_dir = "/content/drive/MyDrive/SIH26008_ML"
fpath = f"{drive_dir}/raw/paderborn/K001/N15_M07_F10_K001_20.mat"
data = sio.loadmat(fpath)
top_key = [k for k in data.keys() if not k.startswith("__")][0]
struct = data[top_key]
y_arr = struct['Y'][0, 0] # shape (1, 7)
print("Y shape:", y_arr.shape)

for i in range(y_arr.shape[1]):
    item = y_arr[0, i]
    name = item['Name'][0] if hasattr(item['Name'], '__len__') else item['Name']
    data_field = item['Data']
    print(f"Channel {i}: Name={name}, Data shape={getattr(data_field, 'shape', None)}, size={getattr(data_field, 'size', None)}")
