from pymatgen.core import Structure
from pymatgen.core.lattice import Lattice
import os

os.chdir(r'D:/src/Ziang-Nan/晶体学-ZiangNan/cif-chat/tests')

# 1. NaCl 岩盐结构（简单立方，6配位）
nacl = Structure.from_spacegroup(
    225, 
    Lattice.cubic(5.64), 
    [11, 17], 
    [[0, 0, 0], [0.5, 0.5, 0.5]]
)
nacl.to(filename='NaCl.cif')
print(f'NaCl.cif 已创建，{len(nacl)} 个原子位点')

# 2. Si 金刚石结构（四面体配位）
si = Structure(
    Lattice.cubic(5.43),
    [14, 14],
    [[0, 0, 0], [0.25, 0.25, 0.25]]
)
si.to(filename='Si.cif')
print(f'Si.cif 已创建，{len(si)} 个原子位点')

# 3. CaTiO3 钙钛矿（过渡金属 + 氧八面体，更有趣）
perov = Structure.from_spacegroup(
    221,
    Lattice.cubic(3.84),
    [20, 22, 8],
    [[0.5, 0.5, 0.5], [0, 0, 0], [0.5, 0.5, 0]]
)
perov.to(filename='CaTiO3.cif')
print(f'CaTiO3.cif 已创建，{len(perov)} 个原子位点')

print('\n三个测试文件已生成到 tests/ 目录')
