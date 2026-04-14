from setuptools import setup, Extension

ext_module = Extension(
    'curseforge_fingerprint._core',
    sources=[
        'curseforge_fingerprint/_core.c',
        'curseforge_fingerprint/fingerprint.c',
    ],
    include_dirs=['curseforge_fingerprint/'],
)

setup(
    name='curseforge-fingerprint',
    version='1.0.0',
    description='Python binding for the CurseForge fingerprinting algorithm',
    license='GPL-3.0',
    ext_modules=[ext_module],
    packages=['curseforge_fingerprint'],
    python_requires='>=3.7',
)
