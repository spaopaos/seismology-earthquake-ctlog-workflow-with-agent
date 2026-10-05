# SKHASH

Python package for earthquake focal mechanism inversions.

Author: Robert Skoumal, U.S. Geological Survey | rskoumal@usgs.gov

This project contains Python code to compute focal mechanism solutions using first-motion polarities (traditional, consensus, and/or imputed) and S/P ratios (traditional and/or consensus).

## How to Use
#### 1. Install the latest release in your virtual environment:
<pre>
# If you <i><b>don't</b></i> want to create beachball plots:
pip install -U SKHASH

# If you <i><b>do</b></i> want to create beachball plots:
pip install -U 'SKHASH[plot]'
</pre>
Python 3.8+ versions are supported.

#### 2. Run SKHASH with your desired control file:
```
SKHASH path_to/control_file.txt
```

## More information
### Running examples
A variety of examples are provided in the repository. It's recommended you play around with these examples to learn about some of the features.
1. Download the examples folder available [HERE](https://code.usgs.gov/esc/SKHASH/-/archive/main/SKHASH-main.zip?path=examples).
2. Unzip the folder.
3. Navigate to the examples folder you just downloaded, e.g.:
`
cd examples
`
4. Run SKHASH with the example of your choice, e.g.:
`SKHASH hash1/control_file.txt`

### Manual
Refer to the [manual](https://code.usgs.gov/esc/SKHASH/-/blob/main/SKHASH_manual.pdf) or the [wiki](https://code.usgs.gov/esc/SKHASH/-/wikis/home) for additional information about running the code.

## Fortran subroutine (completely optional)
By default, SKHASH will compute mechanisms using the Python routine. However, to speed up the grid search, you can choose to take advantage of an included Fortran subroutine. If the Python C/API wrapper does not already exist, SKHASH will automatically create the wrapper with the user's permission when the Fortran subroutine is used.

To use this Fortran routine, add the following lines to your control file:
```
$use_fortran
True
```

A fortran compiler will be needed on the user's machine. If one does not exist, here are some examples on how to get one:
```
# macOS Homebrew example
brew install gcc

# Ubuntu example
apt install gfortran
```

If you're using Python 3.12+, the [meson](https://pypi.org/project/meson-python) and [ninja](https://pypi.org/project/ninja) packages are also needed.
```
pip3 install meson ninja
```

Note that if you are using macOS and receive an error, you may be missing the Command Line Tools package. To install:
```
xcode-select --install
```

## Citation
Please cite our paper if you use anything in this project:

- Skoumal, R.J., Hardebeck, J.L., Shearer, P.M. (2024). SKHASH: A Python package for computing earthquake focal mechanisms. _Seismological Research Letters_, 95(4), 2519-2526. https://doi.org/10.1785/0220230329

Significant portions of this algorithm are based on [HASH](https://www.usgs.gov/node/279393):

- Hardebeck, J.L., & Shearer, P.M. (2002). A new method for determining first-motion focal mechanisms. _Bulletin of the Seismological Society of America_, 92(6), 2264-2276. https://doi.org/10.1785/0120010200

- Hardebeck, J.L., & Shearer, P.M. (2003). Using S/P amplitude ratios to constrain the focal mechanisms of small earthquakes. _Bulletin of the Seismological Society of America_, 93(6), 2434-2444. https://doi.org/10.1785/0120020236

## License and Disclaimer
[License](https://code.usgs.gov/esc/SKHASH/-/blob/main/LICENSE.md): This project is in the public domain.

[Disclaimer](https://code.usgs.gov/esc/SKHASH/-/blob/main/DISCLAIMER.md): This software is preliminary or provisional and is subject to revision.
