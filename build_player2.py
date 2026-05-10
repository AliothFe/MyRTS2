import sys
sys.path.insert(0, '.')
from src.main import main
sys.argv = ['main.py', '--player', '2']
main()