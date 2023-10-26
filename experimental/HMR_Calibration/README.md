# HMR Grid Calibration
This CL contains the Python source code for the grid calibration algorithm that reports the systematic errors arise from the Human Motion Robot (HMR) itself including:
- Rotational error
- Skewing error
- 2D Scaling factors relative to the physical dimensions of the Device Under Test (DUT)
- 2D Offset values relative to the physical dimensions of the DUT

These values can then be used to correct the test cases performed on the HMR before evaluation.

## Installation Guide
This algorithm is implemented using Python 3.10.10 ([download link](https://www.python.org/downloads/release/python-31010/)) and requires several libraries in Python to perform curve fitting and graph plotting. These libraries are described in `requirements.txt`. To install these libraries, please run the command:
~~~
pip install -r requirements.txt
~~~

## Running the algorithm
There are a few variables we need to provide for the algorithm to run in `main.py`:
- `dutDimensions`: The screen dimensions of the DUT
- `margins`: The external and internal margins
- `threshold`: The filtering and midline threshold

After providing the above variables and constants, simply run the evaluation algorithm by:
~~~
python -u "<directory-of-HMR_insitu_calibration.py>/HMR_insitu_calibration.py"
~~~
