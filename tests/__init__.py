# make django-tables available for import for tests
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
