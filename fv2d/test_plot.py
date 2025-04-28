from datahandler import AthenaTabular, Fv2DH5
from pathlib import Path
import matplotlib.pyplot as plt

athena_data_path = Path("athena_output")
athena_data_file = list(sorted(athena_data_path.glob("*.tab")))[-1]
athena_data = AthenaTabular(athena_data_file)
athena_data.rescale()
fv2d_data_path = Path("fv2d_output")
fv2d_data_file = fv2d_data_path / "run_brio_wu.h5"
fv2d_data = Fv2DH5(fv2d_data_file, reshape=True)
fv2d_data_file_5w = fv2d_data_path / "run_brio_wu_5w.h5"
fv2d_data_5w = Fv2DH5(fv2d_data_file_5w, reshape=True)

fv2d_data_file_5w_nodc = fv2d_data_path / "run_brio_wu_5w_noDC.h5"
fv2d_data_5w_nodc = Fv2DH5(fv2d_data_file_5w_nodc, reshape=True)
# fv2d_data.reshape(Nx=512)

plt.figure(figsize=(10, 10))
plt.plot(athena_data.x, athena_data.rho, label="Athena-hlld")
plt.plot(fv2d_data.x, fv2d_data.rho, label="FV2D-hlld")
plt.plot(fv2d_data_5w.x, fv2d_data_5w.rho, label="FV2D-5waves")
plt.plot(fv2d_data_5w_nodc.x, fv2d_data_5w_nodc.rho, label="FV2D-5waves-noDC")
plt.xlabel("x")
plt.ylabel(r"Density $\rho$")
plt.legend()
plt.grid()
plt.show()
