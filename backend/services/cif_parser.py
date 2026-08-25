from pymatgen.core import Structure
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer


class CIFParser:
    def __init__(self, cif_path: str):
        self.structure = Structure.from_file(cif_path)
        self.sga = SpacegroupAnalyzer(self.structure)
    
    def get_basic_info(self) -> dict:
        return {
            "formula": self.structure.formula,
            "space_group": self.sga.get_space_group_symbol(),
            "space_group_number": self.sga.get_space_group_number(),
            "point_group": self.sga.get_point_group_symbol(),
            "crystal_system": self.sga.get_crystal_system(),
            "lattice": {
                "a": self.structure.lattice.a,
                "b": self.structure.lattice.b,
                "c": self.structure.lattice.c,
                "alpha": self.structure.lattice.alpha,
                "beta": self.structure.lattice.beta,
                "gamma": self.structure.lattice.gamma,
                "volume": self.structure.lattice.volume,
            },
            "num_sites": len(self.structure),
            "density": self.structure.density,
        }
    
    def get_symmetry_operations(self, max_ops: int = 10) -> list:
        """获取空间群的部分对称操作（用于分析）"""
        try:
            ops = self.sga.get_symmetry_operations()
            return [str(op) for op in ops[:max_ops]]
        except Exception:
            return []
    
    def infer_oxidation_states(self) -> dict:
        """基于电中性和常见氧化态推断各元素氧化态"""
        from collections import Counter
        
        elements = [str(site.specie) for site in self.structure]
        counts = Counter(elements)
        
        # 常见元素氧化态表（简化版）
        common_states = {
            'O': -2, 'S': -2, 'Se': -2, 'Te': -2,
            'F': -1, 'Cl': -1, 'Br': -1, 'I': -1,
            'H': 1,
            'Li': 1, 'Na': 1, 'K': 1, 'Rb': 1, 'Cs': 1,
            'Mg': 2, 'Ca': 2, 'Sr': 2, 'Ba': 2,
            'Al': 3,
            'Si': 4,
            'Ti': 4, 'Zr': 4, 'Hf': 4,
            'Fe': [2, 3], 'Co': [2, 3], 'Ni': 2, 'Cu': [1, 2],
            'Zn': 2, 'Cd': 2,
            'Mn': [2, 4], 'Cr': 3,
            'La': 3, 'Ce': [3, 4],
        }
        
        # 计算已知阴离子的总负电荷
        known_negative = 0
        unknown_elements = {}
        for elem, count in counts.items():
            if elem in common_states:
                if elem in ['O', 'S', 'Se', 'Te', 'F', 'Cl', 'Br', 'I']:
                    known_negative += common_states[elem] * count
                else:
                    unknown_elements[elem] = count
            else:
                unknown_elements[elem] = count
        
        # 简单推断：假设化合物电中性，正电荷总和 = -负电荷总和
        result = {}
        total_positive = -known_negative
        
        if len(unknown_elements) == 1:
            elem, count = list(unknown_elements.items())[0]
            inferred = total_positive / count
            result[elem] = round(inferred, 1) if inferred == int(inferred) else f"~{inferred:.1f}"
        else:
            for elem, count in unknown_elements.items():
                if elem in common_states:
                    states = common_states[elem]
                    if isinstance(states, list):
                        result[elem] = states
                    else:
                        result[elem] = states
                else:
                    result[elem] = "?"
        
        return result
    
    def get_coordination(self, max_sites: int = 10) -> list:
        """配位环境分析，包含键角"""
        cnn = CrystalNN()
        results = []
        for i, site in enumerate(self.structure[:max_sites]):
            try:
                nn = cnn.get_nn_info(self.structure, i)
                # 按距离排序，取最近 6 个邻居
                neighbors = sorted(
                    [{"element": str(n["site"].specie), "distance": round(site.distance(n["site"]), 3), "index": n["site_index"]}
                     for n in nn],
                    key=lambda x: x["distance"]
                )[:6]
                
                # 计算键角（取前 3 个邻居之间的夹角）
                angles = []
                if len(neighbors) >= 3:
                    for a in range(min(3, len(neighbors))):
                        for b in range(a + 1, min(3, len(neighbors))):
                            try:
                                angle = self.structure.get_angle(
                                    neighbors[a]["index"], i, neighbors[b]["index"]
                                )
                                angles.append({
                                    "pair": f"{neighbors[a]['element']}-{site.specie}-{neighbors[b]['element']}",
                                    "angle": round(angle, 1)
                                })
                            except Exception:
                                pass
                
                results.append({
                    "site": f"{site.specie}{i}",
                    "coords": [round(x, 4) for x in site.frac_coords],
                    "coordination_num": len(nn),
                    "neighbors": neighbors[:4],  # 只显示最近 4 个
                    "angles": angles[:6],  # 只显示前 6 个键角
                })
            except Exception:
                continue
        return results
    
    def get_bond_lengths(self, max_pairs: int = 20) -> list:
        bonds = []
        seen = set()
        for i in range(min(len(self.structure), 20)):
            for j in range(i + 1, min(len(self.structure), 20)):
                d = self.structure.get_distance(i, j)
                if d < 3.0:
                    pair = tuple(sorted([str(self.structure[i].specie), str(self.structure[j].specie)]))
                    key = (pair, round(d, 2))
                    if key not in seen:
                        seen.add(key)
                        bonds.append({"pair": f"{pair[0]}-{pair[1]}", "distance": round(d, 3)})
        return sorted(bonds, key=lambda x: x["distance"])[:max_pairs]
    
    def export_for_llm(self, max_length: int = 4000) -> str:
        """导出为 LLM 友好的详细文本格式"""
        info = self.get_basic_info()
        coord = self.get_coordination()
        bonds = self.get_bond_lengths()
        ox_states = self.infer_oxidation_states()
        sym_ops = self.get_symmetry_operations()
        
        text = f"""Crystal Structure Data:

## Basic Information
Formula: {info['formula']}
Space Group: {info['space_group']} (No. {info['space_group_number']})
Point Group: {info['point_group']}
Crystal System: {info['crystal_system']}
Lattice: a={info['lattice']['a']:.4f}Å, b={info['lattice']['b']:.4f}Å, c={info['lattice']['c']:.4f}Å
Angles: α={info['lattice']['alpha']:.2f}°, β={info['lattice']['beta']:.2f}°, γ={info['lattice']['gamma']:.2f}°
Volume: {info['lattice']['volume']:.2f}Å³
Sites: {info['num_sites']}, Density: {info['density']:.3f} g/cm³

## Oxidation State Inference
"""
        for elem, state in ox_states.items():
            text += f"  {elem}: {state}\n"
        
        text += f"\n## Coordination Environment (first {len(coord)} sites)\n"
        for c in coord:
            text += f"\n  {c['site']} at ({', '.join(map(str, c['coords']))})\n"
            text += f"  Coordination Number: {c['coordination_num']}\n"
            text += f"  Neighbors: " + ", ".join([f"{n['element']}@{n['distance']}Å" for n in c['neighbors']]) + "\n"
            if c['angles']:
                text += f"  Key Angles: " + ", ".join([f"{a['pair']}={a['angle']}°" for a in c['angles']]) + "\n"
        
        text += f"\n## Selected Bond Lengths (<3.0Å, top {len(bonds)}):\n"
        for b in bonds:
            text += f"  {b['pair']}: {b['distance']}Å\n"
        
        if sym_ops:
            text += f"\n## Representative Symmetry Operations (first {len(sym_ops)}):\n"
            for op in sym_ops:
                text += f"  {op}\n"
        
        if len(text) > max_length:
            text = text[:max_length] + "\n... (truncated)"
        
        return text
