import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.

buildOptions = dict(packages = ['json', 'flask'], excludes = [], include_files = ['webapp'])

base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('main.py', base=base, targetName = 'epycor')
]

setup(name='Epycor',
      version = '1.0',
      description = 'Cross-platform Epicor time entry',
      options = dict(build_exe = buildOptions),
      executables = executables)
