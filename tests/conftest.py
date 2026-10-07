import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
sys.path.insert(0,str(R/'src/common/benchmarks'))
